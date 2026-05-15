"""
core/commands.py — Slash command dispatcher for JARVIS PRO.
All commands: voice, sessions, models, language, plugins, security, export, ...
"""
import json
import urllib.request
from datetime import datetime as dt
from pathlib import Path
from typing import Optional

from config import get_config
from core.memory import load_memory, save_memory, clear_memory, get_memory_stats
from core.token_counter import TokenCounter
from core.session_manager import get_session_manager
from core.i18n import t, set_language, get_language
from logger import debug, error


def get_help() -> dict:
    return {
        "/help, /h":           "Show this command list",
        "/tools":              "Show available tools",
        "/plugins":            "List loaded plugins",
        "/memory, /m":         "Conversation memory stats",
        "/model list":         "List available models",
        "/model set [name]":   "Set active model",
        "/model current":      "Show current model",
        "/session create [n]": "Create a new session",
        "/session switch [n]": "Switch session",
        "/session list":       "List sessions",
        "/session current":    "Current session",
        "/session delete [n]": "Delete session",
        "/search [text]":      "Search conversation history",
        "/export":             "Export conversation to Markdown",
        "/clear":              "Reset conversation memory",
        "/cleanup":            "Remove old messages from DB",
        "/status, /s":         "System and connection status",
        "/config":             "Current configuration",
        "/history":            "Last session messages",
        "/lang [it|en|es|fr|de]": "Change runtime language",
        "/silent on|off":      "Silent/short response mode",
        "/voice on|off|status|test": "Voice synthesis control",
        "/api on|off":         "Start/stop REST API server",
        "/encrypt on|off":     "Enable/disable memory encryption",
        "/exit, /quit":        "Quit JARVIS",
    }


def _get_available_models() -> list:
    config = get_config()
    try:
        url = config.ollama_url.replace("/api/chat", "/api/tags")
        with urllib.request.urlopen(
            urllib.request.Request(url, method="GET"), timeout=5
        ) as r:
            data = json.loads(r.read().decode())
            return [m.get("name", "?") for m in data.get("models", [])]
    except Exception as e:
        debug(f"Failed to get models: {e}")
        return []


def _check_ollama() -> dict:
    config = get_config()
    try:
        url = config.ollama_url.replace("/api/chat", "/api/tags")
        with urllib.request.urlopen(
            urllib.request.Request(url, method="GET"), timeout=5
        ) as r:
            data = json.loads(r.read().decode())
            return {
                "ollama": True,
                "model": config.model,
                "models_available": [m.get("name", "?") for m in data.get("models", [])],
            }
    except Exception as e:
        return {"ollama": False, "model": config.model, "models_available": [], "error": str(e)}


