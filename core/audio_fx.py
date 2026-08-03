import subprocess

from logger import debug, error


def apply_ironman(input_wav: str, output_wav: str, timeout: int = 15) -> bool:
    """Apply an Iron Man-style audio filter to the WAV file.

    Runs with a timeout and catches broad exceptions on purpose: this
    used to have neither, and a single stuck/failing ffmpeg call would
    hang or kill the background TTS worker thread — since that thread
    isn't restarted automatically, voice output would then go silent
    for the rest of the session with no visible error.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_wav,
        "-filter:a",
        "asetrate=44100*0.92,atempo=1.0,compand,lowpass=f=3200,highpass=f=90",
        output_wav
    ]
    debug(f"AudioFX apply_ironman: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        check=True, timeout=timeout)
        return True
    except subprocess.CalledProcessError as e:
        error(f"Audio FX error: {e}")
        return False
    except subprocess.TimeoutExpired:
        error(f"Audio FX timed out after {timeout}s — falling back to unprocessed audio")
        return False
    except FileNotFoundError:
        error("ffmpeg not found: install it to apply audio FX")
        return False
    except Exception as e:
        error(f"Audio FX unexpected error: {e}")
        return False
