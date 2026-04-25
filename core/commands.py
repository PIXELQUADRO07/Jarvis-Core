from core.memory import load_memory, save_memory


# ─────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────

def get_help() -> dict:
    return {
        "/help": "Mostra questo elenco comandi",
        "/reset": "Azzera la memoria conversazionale",
        "/status": "Mostra stato memoria e sistema",
        "/exit": "Chiude JARVIS"
    }


# ─────────────────────────────────────────────
# CORE COMMAND HANDLER
# ─────────────────────────────────────────────

def run_command(raw: str) -> dict:
    cmd = raw.strip().lower()

    # HELP
    if cmd in ("/help", "/h"):
        return {
            "action": "message",
            "data": "\n".join(f"{k} → {v}" for k, v in get_help().items())
        }

    # RESET
    if cmd == "/reset":
        save_memory([])
        return {
            "action": "message",
            "data": "Memoria azzerata."
        }

    # STATUS
    if cmd == "/status":
        mem = load_memory()
        return {
            "action": "message",
            "data": f"Messaggi in memoria: {len(mem)}"
        }

    # EXIT
    if cmd == "/exit":
        return {
            "action": "exit",
            "data": "Chiusura sistema."
        }

    # UNKNOWN
    return {
        "action": "unknown",
        "data": raw
    }
