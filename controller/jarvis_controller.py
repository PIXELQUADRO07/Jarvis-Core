"""
controller/jarvis_controller.py — Controller JARVIS PRO
Unico punto di ingresso dalla UI. Gestisce sicurezza, rate limiting, notifiche, i18n.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Generator, Any

from config import get_config
from core.commands import run_command
from core.state import set_status
from core.llm import stream_llm
from core.tools.router import route_query
from core.voice import speak_text
from core.security import sanitize_input, get_rate_limiter
from core.notifications import get_notifier
from core.i18n import t
from logger import debug


@dataclass
class UIEvent:
    kind:    str
    payload: Any = None


def handle_input(raw: str) -> Generator[UIEvent, None, None]:
    raw = raw.strip()
    if not raw:
        return

    config = get_config()

    # ── Sicurezza: sanifica input ────────────────────────────────────────
    if config.sanitize_input:
        raw = sanitize_input(raw)
        if not raw:
            yield UIEvent("system_msg", "⚠️ Input non valido o rimosso per sicurezza.")
            return

    # ── Comandi slash ────────────────────────────────────────────────────
    if raw.startswith("/"):
        result = run_command(raw)
        action = result.get("action")
        data   = result.get("data", "")

        match action:
            case "exit":    yield UIEvent("exit")
            case "clear":   yield UIEvent("clear")
            case "reset":   yield UIEvent("reset")
            case "help":    yield UIEvent("help")
            case "status":  yield UIEvent("status", data)
            case "message":
                yield UIEvent("system_msg", str(data))
                sys_event = result.get("system_event")
                if sys_event in ("voice_enabled", "voice_disabled"):
                    yield UIEvent("banner_update")
            case "unknown":
                yield UIEvent("system_msg", t("unknown_command", cmd=data))
            case _:
                yield UIEvent("system_msg", f"Azione: {action}")
        return

    # ── Rate limiting ────────────────────────────────────────────────────
    limiter = get_rate_limiter()
    if not limiter.allow():
        wait = limiter.wait_time()
        yield UIEvent("system_msg", f"⏳ {t('rate_limit')} (attendi {wait:.0f}s)")
        return

    # ── Flusso AI ────────────────────────────────────────────────────────
    yield UIEvent("user_msg", raw)
    set_status("thinking")

    try:
        # Tool routing (meteo, wiki, plugin, web search...)
        result = route_query(raw)
        if result:
            yield UIEvent("system_msg", result)
            if config.enable_voice:
                speak_text(result)
            get_notifier().jarvis_reply(result)
            return

        # LLM streaming
        full_response = ""
        for chunk, meta in stream_llm(raw):
            set_status("streaming")
            full_response += chunk
            yield UIEvent("ai_chunk", (chunk, meta))

        yield UIEvent("ai_done", full_response)
        get_notifier().jarvis_reply(full_response)

    except ConnectionError as e:
        msg = t("error_ollama")
        yield UIEvent("ai_error", str(e))
        get_notifier().error_alert(str(e))
    except TimeoutError:
        yield UIEvent("ai_error", "Timeout — Ollama non risponde. Riprova.")
    except Exception as e:
        yield UIEvent("ai_error", str(e))
        get_notifier().error_alert(str(e))
    finally:
        set_status("idle")
