"""
core/state.py — Stato globale di JARVIS
Thread-safe: spinner e AI thread leggono/scrivono in sicurezza.
"""
import threading

_lock  = threading.Lock()
_state = "idle"

def set_status(s: str) -> None:
    global _state
    with _lock:
        _state = s

def get_status() -> str:
    with _lock:
        return _state
