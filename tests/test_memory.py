"""
tests/test_memory.py — Regression tests for the memory.py bugs fixed:
  1. Only the last assistant message was persisted to the DB (user
     turns were silently never saved).
  2. clear_memory() didn't clear the DB, only the JSON file, so old
     messages resurfaced on the next load (DB is checked first).
  3. _filter_hallucinations blacklisted ANY message containing
     "GPT"/"BERT"/"qwen"/"ollama", wiping out legitimate messages.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    from config import JarvisConfig, set_config
    cfg = JarvisConfig()
    cfg.db_file = str(tmp_path / "jarvis.db")
    set_config(cfg)

    import core.session_manager as sm
    sm._session_manager = None
    smgr = sm.get_session_manager()
    smgr.sessions_dir = tmp_path / "memory_sessions"
    smgr.sessions_dir.mkdir(exist_ok=True)
    smgr.create_session("default")

    import core.db as dbmod
    dbmod._db = None  # fresh DB singleton pointed at the tmp path

    yield cfg
    set_config(JarvisConfig())


def test_both_user_and_assistant_saved_to_db(isolated_env):
    from core.memory import load_memory, save_memory
    save_memory([{"role": "user", "content": "ciao"},
                 {"role": "assistant", "content": "ciao a te"}])
    loaded = load_memory()
    roles = [m["role"] for m in loaded]
    assert roles == ["user", "assistant"]


def test_clear_memory_clears_db(isolated_env):
    from core.memory import load_memory, save_memory, clear_memory
    save_memory([{"role": "user", "content": "ciao"},
                 {"role": "assistant", "content": "ciao a te"}])
    assert load_memory()  # non-empty before clear
    clear_memory()
    assert load_memory() == []


def test_hallucination_filter_keeps_legitimate_mentions():
    from core.memory import _filter_hallucinations
    legit = [
        {"role": "user", "content": "che differenza c'è tra GPT e BERT?"},
        {"role": "assistant", "content": "Uso qwen2.5 tramite Ollama in locale."},
    ]
    assert _filter_hallucinations(legit) == legit


def test_hallucination_filter_drops_actual_self_id():
    from core.memory import _filter_hallucinations
    bad = [{"role": "assistant", "content": "I'm a GPT model trained by OpenAI."}]
    assert _filter_hallucinations(bad) == []
