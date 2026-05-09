"""
core/voice_queue.py — Coda prioritaria TTS thread-safe.
"""
from collections import deque
import threading
from typing import Deque, Optional, Tuple

from logger import debug


def pop_complete_sentence(buffer: str) -> Tuple[str, str]:
    """Estrae la prima frase completa dal buffer streaming."""
    buffer = buffer.strip()
    if not buffer:
        return "", ""
    terminators = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
    min_pos, found = len(buffer), None
    for term in terminators:
        pos = buffer.find(term)
        if pos != -1 and pos < min_pos:
            min_pos, found = pos, term
    if found is None:
        return "", buffer
    sentence  = buffer[: min_pos + len(found)].strip()
    remaining = buffer[min_pos + len(found) :].strip()
    return sentence, remaining


class VoiceQueue:
    """Coda thread-safe con priorità per testi TTS."""

    def __init__(self):
        self.queue: Deque[Tuple[int, str]] = deque()
        self.lock = threading.Lock()

    def push(self, text: str, priority: int = 1) -> None:
        text = text.strip()
        if not text:
            return
        with self.lock:
            self.queue.append((priority, text))
            self.queue = deque(sorted(self.queue, key=lambda x: x[0]))
            debug(f"VoiceQueue push priority={priority} len={len(text)}")

    def pop(self) -> Optional[str]:
        with self.lock:
            if self.queue:
                return self.queue.popleft()[1]
            return None

    def empty(self) -> bool:
        with self.lock:
            return len(self.queue) == 0

    def clear(self) -> None:
        with self.lock:
            self.queue.clear()
