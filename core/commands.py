import urllib.request
import urllib.error
import json
from datetime import datetime

from core.memory import load_memory, save_memory, clear_memory, get_memory_stats
from core.token_counter import TokenCounter
from core.session_manager import get_session_manager
from config import get_config
from logger import debug, error
from core.voice import get_voice_engine, is_voice_available


def get_help() -> dict:
    """Ritorna help per tutti i comandi disponibili"""
    return {
        "/help, /h": "Mostra questo elenco comandi",
        "/tools": "Mostra gli strumenti disponibili",
        "/memory, /m": "Mostra statistiche memoria conversazione",
        "/model list": "Elenca modelli disponibili",
        "/model set [name]": "Imposta modello attivo",
        "/model current": "Mostra modello attuale",
        "/session create [name]": "Crea nuova sessione",
        "/session switch [name]": "Cambia sessione",
        "/session list": "Elenca sessioni",
        "/session current": "Sessione attuale",
        "/session delete [name]": "Elimina sessione",
        "/export": "Esporta conversazione a file markdown",
        "/clear": "Azzera la memoria conversazionale",
        "/status, /s": "Mostra stato del sistema e connessione",
        "/config": "Mostra configurazione attuale",
        "/history": "Mostra ultimi 5 messaggi",
        "/voice on": "Abilita sintesi vocale",
        "/voice off": "Disabilita sintesi vocale",
        "/voice status": "Stato sintesi vocale",
        "/voice test": "Test sintesi vocale",
        "/exit, /quit": "Chiude JARVIS"
    }


def get_available_models() -> list:
    """Ottiene lista di modelli disponibili da Ollama"""
    config = get_config()
    try:
        url = config.ollama_url.replace("/api/chat", "/api/tags")
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "?") for m in data.get("models", [])]
            return models
    except Exception as e:
        debug(f"Failed to get models from Ollama: {e}")
        return []


def _check_ollama() -> dict:
    """Controlla lo stato di Ollama e modelli disponibili"""
    config = get_config()
    try:
        url = config.ollama_url.replace("/api/chat", "/api/tags")
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "?") for m in data.get("models", [])]
            return {
                "ollama": True,
                "model": config.model,
                "models_available": models
            }
    except Exception as e:
        debug(f"Ollama check failed: {e}")
        return {
            "ollama": False,
            "model": config.model,
            "models_available": [],
            "error": str(e)
        }


