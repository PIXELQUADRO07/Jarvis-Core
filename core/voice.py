"""
core/voice.py — Facade pubblica per la sintesi vocale.
"""
from core.voice_engine import get_voice_engine


def speak_text(text: str) -> bool:
    return get_voice_engine().speak(text)


def is_voice_available() -> bool:
    return get_voice_engine().is_available()
