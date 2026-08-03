"""
tests/test_voice.py — Regression tests for the voice pipeline bugs:
  1. `/voice on` never started the VoiceEngine worker thread, so text
     queued after a mid-session toggle was never spoken.
  2. apply_ironman() had no subprocess timeout and only caught two
     narrow exception types — a stuck/failing ffmpeg could hang or
     kill the TTS worker thread permanently (silent for the rest of
     the session).
  3. The worker loop itself had no top-level exception handling, so
     any unexpected error in one queued item killed the thread.
"""
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_voice_on_command_starts_the_engine():
    from core.commands import run_command
    from config import JarvisConfig, set_config
    set_config(JarvisConfig())

    fake_engine = MagicMock()
    with patch("core.voice_engine.get_voice_engine", return_value=fake_engine):
        run_command("/voice on")
    fake_engine.start.assert_called_once()


def test_apply_ironman_timeout_does_not_raise():
    from core.audio_fx import apply_ironman
    with patch("core.audio_fx.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=15)):
        assert apply_ironman("in.wav", "out.wav") is False


def test_apply_ironman_unexpected_exception_does_not_raise():
    from core.audio_fx import apply_ironman
    with patch("core.audio_fx.subprocess.run", side_effect=OSError("disk full")):
        assert apply_ironman("in.wav", "out.wav") is False


def test_apply_ironman_passes_a_timeout_to_subprocess():
    from core.audio_fx import apply_ironman
    with patch("core.audio_fx.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        apply_ironman("in.wav", "out.wav")
        _, kwargs = mock_run.call_args
        assert "timeout" in kwargs and kwargs["timeout"] is not None


def test_worker_survives_exception_on_one_item_and_processes_the_next():
    """A bad item in the queue must not permanently kill the worker
    thread — the next queued item should still get processed."""
    from core.voice_engine import VoiceEngine
    from config import JarvisConfig, set_config
    cfg = JarvisConfig()
    cfg.enable_voice = True
    set_config(cfg)

    engine = VoiceEngine()
    calls = []

    def fake_synthesize(text, path):
        calls.append(text)
        if text == "boom":
            raise RuntimeError("simulated synth crash")
        Path(path).write_bytes(b"RIFF....WAVEfmt ")  # dummy content
        return True

    with patch("core.voice_engine.synthesize", side_effect=fake_synthesize), \
         patch.object(engine, "_play", return_value=True), \
         patch("core.voice_engine.shutil.which", return_value=None):  # skip ffmpeg path
        engine.running = True
        engine.queue.push("boom", 1)
        engine.queue.push("still works", 1)
        import threading
        t = threading.Thread(target=engine._worker, daemon=True)
        t.start()
        for _ in range(50):  # up to ~1s
            if calls == ["boom", "still works"]:
                break
            time.sleep(0.02)
        engine.running = False
        t.join(timeout=1)

    assert calls == ["boom", "still works"], (
        "worker thread died after the first item instead of continuing"
    )
