"""
controller/jarvis_controller.py — Controller JARVIS
Fa da ponte tra UI e core. La UI non tocca mai il core direttamente.

Flusso:
  UI input
    ↓
  handle_input()   ← unico punto di ingresso
    ↓
  route comandi → core/commands
  route AI      → core/llm (streaming)
    ↓
  yield UIEvent   ← la UI consuma solo eventi tipizzati
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Any

from core.commands import run_command
from core.state    import set_status
from core.llm      import stream_llm
from core.tools.router import route_query


# ─── UIEvent — contratto controller → UI ─────────────────────────────────────

@dataclass
class UIEvent:
    kind   : str    # "clear"|"reset"|"help"|"status"|"system_msg"
                    # "user_msg"|"ai_chunk"|"ai_done"|"ai_error"|"exit"
    payload: Any = None


# ─── handle_input — unico entry point pubblico ───────────────────────────────

def handle_input(raw: str) -> Generator[UIEvent, None, None]:
    """
    Riceve il testo grezzo dall'utente e produce una sequenza di UIEvent.
    La UI fa un for-loop su questo generator e renderizza ogni evento.

    Comandi  → 1 evento azione
    Chat AI  → user_msg + N ai_chunk + ai_done (o ai_error)
    """
    raw = raw.strip()
    if not raw:
        return

    # ── Comandi slash ─────────────────────────────────────────────────────────
    if raw.startswith("/"):
        result = run_command(raw)
        action = result.get("action")
        data   = result.get("data", "")

        match action:
            case "exit":
                yield UIEvent("exit")
            case "clear":
                yield UIEvent("clear")
            case "reset":
                yield UIEvent("reset")
            case "help":
                yield UIEvent("help")
            case "status":
                yield UIEvent("status", data)
            case "message":
                yield UIEvent("system_msg", data)
            case "unknown":
                yield UIEvent("system_msg", f"Comando sconosciuto: {data}  — digita /help")
            case _:
                yield UIEvent("system_msg", f"Azione non gestita: {action}")
        return

    # ── Flusso AI / tools ─────────────────────────────────────────────────────
    yield UIEvent("user_msg", raw)

    set_status("thinking")
    try:
        result = route_query(raw)
        if result:
            yield UIEvent("system_msg", result)
            return

        for chunk in stream_llm(raw):
            set_status("streaming")
            yield UIEvent("ai_chunk", chunk)
        yield UIEvent("ai_done")
    except Exception as e:
        yield UIEvent("ai_error", str(e))
    finally:
        set_status("idle")
