"""
tests/test_core.py — Test unitari JARVIS PRO
Esegui: pytest tests/ -v
"""
import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Config ────────────────────────────────────────────────────────────────────

def test_config_defaults():
    from config import JarvisConfig
    cfg = JarvisConfig()
    assert cfg.temperature == 0.2
    assert cfg.max_history_messages == 100
    assert cfg.language == "it"
    assert cfg.rate_limit_requests == 60


def test_config_validation_temperature():
    from config import JarvisConfig
    cfg = JarvisConfig()
    cfg.temperature = 1.5
    cfg._validate()
    assert cfg.temperature == 1.5


def test_config_validation_language_fallback():
    from config import JarvisConfig
    cfg = JarvisConfig()
    cfg.language = "zz"
    cfg._validate()
    assert cfg.language == "it"


# ── Security ─────────────────────────────────────────────────────────────────

def test_sanitize_input_clean():
    from core.security import sanitize_input
    assert sanitize_input("ciao come stai?") == "ciao come stai?"


def test_sanitize_input_removes_script():
    from core.security import sanitize_input
    result = sanitize_input("<script>alert('xss')</script>testo")
    assert "<script>" not in result
    assert "testo" in result


def test_sanitize_input_truncates_long():
    from core.security import sanitize_input
    long_text = "a" * 5000
    result = sanitize_input(long_text)
    assert len(result) <= 4096


def test_validate_url():
    from core.security import validate_url
    assert validate_url("https://example.com") is True
    assert validate_url("http://example.com") is True
    assert validate_url("file:///etc/passwd") is False
    assert validate_url("ftp://server.com") is False


def test_rate_limiter_allows():
    from core.security import RateLimiter
    rl = RateLimiter(max_requests=5, window_seconds=60)
    for _ in range(5):
        assert rl.allow() is True


def test_rate_limiter_blocks():
    from core.security import RateLimiter
    rl = RateLimiter(max_requests=2, window_seconds=60)
    rl.allow()
    rl.allow()
    assert rl.allow() is False


# ── i18n ─────────────────────────────────────────────────────────────────────

def test_i18n_italian():
    from core.i18n import t, set_language
    set_language("it")
    assert "JARVIS" in t("greeting")


def test_i18n_english():
    from core.i18n import t, set_language
    set_language("en")
    result = t("greeting")
    assert "JARVIS" in result
    assert "online" in result.lower() or "Online" in result


def test_i18n_unknown_key_returns_key():
    from core.i18n import t, set_language
    set_language("it")
    assert t("nonexistent_key_xyz") == "nonexistent_key_xyz"


def test_i18n_format():
    from core.i18n import t, set_language
    set_language("it")
    result = t("lang_changed", lang="en")
    assert "en" in result


def test_i18n_invalid_lang():
    from core.i18n import set_language
    assert set_language("xx") is False
    assert set_language("it") is True


# ── VoiceQueue ────────────────────────────────────────────────────────────────

def test_voice_queue_push_pop():
    from core.voice_queue import VoiceQueue
    q = VoiceQueue()
    q.push("ciao", priority=1)
    assert q.pop() == "ciao"
    assert q.pop() is None


def test_voice_queue_priority_order():
    from core.voice_queue import VoiceQueue
    q = VoiceQueue()
    q.push("bassa", priority=5)
    q.push("alta",  priority=1)
    assert q.pop() == "alta"


def test_voice_queue_empty():
    from core.voice_queue import VoiceQueue
    q = VoiceQueue()
    assert q.empty() is True
    q.push("test")
    assert q.empty() is False
    q.pop()
    assert q.empty() is True


def test_voice_queue_clear():
    from core.voice_queue import VoiceQueue
    q = VoiceQueue()
    q.push("a")
    q.push("b")
    q.clear()
    assert q.empty() is True


def test_pop_complete_sentence_basic():
    from core.voice_queue import pop_complete_sentence
    sentence, remaining = pop_complete_sentence("Ciao come stai. Bene grazie")
    assert sentence == "Ciao come stai."
    assert "Bene" in remaining


def test_pop_complete_sentence_no_terminator():
    from core.voice_queue import pop_complete_sentence
    sentence, remaining = pop_complete_sentence("frase incompleta")
    assert sentence == ""
    assert remaining == "frase incompleta"


def test_pop_complete_sentence_empty():
    from core.voice_queue import pop_complete_sentence
    s, r = pop_complete_sentence("")
    assert s == "" and r == ""


