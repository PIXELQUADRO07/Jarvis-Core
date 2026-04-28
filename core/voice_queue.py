"""
core/voice_queue.py — Coda prioritaria per la sintesi vocale
e utility per estrarre frasi complete da un buffer di testo in streaming.
"""

from collections import deque
import threading
from typing import Deque, Optional, Tuple

from logger import debug


def pop_complete_sentence(buffer: str) -> Tuple[str, str]:
    """
    Estrae la prima frase completa dal buffer.
    Ritorna (frase_completa, buffer_rimanente).
    Se non ci sono frasi complete, ritorna ("", buffer).
    """
    buffer = buffer.strip()
    if not buffer:
        return "", ""

    terminators = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
    min_pos = len(buffer)
    found_terminator = None

    for term in terminators:
        pos = buffer.find(term)
        if pos != -1 and pos < min_pos:
            min_pos = pos
            found_terminator = term

    if found_terminator is None:
        return "", buffer

    sentence = buffer[: min_pos + len(found_terminator)].strip()
    remaining = buffer[min_pos + len(found_terminator) :].strip()
    return sentence, remaining


class VoiceQueue:
    """Coda thread-safe con priorità per i testi da sintetizzare."""

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
            debug(f"VoiceQueue push priority={priority} text={text[:40]}...")

    def pop(self) -> Optional[str]:
        with self.lock:
            if self.queue:
                text = self.queue.popleft()[1]
                debug(f"VoiceQueue pop text={text[:40]}...")
                return text
            return None

    def empty(self) -> bool:
        with self.lock:
            return len(self.queue) == 0
