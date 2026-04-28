import subprocess

from logger import debug, error


def apply_ironman(input_wav: str, output_wav: str) -> bool:
    """Applica un filtro audio in stile Iron Man al file WAV."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_wav,
        "-filter:a",
        "asetrate=44100*0.92,atempo=1.0,compand,lowpass=f=3200,highpass=f=90",
        output_wav
    ]
    debug(f"AudioFX apply_ironman: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError as e:
        error(f"Errore audio FX: {e}")
        return False
    except FileNotFoundError:
        error("ffmpeg non trovato: installalo per applicare l'audio FX")
        return False