# ── Token Counter ─────────────────────────────────────────────────────────────

def test_token_counter_basic():
    from core.token_counter import TokenCounter
    tokens = TokenCounter.estimate_tokens("Ciao come stai?", "mistral")
    assert tokens > 0


def test_token_counter_empty():
    from core.token_counter import TokenCounter
    assert TokenCounter.estimate_tokens("", "mistral") == 0


def test_token_counter_format():
    from core.token_counter import TokenCounter
    result = TokenCounter.format_usage(100, 200)
    assert "100" in result and "200" in result and "300" in result


# ── Plugin Manager ────────────────────────────────────────────────────────────

def test_plugin_manager_empty_dir(tmp_path):
    from core.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=str(tmp_path))
    n = pm.load_all()
    assert n == 0
    assert pm.list_plugins() == []


def test_plugin_manager_load_plugin(tmp_path):
    # Crea un plugin valido
    plugin_code = '''
from core.plugin_manager import PluginBase
class TestPlugin(PluginBase):
    name = "test_plugin"
    description = "Plugin di test"
    def can_handle(self, query):
        return "test" in query.lower()
    def handle(self, query):
        return "risposta test"
'''
    (tmp_path / "test_plugin.py").write_text(plugin_code)
    from core.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=str(tmp_path))
    n = pm.load_all()
    assert n == 1
    result = pm.route("questo è un test")
    assert result == "risposta test"


def test_plugin_manager_disable(tmp_path):
    plugin_code = '''
from core.plugin_manager import PluginBase
class DisPlugin(PluginBase):
    name = "dis_plugin"
    description = "Test disable"
    def can_handle(self, query): return True
    def handle(self, query): return "result"
'''
    (tmp_path / "dis_plugin.py").write_text(plugin_code)
    from core.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=str(tmp_path))
    pm.load_all()
    pm.disable("dis_plugin")
    assert pm.route("qualcosa") is None


# ── DB ────────────────────────────────────────────────────────────────────────

def test_db_save_and_load(tmp_path):
    from core.db import ConversationDB
    db = ConversationDB(str(tmp_path / "test.db"))
    db.save_message("sess1", "user",      "Ciao JARVIS")
    db.save_message("sess1", "assistant", "Ciao utente!")
    msgs = db.load_session("sess1")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_db_search(tmp_path):
    from core.db import ConversationDB
    db = ConversationDB(str(tmp_path / "test.db"))
    db.save_message("sess1", "user", "Mi parli del meteo a Roma")
    results = db.search("meteo")
    assert len(results) >= 1
    assert "meteo" in results[0]["content"].lower()


def test_db_export_markdown(tmp_path):
    from core.db import ConversationDB
    db = ConversationDB(str(tmp_path / "test.db"))
    db.save_message("s1", "user",      "Domanda")
    db.save_message("s1", "assistant", "Risposta")
    md = db.export_session_markdown("s1")
    assert "Domanda" in md
    assert "Risposta" in md
    assert "# Conversazione" in md


def test_db_cleanup(tmp_path):
    from core.db import ConversationDB
    from datetime import datetime, timedelta
    import sqlite3
    db = ConversationDB(str(tmp_path / "test.db"))
    db.save_message("s1", "user", "vecchio")
    # Modifica manualmente la data per renderlo vecchio
    old_date = (datetime.now() - timedelta(days=40)).isoformat()
    with sqlite3.connect(str(tmp_path / "test.db")) as c:
        c.execute("UPDATE messages SET created_at = ?", (old_date,))
    deleted = db.cleanup_old_messages(days=30)
    assert deleted >= 1


def test_db_stats(tmp_path):
    from core.db import ConversationDB
    db = ConversationDB(str(tmp_path / "test.db"))
    db.save_message("s1", "user",      "a", prompt_tokens=10, reply_tokens=5)
    db.save_message("s1", "assistant", "b", prompt_tokens=10, reply_tokens=20)
    stats = db.get_stats()
    assert stats["messages"] == 2
    assert stats["total_tokens"] == 45


# ── Notifications ─────────────────────────────────────────────────────────────

def test_notification_manager_disabled():
    from core.notifications import NotificationManager
    nm = NotificationManager(enabled=False)
    # Non deve crashare
    result = nm.notify("Titolo", "Corpo", "info")
    assert result is False


def test_notification_manager_level_filter():
    from core.notifications import NotificationManager
    nm = NotificationManager(level="error", enabled=False)
    assert nm.notify("T", "B", "info") is False
