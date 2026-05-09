"""
core/commands.py — Dispatcher comandi slash JARVIS PRO.
Tutti i comandi: voce, sessioni, modelli, lingua, plugin, sicurezza, esporta, ...
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
        "/help, /h":           "Mostra questo elenco comandi",
        "/tools":              "Mostra gli strumenti disponibili",
        "/plugins":            "Elenca plugin caricati",
        "/memory, /m":         "Statistiche memoria conversazione",
        "/model list":         "Elenca modelli disponibili",
        "/model set [name]":   "Imposta modello attivo",
        "/model current":      "Mostra modello attuale",
        "/session create [n]": "Crea nuova sessione",
        "/session switch [n]": "Cambia sessione",
        "/session list":       "Elenca sessioni",
        "/session current":    "Sessione attuale",
        "/session delete [n]": "Elimina sessione",
        "/search [testo]":     "Cerca nello storico conversazioni",
        "/export":             "Esporta conversazione in Markdown",
        "/clear":              "Azzera la memoria conversazionale",
        "/cleanup":            "Rimuovi messaggi vecchi dal DB",
        "/status, /s":         "Stato sistema e connessione",
        "/config":             "Configurazione attuale",
        "/history":            "Ultimi messaggi della sessione",
        "/lang [it|en|es|fr|de]": "Cambia lingua runtime",
        "/silent on|off":      "Modalità risposta silenziosa/breve",
        "/voice on|off|status|test": "Controllo sintesi vocale",
        "/api on|off":         "Avvia/ferma il server API REST",
        "/encrypt on|off":     "Abilita/disabilita crittografia memoria",
        "/exit, /quit":        "Chiude JARVIS",
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
            f"📊 Memoria — sessione: {get_session_manager().current_session.name}\n"
            f"  Messaggi totali:  {stats['total_messages']}\n"
            f"  Messaggi utente:  {stats['user_messages']}\n"
            f"  Risposte JARVIS:  {stats['assistant_messages']}\n"
            f"  Caratteri totali: {stats['total_characters']}\n"
            f"  Media per msg:    {stats['avg_message_length']} chars\n"
            f"  DB (tutte sessioni): {db_stats.get('messages', 0)} msg / {db_stats.get('total_tokens', 0)} token"
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
            f"⚙️  Configurazione JARVIS PRO\n"
            f"  URL Ollama:       {config.ollama_url}\n"
            f"  Modello:          {config.model}\n"
            f"  Temperatura:      {config.temperature}\n"
            f"  Lingua:           {get_language()}\n"
            f"  Modalità silenziosa: {'ON' if config.silent_mode else 'OFF'}\n"
            f"  Voce:             {'ON' if config.enable_voice else 'OFF'} "
            f"(disponibile: {ve.is_available()})\n"
            f"  Crittografia:     {'ON' if config.encrypt_memory else 'OFF'}\n"
            f"  Rate limit:       {config.rate_limit_requests} req/{config.rate_limit_window}s\n"
            f"  Web search:       {'ON' if config.enable_web_search else 'OFF'}\n"
            f"  Plugin:           {'ON' if config.enable_plugins else 'OFF'}\n"
            f"  API server:       {'ON' if config.enable_api else 'OFF'} "
            f"(porta {config.api_port})\n"
            f"  Markdown render:  {'ON' if config.render_markdown else 'OFF'}\n"
            f"  Token counter:    {'ON' if config.show_token_count else 'OFF'}"
        )
        return {"action": "message", "data": text}

    # ── HISTORY ───────────────────────────────────────────────────────────
    if cmd_low == "/history":
        history = load_memory()
        if not history:
            return {"action": "message", "data": "📜 Cronologia vuota"}
        recent = history[-10:]
        lines = ["📜 Ultimi messaggi:"]
        for i, msg in enumerate(recent, 1):
            role    = "👤 Tu" if msg["role"] == "user" else "🤖 JARVIS"
            content = msg["content"][:80] + ("…" if len(msg["content"]) > 80 else "")
            lines.append(f"  {i}. {role}: {content}")
        return {"action": "message", "data": "\n".join(lines)}

    # ── SEARCH ────────────────────────────────────────────────────────────
    if cmd_low.startswith("/search"):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            return {"action": "message", "data": "Uso: /search [testo]"}
        query = parts[1].strip()
        try:
            from core.db import get_db
            results = get_db().search(query, limit=5)
            if not results:
                return {"action": "message", "data": f"🔍 Nessun risultato per: {query}"}
            lines = [f"🔍 Ricerca: **{query}** — {len(results)} risultati\n"]
            for r in results:
                role    = "👤" if r["role"] == "user" else "🤖"
                content = r["content"][:100] + ("…" if len(r["content"]) > 100 else "")
                lines.append(f"  [{r['session']}] {role} {content}")
            return {"action": "message", "data": "\n".join(lines)}
        except Exception as e:
            return {"action": "message", "data": f"Errore ricerca: {e}"}

    # ── TOOLS ─────────────────────────────────────────────────────────────
    if cmd_low == "/tools":
        tools = [
            f"🌤️  Meteo:       {'✓' if config.enable_weather else '✗'} — chiedi 'meteo a [città]'",
            f"📚 Wikipedia:   {'✓' if config.enable_wiki else '✗'} — 'chi è [argomento]'",
            f"🧮 Calcoli:     {'✓' if config.enable_math else '✗'} — espressioni matematiche",
            f"🔗 Scraper:     {'✓' if config.enable_scraper else '✗'} — incolla un URL",
            f"🖥️  Sistema:     {'✓' if config.enable_system else '✗'} — info sistema operativo",
            f"🌐 Web search:  {'✓' if config.enable_web_search else '✗'} — 'cerca [query]'",
        ]
        return {"action": "message", "data": "🛠️  Strumenti:\n" + "\n".join(tools)}

    # ── PLUGINS ───────────────────────────────────────────────────────────
    if cmd_low == "/plugins":
        try:
            from core.plugin_manager import get_plugin_manager
            plugins = get_plugin_manager().list_plugins()
            if not plugins:
                return {"action": "message", "data": "🔌 Nessun plugin caricato.\nCrea file in plugins/*.py"}
            lines = [f"🔌 {t('plugin_list')} ({len(plugins)}):"]
            for p in plugins:
                status = "✓" if p["enabled"] else "✗"
                lines.append(f"  {status} {p['name']} v{p['version']} — {p['description']}")
            return {"action": "message", "data": "\n".join(lines)}
        except Exception as e:
            return {"action": "message", "data": f"Errore plugin: {e}"}

    # ── LANG ──────────────────────────────────────────────────────────────
    if cmd_low.startswith("/lang"):
        parts = cmd_low.split()
        if len(parts) < 2:
            return {"action": "message", "data": "Uso: /lang [it|en|es|fr|de]"}
        lang = parts[1].strip()
        if set_language(lang):
            config.language = lang
            config.save()
            return {"action": "message", "data": t("lang_changed", lang=lang)}
        return {"action": "message", "data": f"Lingua non supportata: {lang}. Disponibili: it, en, es, fr, de"}

    # ── SILENT ────────────────────────────────────────────────────────────
    if cmd_low.startswith("/silent"):
        parts = cmd_low.split()
        if len(parts) < 2:
            state = "ON" if config.silent_mode else "OFF"
            return {"action": "message", "data": f"Modalità silenziosa: {state}. Usa /silent on|off"}
        if parts[1] == "on":
            config.silent_mode = True
            config.save()
            return {"action": "message", "data": t("silent_on")}
        elif parts[1] == "off":
            config.silent_mode = False
            config.save()
            return {"action": "message", "data": t("silent_off")}
        return {"action": "message", "data": "Uso: /silent on|off"}

    # ── ENCRYPT ───────────────────────────────────────────────────────────
    if cmd_low.startswith("/encrypt"):
        parts = cmd_low.split()
        if len(parts) < 2:
            state = "ON" if config.encrypt_memory else "OFF"
            return {"action": "message", "data": f"Crittografia memoria: {state}. Usa /encrypt on|off"}
        if parts[1] == "on":
            try:
                from core.security import encrypt_text
                if encrypt_text("test") is None:
                    return {"action": "message", "data": "✗ Libreria 'cryptography' non installata.\npip install cryptography"}
            except Exception:
                return {"action": "message", "data": "✗ Installa: pip install cryptography"}
            config.encrypt_memory = True
            config.save()
            return {"action": "message", "data": "✓ Crittografia AES abilitata per memoria."}
        elif parts[1] == "off":
            config.encrypt_memory = False
            config.save()
            return {"action": "message", "data": "✓ Crittografia disabilitata."}

    # ── CLEANUP ───────────────────────────────────────────────────────────
    if cmd_low == "/cleanup":
        try:
            from core.memory import auto_cleanup_old_messages
            from core.db import get_db
            db = get_db()
            deleted = db.cleanup_old_messages(config.memory_cleanup_days)
            return {"action": "message", "data": f"🗑️  Rimossi {deleted} messaggi più vecchi di {config.memory_cleanup_days} giorni."}
        except Exception as e:
            return {"action": "message", "data": f"✗ Cleanup fallito: {e}"}

    # ── VOICE ─────────────────────────────────────────────────────────────
    if cmd_low.startswith("/voice"):
        from core.voice_engine import get_voice_engine
        parts = cmd_low.split()
        if len(parts) < 2:
            return {"action": "message", "data": "Uso: /voice on|off|status|test"}
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
            on   = "🟢 ABILITATA" if config.enable_voice else "🔴 DISABILITATA"
            avail = "🟢 DISPONIBILE" if ve.is_available() else "🔴 NON DISPONIBILE"
            return {"action": "message", "data":
                f"🔊 Voce: {on} | {avail}\n  Modello: {config.voice_model}\n  Volume: {config.voice_volume}"}
        elif sub == "test":
            if ve.is_available():
                ve.speak("Ciao! Questo è un test della sintesi vocale di JARVIS.")
                return {"action": "message", "data": "✓ Test voce inviato"}
            return {"action": "message", "data": "✗ Voce non disponibile. Verifica Piper e modello .onnx"}

    # ── MODEL ─────────────────────────────────────────────────────────────
    if cmd_low.startswith("/model"):
        parts = cmd.split()
        if len(parts) < 2:
            return {"action": "message", "data": "Uso: /model list|set [name]|current"}
        sub = parts[1].lower()
        if sub == "list":
            models = _get_available_models()
            if not models:
                return {"action": "message", "data": "❌ Nessun modello. Verifica Ollama online."}
            current = config.model
            ml = "\n".join(f"  {'✓' if m == current else ' '} {m}" for m in models)
            return {"action": "message", "data": f"📦 Modelli disponibili:\n{ml}"}
        elif sub == "current":
            return {"action": "message", "data": f"📊 Modello attuale: **{config.model}**"}
        elif sub == "set":
            if len(parts) < 3:
                return {"action": "message", "data": "Uso: /model set [nome]"}
            name = parts[2]
            available = _get_available_models()
            if name not in available:
                return {"action": "message", "data": f"❌ Modello '{name}' non trovato. Usa /model list"}
            config.model = name
            config.save()
            return {"action": "message", "data": f"✓ Modello → **{name}**"}

    # ── SESSION ───────────────────────────────────────────────────────────
    if cmd_low.startswith("/session"):
        sm    = get_session_manager()
        parts = cmd.split()
        if len(parts) < 2:
            cur = sm.current_session.name if sm.current_session else "?"
            return {"action": "message", "data": f"Sessione attiva: {cur}. Uso: /session create|switch|list|delete|current"}
        sub = parts[1].lower()
        if sub == "list":
            sessions = sm.list_sessions()
            current  = sm.current_session.name if sm.current_session else None
            if not sessions:
                return {"action": "message", "data": "📋 Nessuna sessione trovata."}
            lines = ["📋 Sessioni:"] + [
                f"  {'▶' if s == current else ' '} {s}" for s in sessions
            ]
            return {"action": "message", "data": "\n".join(lines)}
        elif sub == "current":
            cur = sm.current_session.name if sm.current_session else "?"
            return {"action": "message", "data": f"Sessione attiva: **{cur}**"}
        elif sub == "create":
            if len(parts) < 3:
                return {"action": "message", "data": "Uso: /session create [nome]"}
            name = parts[2]
            sm.create_session(name)
            return {"action": "message", "data": t("session_created", name=name)}
        elif sub == "switch":
            if len(parts) < 3:
                return {"action": "message", "data": "Uso: /session switch [nome]"}
            name = parts[2]
            result = sm.switch_session(name)
            if result:
                return {"action": "message", "data": t("session_switched", name=name)}
            return {"action": "message", "data": f"✗ Sessione '{name}' non trovata."}
        elif sub == "delete":
            if len(parts) < 3:
                return {"action": "message", "data": "Uso: /session delete [nome]"}
            name = parts[2]
            if sm.delete_session(name):
                return {"action": "message", "data": f"✓ Sessione '{name}' eliminata."}
            return {"action": "message", "data": f"✗ Sessione '{name}' non trovata."}

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
                md = f"# Conversazione JARVIS — {session_name}\n\n**Data:** {now.strftime('%d/%m/%Y %H:%M')}\n\n---\n\n"
                for msg in history:
                    label = "👤 **Tu**" if msg["role"] == "user" else "🤖 **JARVIS**"
                    md += f"### {label}\n\n{msg['content']}\n\n"

        if not md:
            return {"action": "message", "data": "✗ Cronologia vuota, nulla da esportare."}

        Path("exports").mkdir(exist_ok=True)
        filename = f"exports/conversation_{session_name}_{dt.now().strftime('%Y%m%d_%H%M%S')}.md"
        Path(filename).write_text(md, encoding="utf-8")
        return {"action": "message", "data": t("export_ok", file=filename)}

    # ── API ───────────────────────────────────────────────────────────────
    if cmd_low.startswith("/api"):
        parts = cmd_low.split()
        if len(parts) < 2:
            state = "ON" if config.enable_api else "OFF"
            return {"action": "message", "data": f"API server: {state} (porta {config.api_port}). Usa /api on|off"}
        if parts[1] == "on":
            config.enable_api = True
            config.save()
            try:
                from api.rest_api import run_api_server
                run_api_server()
                return {"action": "message", "data": f"✓ API server avviato su http://{config.api_host}:{config.api_port}"}
            except ImportError:
                return {"action": "message", "data": "✗ Installa FastAPI: pip install fastapi uvicorn"}
        elif parts[1] == "off":
            config.enable_api = False
            config.save()
            return {"action": "message", "data": "✓ API server disabilitato (riavvia JARVIS per fermare il thread)"}

    # ── EXIT ─────────────────────────────────────────────────────────────
    if cmd_low in ("/exit", "/quit"):
        return {"action": "exit"}

    # ── UNKNOWN ──────────────────────────────────────────────────────────
    return {"action": "unknown", "data": raw}
