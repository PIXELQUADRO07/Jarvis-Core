from core.memory import load_memory, save_memory


# ─────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────

def get_help() -> dict:
    return {
        "/help": "Mostra questo elenco comandi",
        "/tools": "Mostra gli strumenti disponibili",
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

    # TOOLS
    if cmd == "/tools":
        tools = [
            "Meteo: Chiedi 'meteo a [città]' per previsioni del tempo.",
            "Wikipedia: Chiedi 'chi è [argomento]' per informazioni da Wikipedia.",
            "Calcoli: Inserisci espressioni matematiche come '2 + 3 * 4'.",
            "Scraper: Inserisci un URL per ottenere il titolo della pagina.",
            "Sistema: Comandi di sistema come 'aggiorna sistema'."
        ]
        return {
            "action": "message",
            "data": "Strumenti disponibili:\n" + "\n".join(f"- {t}" for t in tools)
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