def run_command(raw: str) -> dict:
    """
    Dispatcher centrale per i comandi slash.
    Ritorna dict con "action" e "data" per il controller.
    """
    cmd = raw.strip().lower()

    # HELP
    if cmd in ("/help", "/h"):
        help_text = "\n".join(f"{k:20} → {v}" for k, v in get_help().items())
        return {
            "action": "message",
            "data": help_text
        }

    # MEMORY / STATS
    if cmd in ("/memory", "/m"):
        stats = get_memory_stats()
        text = (
            f"📊 Statistiche Memoria:\n"
            f"  Messaggi totali: {stats['total_messages']}\n"
            f"  Messaggi utente: {stats['user_messages']}\n"
            f"  Risposte JARVIS: {stats['assistant_messages']}\n"
            f"  Caratteri totali: {stats['total_characters']}\n"
            f"  Lunghezza media: {stats['avg_message_length']} char/msg"
        )
        return {
            "action": "message",
            "data": text
        }

    # CLEAR
    if cmd == "/clear":
        clear_memory()
        return {
            "action": "message",
            "data": "✓ Memoria conversazione azzerata."
        }

    # STATUS
    if cmd in ("/status", "/s"):
        ollama_info = _check_ollama()
        stats = get_memory_stats()
        
        ollama_status = "🟢 ONLINE" if ollama_info["ollama"] else "🔴 OFFLINE"
        text = (
            f"📡 Sistema JARVIS\n"
            f"  Ollama: {ollama_status}\n"
            f"  Modello: {ollama_info['model']}\n"
            f"  Messaggi in memoria: {stats['total_messages']}\n"
            f"  Modelli disponibili: {', '.join(ollama_info['models_available']) or 'nessuno'}"
        )
        return {
            "action": "status",
            "data": ollama_info
        }

    # CONFIG
    if cmd == "/config":
        config = get_config()
        voice_engine = get_voice_engine()
        
        voice_status = "ABILITATA" if config.enable_voice else "DISABILITATA"
        voice_available = "SÌ" if voice_engine.is_available() else "NO"
        
        text = (
            f"⚙️  Configurazione Attuale:\n"
            f"  Ollama URL: {config.ollama_url}\n"
            f"  Modello: {config.model}\n"
            f"  Temperatura: {config.temperature}\n"
            f"  Max risposta: {config.max_response_length} char\n"
            f"  Max storia: {config.max_history_messages} msg\n"
            f"  Timeout: {config.request_timeout}s\n"
            f"  Voce abilitata: {voice_status} (Disponibile: {voice_available})\n"
            f"  Modello voce: {config.voice_model}\n"
            f"  Volume voce: {config.voice_volume}\n"
            f"  File config: jarvis_config.json"
        )
        return {
            "action": "message",
            "data": text
        }

    # HISTORY
    if cmd == "/history":
        history = load_memory()
        if not history:
            return {
                "action": "message",
                "data": "📜 Cronologia vuota"
            }
        
        # Mostra ultimi 5 messaggi
        recent = history[-10:]
        text = "📜 Ultimi messaggi:\n"
        for i, msg in enumerate(recent, 1):
            role = "👤 Tu" if msg["role"] == "user" else "🤖 JARVIS"
            content = msg["content"][:60] + ("..." if len(msg["content"]) > 60 else "")
            text += f"  {i}. {role}: {content}\n"
        
        return {
            "action": "message",
            "data": text
        }

    # TOOLS
    if cmd == "/tools":
        tools = [
            "🌤️  Meteo: Chiedi 'meteo a [città]' per previsioni del tempo.",
            "📚 Wikipedia: Chiedi 'chi è [argomento]' per informazioni.",
            "🧮 Calcoli: Inserisci 'quanto è 2 + 3 * 4' o espressioni matematiche.",
            "🔗 Scraper: Inserisci un URL per ottenere il titolo della pagina.",
            "🖥️  Sistema: Comandi come 'aggiorna sistema' o 'controlla risorse'."
        ]
        text = "🛠️  Strumenti disponibili:\n" + "\n".join(tools)
        return {
            "action": "message",
            "data": text
        }

    # VOICE COMMANDS
    if cmd.startswith("/voice"):
        parts = cmd.split()
        if len(parts) < 2:
            return {
                "action": "message",
                "data": "Uso: /voice on|off|status|test"
            }
        
        subcmd = parts[1].lower()
        config = get_config()
        voice_engine = get_voice_engine()
        
        if subcmd == "on":
            config.enable_voice = True
            config.save()
            return {
                "action": "message",
                "data": f"✓ Sintesi vocale abilitata. Disponibile: {voice_engine.is_available()}",
                "system_event": "voice_enabled"
            }
        
        elif subcmd == "off":
            config.enable_voice = False
            config.save()
            return {
                "action": "message",
                "data": "✓ Sintesi vocale disabilitata",
                "system_event": "voice_disabled"
            }
        
        elif subcmd == "status":
            voice_status = "🟢 ABILITATA" if config.enable_voice else "🔴 DISABILITATA"
            available = voice_engine.is_available()
            avail_status = "🟢 DISPONIBILE" if available else "🔴 NON DISPONIBILE"
            
            text = (
                f"🔊 Stato Sintesi Vocale:\n"
                f"  Abilitata: {voice_status}\n"
                f"  Disponibile: {avail_status}\n"
                f"  Modello: {config.voice_model}\n"
                f"  Volume: {config.voice_volume}"
            )
            return {
                "action": "message",
                "data": text
            }
        
        elif subcmd == "test":
            if voice_engine.is_available():
                test_text = "Ciao! Questa è una prova della sintesi vocale di JARVIS."
                if voice_engine.speak(test_text):
                    return {
                        "action": "message",
                        "data": "✓ Test sintesi vocale completato"
                    }
                else:
                    return {
                        "action": "message",
                        "data": "✗ Errore durante il test della sintesi vocale"
                    }
            else:
                return {
                    "action": "message",
                    "data": "✗ Sintesi vocale non disponibile. Verifica Piper e modello vocale."
                }
        
        else:
            return {
                "action": "message",
                "data": f"Comando voce sconosciuto: {subcmd}. Usa: on|off|status|test"
            }

    # MODEL COMMANDS
    if cmd.startswith("/model"):
        parts = cmd.split()
        if len(parts) < 2:
            return {
                "action": "message",
                "data": "Uso: /model list|set [name]|current"
            }
        
        subcmd = parts[1].lower()
        config = get_config()
        
        if subcmd == "list":
            models = get_available_models()
            if not models:
                return {
                    "action": "message",
                    "data": "❌ Nessun modello trovato. Assicurati che Ollama sia online e abbia modelli pullati."
                }
            current = config.model
            model_list = "\n".join(
                f"  {'✓' if m == current else ' '} {m}" 
                for m in models
            )
            return {
                "action": "message",
                "data": f"📦 Modelli disponibili:\n{model_list}"
            }
        
        elif subcmd == "current":
            return {
                "action": "message",
                "data": f"📊 Modello attuale: **{config.model}**"
            }
        
        elif subcmd == "set":
            if len(parts) < 3:
                return {
                    "action": "message",
                    "data": "Uso: /model set [nome_modello]"
                }
            model_name = parts[2]
            available = get_available_models()
            if model_name not in available:
                return {
                    "action": "message",
                    "data": f"❌ Modello '{model_name}' non trovato. Usa /model list per vedere i disponibili."
                }
            config.model = model_name
            config.save()
            return {
                "action": "message",
                "data": f"✓ Modello cambiato a **{model_name}**"
            }
        
        else:
            return {
                "action": "message",
                "data": f"Comando modello sconosciuto: {subcmd}. Usa: list|set [name]|current"
            }

    # EXPORT
    if cmd == "/export":
        history = load_memory()
        if not history:
            return {
                "action": "message",
                "data": "✗ Cronologia vuota, nulla da esportare."
            }
        
        # Crea file markdown
        from datetime import datetime as dt
        now = dt.now()
        filename = f"exports/conversation_{now.strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Conversazione JARVIS\n\n")
                f.write(f"**Data:** {now.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"**Modello:** {get_config().model}\n")
                f.write(f"**Messaggi:** {len(history)}\n\n")
                f.write("---\n\n")
                
                for msg in history:
                    role = "👤 **Tu**" if msg["role"] == "user" else "🤖 **JARVIS**"
                    f.write(f"### {role}\n\n")
                    f.write(f"{msg['content']}\n\n")
            
            return {
                "action": "message",
                "data": f"✓ Conversazione esportata: **{filename}**"
            }
        except Exception as e:
            error(f"Export failed: {e}")
            return {
                "action": "message",
                "data": f"✗ Errore durante l'esportazione: {str(e)}"
            }

    # EXIT
    if cmd in ("/exit", "/quit"):
        return {
            "action": "exit",
            "data": "Chiusura sistema."
        }

    # UNKNOWN
    return {
        "action": "unknown",
        "data": raw
    }
