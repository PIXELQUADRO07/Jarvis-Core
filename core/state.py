"""
core/state.py — Global JARVIS state.
Thread-safe: spinner and AI threads read/write safely.
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
