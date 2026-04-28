"""
core/voice.py — Facade pubblica per la sintesi vocale.
Tutti i moduli del progetto importano speak_text / is_voice_available da qui.
L'implementazione reale è in core/voice_engine.py.
"""

from core.voice_engine import get_voice_engine


def speak_text(text: str) -> bool:
    """Accoda il testo per la sintesi vocale. Non bloccante."""
    return get_voice_engine().speak(text)


def is_voice_available() -> bool:
    """True se Piper è installato, il modello esiste e la voce è abilitata."""
    return get_voice_engine().is_available()
