"""
core/i18n.py — Supporto multi-lingua runtime.
Cambia lingua con /lang [it|en|es|fr|de] senza riavvio.
"""
from typing import Dict

_STRINGS: Dict[str, Dict[str, str]] = {
    "it": {
        "greeting":        "Sistemi online. Sono JARVIS, la tua intelligenza artificiale locale.",
        "help_hint":       "Scrivi /help per i comandi disponibili.",
        "thinking":        "Pensando",
        "processing":      "Elaborando",
        "analyzing":       "Analizzando",
        "responding":      "Rispondo",
        "error_ollama":    "Ollama non raggiungibile. Assicurati che sia avviato.",
        "voice_on":        "Sintesi vocale abilitata.",
        "voice_off":       "Sintesi vocale disabilitata.",
        "memory_cleared":  "Memoria conversazione azzerata.",
        "rate_limit":      "Troppe richieste. Attendi qualche secondo.",
        "offline":         "OFFLINE",
        "online":          "ONLINE",
        "lang_changed":    "Lingua cambiata in: {lang}",
        "session_created": "Sessione creata: {name}",
        "session_switched":"Sessione attiva: {name}",
        "unknown_command": "Comando sconosciuto: {cmd}",
        "export_ok":       "Conversazione esportata: {file}",
        "plugin_list":     "Plugin caricati",
        "silent_on":       "Modalità silenziosa attivata.",
        "silent_off":      "Modalità normale ripristinata.",
    },
    "en": {
        "greeting":        "Systems online. I am JARVIS, your local AI assistant.",
        "help_hint":       "Type /help for available commands.",
        "thinking":        "Thinking",
        "processing":      "Processing",
        "analyzing":       "Analyzing",
        "responding":      "Responding",
        "error_ollama":    "Cannot reach Ollama. Make sure it's running.",
        "voice_on":        "Voice synthesis enabled.",
        "voice_off":       "Voice synthesis disabled.",
        "memory_cleared":  "Conversation memory cleared.",
        "rate_limit":      "Too many requests. Please wait a moment.",
        "offline":         "OFFLINE",
        "online":          "ONLINE",
        "lang_changed":    "Language changed to: {lang}",
        "session_created": "Session created: {name}",
        "session_switched":"Active session: {name}",
        "unknown_command": "Unknown command: {cmd}",
        "export_ok":       "Conversation exported: {file}",
        "plugin_list":     "Loaded plugins",
        "silent_on":       "Silent mode activated.",
        "silent_off":      "Normal mode restored.",
    },
    "es": {
        "greeting":        "Sistemas en línea. Soy JARVIS, tu asistente de IA local.",
        "help_hint":       "Escribe /help para ver los comandos disponibles.",
        "thinking":        "Pensando",
        "processing":      "Procesando",
        "analyzing":       "Analizando",
        "responding":      "Respondiendo",
        "error_ollama":    "No se puede conectar con Ollama. Asegúrate de que esté iniciado.",
        "voice_on":        "Síntesis de voz habilitada.",
        "voice_off":       "Síntesis de voz deshabilitada.",
        "memory_cleared":  "Memoria de conversación borrada.",
        "rate_limit":      "Demasiadas solicitudes. Espera un momento.",
        "offline":         "DESCONECTADO",
        "online":          "CONECTADO",
        "lang_changed":    "Idioma cambiado a: {lang}",
        "session_created": "Sesión creada: {name}",
        "session_switched":"Sesión activa: {name}",
        "unknown_command": "Comando desconocido: {cmd}",
        "export_ok":       "Conversación exportada: {file}",
        "plugin_list":     "Plugins cargados",
        "silent_on":       "Modo silencioso activado.",
        "silent_off":      "Modo normal restaurado.",
    },
    "fr": {
        "greeting":        "Systèmes en ligne. Je suis JARVIS, votre assistant IA local.",
        "help_hint":       "Tapez /help pour les commandes disponibles.",
        "thinking":        "Réflexion",
        "processing":      "Traitement",
        "analyzing":       "Analyse",
        "responding":      "Réponse",
        "error_ollama":    "Ollama inaccessible. Assurez-vous qu'il est démarré.",
        "voice_on":        "Synthèse vocale activée.",
        "voice_off":       "Synthèse vocale désactivée.",
        "memory_cleared":  "Mémoire de conversation effacée.",
        "rate_limit":      "Trop de requêtes. Veuillez patienter.",
        "offline":         "HORS LIGNE",
        "online":          "EN LIGNE",
        "lang_changed":    "Langue changée en: {lang}",
        "session_created": "Session créée: {name}",
        "session_switched":"Session active: {name}",
        "unknown_command": "Commande inconnue: {cmd}",
        "export_ok":       "Conversation exportée: {file}",
        "plugin_list":     "Plugins chargés",
        "silent_on":       "Mode silencieux activé.",
        "silent_off":      "Mode normal restauré.",
    },
    "de": {
        "greeting":        "Systeme online. Ich bin JARVIS, Ihr lokaler KI-Assistent.",
        "help_hint":       "Tippe /help für verfügbare Befehle.",
        "thinking":        "Denke",
        "processing":      "Verarbeite",
        "analyzing":       "Analysiere",
        "responding":      "Antworte",
        "error_ollama":    "Ollama nicht erreichbar. Stellen Sie sicher, dass es läuft.",
        "voice_on":        "Sprachsynthese aktiviert.",
        "voice_off":       "Sprachsynthese deaktiviert.",
        "memory_cleared":  "Gesprächsspeicher geleert.",
        "rate_limit":      "Zu viele Anfragen. Bitte warten.",
        "offline":         "OFFLINE",
        "online":          "ONLINE",
        "lang_changed":    "Sprache geändert auf: {lang}",
        "session_created": "Sitzung erstellt: {name}",
        "session_switched":"Aktive Sitzung: {name}",
        "unknown_command": "Unbekannter Befehl: {cmd}",
        "export_ok":       "Gespräch exportiert: {file}",
        "plugin_list":     "Geladene Plugins",
        "silent_on":       "Stiller Modus aktiviert.",
        "silent_off":      "Normaler Modus wiederhergestellt.",
    },
}

_current_lang = "it"


def set_language(lang: str) -> bool:
    global _current_lang
    if lang in _STRINGS:
        _current_lang = lang
        return True
    return False


def get_language() -> str:
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Traduce una chiave nella lingua corrente."""
    lang_dict = _STRINGS.get(_current_lang, _STRINGS["it"])
    text = lang_dict.get(key, _STRINGS["it"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
