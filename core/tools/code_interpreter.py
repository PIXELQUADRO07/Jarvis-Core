"""
core/tools/code_interpreter.py — Python code execution with process-level isolation.

IMPORTANT — read before enabling/trusting this tool:
This is NOT a real sandbox. It runs code in a separate OS process with
resource limits (CPU time, memory, no new processes) and a stripped
environment, which stops accidental resource exhaustion and blocks a lot
of casual misuse. It does NOT stop a determined attacker: the process
still runs as your user, with your filesystem and network access. The
old string-blacklist approach (checking for "os.system", "eval(", etc.
as literal substrings) is kept only as a cheap first filter — it is
trivially bypassed (e.g. string concatenation, __import__ via getattr,
splitting a keyword across lines) and must not be treated as a security
boundary.

For real isolation, run this tool inside a container (Docker with
--network=none and a memory/cpu cgroup, or Firejail/bubblewrap) rather
than relying on this module alone. If you have Docker available, prefer
routing execution through it instead of the raw subprocess path below.
"""
import os
import subprocess
import sys
from typing import Optional

from logger import warning

# Defense-in-depth only — see module docstring. Do not rely on this alone.
_BLOCKED_PATTERNS = [
    "os.system", "os.popen", "subprocess.", "shutil.rmtree",
    "os.remove", "os.unlink", "os.rmdir", "__import__",
    "eval(", "exec(", "compile(", "open(", "ctypes", "pty.spawn",
]


def _resource_limits(max_memory_mb: int):
    """Return a preexec_fn that caps CPU time, memory, and process count
    for the child process. POSIX only (no-op on Windows)."""
    if os.name != "posix":
        return None

    def _apply():
        import resource
        mem_bytes = max_memory_mb * 1024 * 1024
        # Address space cap — kills runaway allocations.
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        # No forking/spawning further processes from inside the snippet.
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
        except (ValueError, OSError):
            pass  # some platforms don't allow lowering this
        # Don't let it write huge files to disk.
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))

    return _apply


def execute_python(code: str, timeout: Optional[int] = None) -> str:
    """Execute Python code in a resource-limited subprocess."""
    if not code:
        return "No code provided."

    from config import get_config
    cfg = get_config()
    timeout = timeout or cfg.code_exec_timeout

    for pattern in _BLOCKED_PATTERNS:
        if pattern in code:
            warning(f"code_interpreter: blocked pattern '{pattern}' in submitted code")
            return f"Error: blocked pattern detected: {pattern}"

    # Minimal environment: don't leak the parent's env vars (API keys, etc.)
    # into arbitrary code.
    clean_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"}

    try:
        result = subprocess.run(
            [sys.executable, "-I", "-c", code],  # -I: isolated mode, ignores env/site
            capture_output=True,
            text=True,
            timeout=timeout,
            env=clean_env,
            preexec_fn=_resource_limits(cfg.code_exec_max_memory_mb),
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: execution timed out after {timeout} seconds."
    except MemoryError:
        return "Error: memory limit exceeded."
    except Exception as e:
        return f"Error: {str(e)}"


def handle_code_query(query: str) -> Optional[str]:
    """Route code execution queries."""
    q = query.lower().strip()
    if q.startswith("python:"):
        code = query[7:].strip()
        return execute_python(code)

    if q.startswith("esegui python"):
        code = query[13:].strip()
        return execute_python(code)

    return None
