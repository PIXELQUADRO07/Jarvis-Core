"""
core/voice_engine.py — Motore vocale asincrono con Piper TTS + Iron Man FX.
Worker daemon thread: sintetizza, applica FX, riproduce.
"""
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

from config import get_config
from core.audio_fx import apply_ironman
from core.tts_piper import synthesize
from core.voice_queue import VoiceQueue
from logger import debug, error


class VoiceEngine:
    _PLAYERS = [["aplay"], ["paplay"], ["play"], ["cvlc", "--play-and-exit"], ["mplayer"]]

    def __init__(self):
        self.queue   = VoiceQueue()
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._worker, daemon=True, name="jarvis-tts")
        self._thread.start()
        debug("VoiceEngine started")

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            debug("VoiceEngine stopped")

    def speak(self, text: str, priority: int = 1) -> bool:
        text = text.strip()
        if not text or not self.is_available():
            return False
        # Rimuovi markdown per il TTS
        from core.llm import strip_markdown
        self.queue.push(strip_markdown(text), priority)
        return True

    def interrupt(self) -> None:
        """Interrompe la frase corrente svuotando la coda."""
        self.queue.clear()

    def is_available(self) -> bool:
        cfg = get_config()
        return (
            cfg.enable_voice
            and Path(cfg.voice_model).exists()
            and shutil.which("piper") is not None
        )

    def _worker(self) -> None:
        while self.running:
            text = self.queue.pop()
            if not text:
                time.sleep(0.05)
                continue
            raw = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            fx  = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            try:
                if not synthesize(text, raw):
                    continue
                play_path = fx if (shutil.which("ffmpeg") and apply_ironman(raw, fx)) else raw
                self._play(play_path)
            finally:
                for p in {raw, fx}:
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except OSError:
                        pass

    def _play(self, path: str) -> bool:
        for player in self._PLAYERS:
            if not shutil.which(player[0]):
                continue
            try:
                r = subprocess.run(player + [path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   timeout=30)
                if r.returncode == 0:
                    return True
            except Exception as e:
                error(f"Player {player[0]} error: {e}")
        return False


_engine: Optional[VoiceEngine] = None


def get_voice_engine() -> VoiceEngine:
    global _engine
    if _engine is None:
        _engine = VoiceEngine()
    return _engine
