import subprocess

from config import get_config
from logger import debug, error


def synthesize(text: str, output_path: str) -> bool:
    """Genera un file WAV usando Piper."""
    config = get_config()
    model = config.voice_model
    cmd = [
        "piper",
        "--model", model,
        "--output_file", output_path,
        "--length_scale", str(config.voice_length_scale),
        "--sentence_silence", str(config.voice_sentence_silence),
        "--volume", str(config.voice_volume),
    ]
    debug(f"TTS Piper synthesize: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            input=text.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=40
        )
        if result.returncode != 0:
            error(f"Piper error: {result.stderr.decode(errors='ignore')}")
            return False
        return True
    except subprocess.TimeoutExpired:
        error("Timeout durante la sintesi Piper")
        return False
    except Exception as e:
        error(f"Errore durante la sintesi Piper: {e}")
        return False