def run_command(raw: str) -> dict:
    """Dispatcher centrale comandi. Ritorna dict {action, data, ...}."""
    cmd     = raw.strip()
    cmd_low = cmd.lower()
    config  = get_config()

    # ── HELP ──────────────────────────────────────────────────────────────
    if cmd_low in ("/help", "/h"):
        return {"action": "help"}

    # ── MEMORY ────────────────────────────────────────────────────────────
    if cmd_low in ("/memory", "/m"):
        stats = get_memory_stats()
        try:
            from core.db import get_db
            db_stats = get_db().get_stats()
        except Exception:
            db_stats = {}
        text = (
            f"📊 Memory — session: {get_session_manager().current_session.name}\n"
            f"  Total messages:    {stats['total_messages']}\n"
            f"  User messages:     {stats['user_messages']}\n"
            f"  JARVIS replies:    {stats['assistant_messages']}\n"
            f"  Total characters:  {stats['total_characters']}\n"
            f"  Avg per msg:       {stats['avg_message_length']} chars\n"
            f"  DB (all sessions): {db_stats.get('messages', 0)} msg / {db_stats.get('total_tokens', 0)} tokens"
        )
        return {"action": "message", "data": text}

    # ── CLEAR ─────────────────────────────────────────────────────────────
    if cmd_low == "/clear":
        clear_memory()
        return {"action": "reset"}

    # ── STATUS ────────────────────────────────────────────────────────────
    if cmd_low in ("/status", "/s"):
        info = _check_ollama()
        return {"action": "status", "data": info}

    # ── CONFIG ────────────────────────────────────────────────────────────
    if cmd_low == "/config":
        from core.voice_engine import get_voice_engine
        ve = get_voice_engine()
        text = (
            f"⚙️  JARVIS PRO configuration\n"
            f"  Ollama URL:       {config.ollama_url}\n"
            f"  Model:            {config.model}\n"
            f"  Temperature:      {config.temperature}\n"
            f"  Language:         {get_language()}\n"
            f"  Silent mode:      {'ON' if config.silent_mode else 'OFF'}\n"
            f"  Voice:            {'ON' if config.enable_voice else 'OFF'} "
            f"(available: {ve.is_available()})\n"
            f"  Encryption:       {'ON' if config.encrypt_memory else 'OFF'}\n"
            f"  Rate limit:       {config.rate_limit_requests} req/{config.rate_limit_window}s\n"
            f"  Web search:       {'ON' if config.enable_web_search else 'OFF'}\n"
            f"  Plugins:          {'ON' if config.enable_plugins else 'OFF'}\n"
            f"  API server:       {'ON' if config.enable_api else 'OFF'} "
            f"(port {config.api_port})\n"
            f"  Markdown render:  {'ON' if config.render_markdown else 'OFF'}\n"
            f"  Token counter:    {'ON' if config.show_token_count else 'OFF'}"
        )
        return {"action": "message", "data": text}

    # ── HISTORY ───────────────────────────────────────────────────────────
    if cmd_low == "/history":
        history = load_memory()
        if not history:
            return {"action": "message", "data": "📜 Empty history"}
        recent = history[-10:]
        lines = ["📜 Latest messages:"]
        for i, msg in enumerate(recent, 1):
            role    = "👤 You" if msg["role"] == "user" else "🤖 JARVIS"
            content = msg["content"][:80] + ("…" if len(msg["content"]) > 80 else "")
            lines.append(f"  {i}. {role}: {content}")
        return {"action": "message", "data": "\n".join(lines)}

    # ── SEARCH ────────────────────────────────────────────────────────────
    if cmd_low.startswith("/search"):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            return {"action": "message", "data": "Usage: /search [text]"}
        query = parts[1].strip()
        try:
            from core.db import get_db
            results = get_db().search(query, limit=5)
            if not results:
                return {"action": "message", "data": f"🔍 No results for: {query}"}
            lines = [f"🔍 Search: **{query}** — {len(results)} results\n"]
            for r in results:
                role    = "👤" if r["role"] == "user" else "🤖"
                content = r["content"][:100] + ("…" if len(r["content"]) > 100 else "")
                lines.append(f"  [{r['session']}] {role} {content}")
            return {"action": "message", "data": "\n".join(lines)}
        except Exception as e:
            return {"action": "message", "data": f"Search error: {e}"}

    # ── TOOLS ─────────────────────────────────────────────────────────────
    if cmd_low == "/tools":
        tools = [
            f"🌤️  Weather:       {'✓' if config.enable_weather else '✗'} — ask 'weather in [city]'",
            f"📚 Wikipedia:     {'✓' if config.enable_wiki else '✗'} — 'who is [topic]'",
            f"🧮 Math:          {'✓' if config.enable_math else '✗'} — calculations and expressions",
            f"🔗 Scraper:       {'✓' if config.enable_scraper else '✗'} — paste a URL",
            f"🖥️  System:        {'✓' if config.enable_system else '✗'} — OS information",
            f"🌐 Web search:    {'✓' if config.enable_web_search else '✗'} — 'search [query]'",
        ]
        return {"action": "message", "data": "🛠️  Tools:\n" + "\n".join(tools)}

    # ── PLUGINS ───────────────────────────────────────────────────────────
    if cmd_low == "/plugins":
        try:
            from core.plugin_manager import get_plugin_manager
            plugins = get_plugin_manager().list_plugins()
            if not plugins:
                return {"action": "message", "data": "🔌 No plugins loaded.\nCreate a file in plugins/*.py"}
            lines = [f"🔌 {t('plugin_list')} ({len(plugins)}):"]
            for p in plugins:
                status = "✓" if p["enabled"] else "✗"
                lines.append(f"  {status} {p['name']} v{p['version']} — {p['description']}")
            return {"action": "message", "data": "\n".join(lines)}
        except Exception as e:
            return {"action": "message", "data": f"Plugin error: {e}"}

    # ── LANG ──────────────────────────────────────────────────────────────
    if cmd_low.startswith("/lang"):
        parts = cmd_low.split()
        if len(parts) < 2:
            return {"action": "message", "data": "Usage: /lang [it|en|es|fr|de]"}
        lang = parts[1].strip()
        if set_language(lang):
            config.language = lang
            config.save()
            return {"action": "message", "data": t("lang_changed", lang=lang)}
        return {"action": "message", "data": f"Unsupported language: {lang}. Available: it, en, es, fr, de"}

    # ── SILENT ────────────────────────────────────────────────────────────
    if cmd_low.startswith("/silent"):
        parts = cmd_low.split()
        if len(parts) < 2:
            state = "ON" if config.silent_mode else "OFF"
            return {"action": "message", "data": f"Silent mode: {state}. Use /silent on|off"}
        if parts[1] == "on":
            config.silent_mode = True
            config.save()
            return {"action": "message", "data": t("silent_on")}
        elif parts[1] == "off":
            config.silent_mode = False
            config.save()
            return {"action": "message", "data": t("silent_off")}
        return {"action": "message", "data": "Usage: /silent on|off"}

    # ── ENCRYPT ───────────────────────────────────────────────────────────
    if cmd_low.startswith("/encrypt"):
        parts = cmd_low.split()
        if len(parts) < 2:
            state = "ON" if config.encrypt_memory else "OFF"
            return {"action": "message", "data": f"Memory encryption: {state}. Use /encrypt on|off"}
        if parts[1] == "on":
            try:
                from core.security import encrypt_text
                if encrypt_text("test") is None:
                    return {"action": "message", "data": "✗ 'cryptography' library is not installed.\npip install cryptography"}
            except Exception:
                return {"action": "message", "data": "✗ Install: pip install cryptography"}
            config.encrypt_memory = True
            config.save()
            return {"action": "message", "data": "✓ AES encryption enabled for memory."}
        elif parts[1] == "off":
            config.encrypt_memory = False
            config.save()
            return {"action": "message", "data": "✓ Encryption disabled."}

    # ── CLEANUP ───────────────────────────────────────────────────────────
    if cmd_low == "/cleanup":
        try:
            from core.memory import auto_cleanup_old_messages
            from core.db import get_db
            db = get_db()
            deleted = db.cleanup_old_messages(config.memory_cleanup_days)
            return {"action": "message", "data": f"🗑️  Deleted {deleted} messages older than {config.memory_cleanup_days} days."}
        except Exception as e:
            return {"action": "message", "data": f"✗ Cleanup failed: {e}"}

    # ── VOICE ─────────────────────────────────────────────────────────────
    if cmd_low.startswith("/voice"):
        from core.voice_engine import get_voice_engine
        parts = cmd_low.split()
        if len(parts) < 2:
            return {"action": "message", "data": "Usage: /voice on|off|status|test"}
        sub = parts[1]
        ve  = get_voice_engine()
        if sub == "on":
            config.enable_voice = True
            config.save()
            return {"action": "message", "data": t("voice_on"), "system_event": "voice_enabled"}
        elif sub == "off":
            config.enable_voice = False
            config.save()
            return {"action": "message", "data": t("voice_off"), "system_event": "voice_disabled"}
        elif sub == "status":
            on   = "🟢 ENABLED" if config.enable_voice else "🔴 DISABLED"
            avail = "🟢 AVAILABLE" if ve.is_available() else "🔴 NOT AVAILABLE"
            return {"action": "message", "data":
                f"🔊 Voice: {on} | {avail}\n  Model: {config.voice_model}\n  Volume: {config.voice_volume}"}
        elif sub == "test":
            if ve.is_available():
                ve.speak("Hello! This is a JARVIS voice synthesis test.")
                return {"action": "message", "data": "✓ Voice test sent"}
            return {"action": "message", "data": "✗ Voice not available. Check Piper and .onnx model"}

    # ── MODEL ─────────────────────────────────────────────────────────────
    if cmd_low.startswith("/model"):
        parts = cmd.split()
        if len(parts) < 2:
            return {"action": "message", "data": "Usage: /model list|set [name]|current"}
        sub = parts[1].lower()
        if sub == "list":
            models = _get_available_models()
            if not models:
                return {"action": "message", "data": "❌ No models found. Check Ollama online."}
            current = config.model
            ml = "\n".join(f"  {'✓' if m == current else ' '} {m}" for m in models)
            return {"action": "message", "data": f"📦 Available models:\n{ml}"}
        elif sub == "current":
            return {"action": "message", "data": f"📊 Current model: **{config.model}**"}
        elif sub == "set":
            if len(parts) < 3:
                return {"action": "message", "data": "Usage: /model set [name]"}
            name = parts[2]
            available = _get_available_models()
            if name not in available:
                return {"action": "message", "data": f"❌ Model '{name}' not found. Use /model list"}
            config.model = name
            config.save()
            return {"action": "message", "data": f"✓ Model → **{name}**"}

    # ── SESSION ───────────────────────────────────────────────────────────
    if cmd_low.startswith("/session"):
        sm    = get_session_manager()
        parts = cmd.split()
        if len(parts) < 2:
            cur = sm.current_session.name if sm.current_session else "?"
            return {"action": "message", "data": f"Active session: {cur}. Use /session create|switch|list|delete|current"}
        sub = parts[1].lower()
        if sub == "list":
            sessions = sm.list_sessions()
            current  = sm.current_session.name if sm.current_session else None
            if not sessions:
                return {"action": "message", "data": "📋 No sessions found."}
            lines = ["📋 Sessions:"] + [
                f"  {'▶' if s == current else ' '} {s}" for s in sessions
            ]
            return {"action": "message", "data": "\n".join(lines)}
        elif sub == "current":
            cur = sm.current_session.name if sm.current_session else "?"
            return {"action": "message", "data": f"Active session: **{cur}**"}
        elif sub == "create":
            if len(parts) < 3:
                return {"action": "message", "data": "Usage: /session create [name]"}
            name = parts[2]
            sm.create_session(name)
            return {"action": "message", "data": t("session_created", name=name)}
        elif sub == "switch":
            if len(parts) < 3:
                return {"action": "message", "data": "Usage: /session switch [name]"}
            name = parts[2]
            result = sm.switch_session(name)
            if result:
                return {"action": "message", "data": t("session_switched", name=name)}
            return {"action": "message", "data": f"✗ Session '{name}' not found."}
        elif sub == "delete":
            if len(parts) < 3:
                return {"action": "message", "data": "Usage: /session delete [name]"}
            name = parts[2]
            if sm.delete_session(name):
                return {"action": "message", "data": f"✓ Session '{name}' deleted."}
            return {"action": "message", "data": f"✗ Session '{name}' not found."}

    # ── EXPORT ────────────────────────────────────────────────────────────
    if cmd_low == "/export":
        sm = get_session_manager()
        session_name = sm.current_session.name if sm.current_session else "default"
        try:
            from core.db import get_db
            md = get_db().export_session_markdown(session_name)
        except Exception:
            history = load_memory()
            md = ""
            if history:
                now = dt.now()
                md = f"# JARVIS Conversation — {session_name}\n\n**Date:** {now.strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
                for msg in history:
                    label = "👤 **You**" if msg["role"] == "user" else "🤖 **JARVIS**"
                    md += f"### {label}\n\n{msg['content']}\n\n"

        if not md:
            return {"action": "message", "data": "✗ Empty history, nothing to export."}

        Path("exports").mkdir(exist_ok=True)
        filename = f"exports/conversation_{session_name}_{dt.now().strftime('%Y%m%d_%H%M%S')}.md"
        Path(filename).write_text(md, encoding="utf-8")
        return {"action": "message", "data": t("export_ok", file=filename)}

    # ── API ───────────────────────────────────────────────────────────────
    if cmd_low.startswith("/api"):
        parts = cmd_low.split()
        if len(parts) < 2:
            state = "ON" if config.enable_api else "OFF"
            return {"action": "message", "data": f"API server: {state} (port {config.api_port}). Use /api on|off"}
        if parts[1] == "on":
            config.enable_api = True
            config.save()
            try:
                from api.rest_api import run_api_server
                run_api_server()
                return {"action": "message", "data": f"✓ API server started at http://{config.api_host}:{config.api_port}"}
            except ImportError:
                return {"action": "message", "data": "✗ Install FastAPI: pip install fastapi uvicorn"}
        elif parts[1] == "off":
            config.enable_api = False
            config.save()
            return {"action": "message", "data": "✓ API server disabled (restart JARVIS to stop the thread)"}

    # ── EXIT ─────────────────────────────────────────────────────────────
    if cmd_low in ("/exit", "/quit"):
        return {"action": "exit"}

    # ── UNKNOWN ──────────────────────────────────────────────────────────
    return {"action": "unknown", "data": raw}
