"""
core/voice_engine.py — Motore vocale con coda e TTS Piper.
Questo è l'unico motore vocale attivo. Viene avviato da main.py.
"""

import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from config import get_config
from core.tts_piper import synthesize
from core.voice_queue import VoiceQueue
from logger import debug, error


class VoiceEngine:
    """
    Motore vocale asincrono.
    - Accoda testi tramite speak()
    - Un worker thread consuma la coda: sintetizza con Piper,
      applica FX Iron Man con ffmpeg, riproduce con aplay/paplay/...
    """

    def __init__(self):
        self.queue = VoiceQueue()
        self.running = False
        self._thread: threading.Thread | None = None
        self._player_commands = [
            ["aplay"],
            ["paplay"],
            ["play"],
            ["cvlc", "--play-and-exit"],
            ["mplayer"],
        ]

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        debug("VoiceEngine started")

    def stop(self) -> None:
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
            debug("VoiceEngine stopped")

    def speak(self, text: str, priority: int = 1) -> bool:
        """Accoda un testo per la sintesi. Non bloccante."""
        text = text.strip()
        if not text:
            return False
        if not self.is_available():
            debug("VoiceEngine speak skipped: voice unavailable")
            return False
        self.queue.push(text, priority)
        return True

    def is_available(self) -> bool:
        config = get_config()
        model_path = Path(config.voice_model)
        return (
            config.enable_voice
            and model_path.exists()
            and shutil.which("piper") is not None
        )

    # ── Worker ────────────────────────────────────────────────────────────────

    def _worker(self) -> None:
        while self.running:
            text = self.queue.pop()
            if not text:
                time.sleep(0.05)
                continue

            raw_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            fx_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

            try:
                if not synthesize(text, raw_wav):
                    continue

                # Riproduce il file generato senza effetti audio aggiuntivi
                play_path = raw_wav
                self._play_file(play_path)
            finally:
                for path in {raw_wav, fx_wav}:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except OSError as exc:
                        error(f"Errore pulizia file temporaneo: {exc}")

    def _play_file(self, path: str) -> bool:
        for player in self._player_commands:
            if shutil.which(player[0]) is None:
                debug(f"Player non trovato: {player[0]}")
                continue
            try:
                debug(f"VoiceEngine playback: {' '.join(player)} {path}")
                result = subprocess.run(
                    player + [path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
                if result.returncode == 0:
                    debug(f"Audio riprodotto con: {player[0]}")
                    return True
                debug(f"Player {player[0]} fallito con codice {result.returncode}")
            except subprocess.TimeoutExpired:
                debug(f"Player timeout: {player[0]}")
            except Exception as exc:
                error(f"Errore playback {player[0]}: {exc}")
        error("Nessun player audio disponibile per la riproduzione")
        return False


# ── Singleton ──────────────────────────────────────────────────────────────────

_voice_engine: VoiceEngine | None = None


def get_voice_engine() -> VoiceEngine:
    """Restituisce (e crea se necessario) il motore vocale globale."""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine()
    return _voice_engine
