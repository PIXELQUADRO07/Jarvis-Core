import os
import platform
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus


OS_RELEASE = Path("/etc/os-release")


def detect_distro() -> str:
    if platform.system() != "Linux":
        return platform.system()

    try:
        content = OS_RELEASE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "Linux"

    for line in content.splitlines():
        if line.startswith("NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return "Linux"


def _is_root() -> bool:
    return os.geteuid() == 0


def get_system_info() -> str:
    distro = detect_distro()
    header = f"Distro: {distro}. Kernel: {platform.release()}."
    status = "Eseguito come root." if _is_root() else "Non eseguito come root."
    return f"{header}\n{status}"


def update_system() -> str:
    distro = detect_distro().lower()
    if not _is_root():
        return (
            "Aggiornamenti bloccati: per aggiornare il sistema devi eseguire JARVIS come root "
            "o usare sudo nel terminale.")

    if "arch" in distro or "manjaro" in distro:
        cmd = "pacman -Syu --noconfirm"
    elif any(d in distro for d in ("ubuntu", "debian", "linux mint", "popos")):
        cmd = "apt update && apt upgrade -y"
    elif "fedora" in distro:
        cmd = "dnf upgrade --refresh -y"
    elif any(d in distro for d in ("opensuse", "suse")):
        cmd = "zypper refresh && zypper update -y"
    else:
        return f"Distro non riconosciuta per aggiornamenti automatici: {distro}."

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, timeout=1200)
        return f"Aggiornamento completato.\n{result.stdout.strip()[:2000]}"
    except subprocess.CalledProcessError as exc:
        return f"Errore durante l'aggiornamento del sistema:\n{exc.stderr.strip() or exc.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return "L'aggiornamento sta impiegando troppo tempo e ha superato il timeout."
    except Exception as exc:
        return f"Impossibile eseguire l'aggiornamento: {exc}"


def _parse_proc_meminfo() -> dict[str, int]:
    meminfo = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                meminfo[key.strip()] = int(value.strip().split()[0])
    except FileNotFoundError:
        pass
    return meminfo


def get_ram_info() -> str:
    system = platform.system()
    if system == "Linux":
        data = _parse_proc_meminfo()
        if not data:
            return "Non è stato possibile leggere le informazioni sulla RAM dal sistema."

        total = data.get("MemTotal")
        free = data.get("MemFree")
        available = data.get("MemAvailable")
        buffers = data.get("Buffers")
        cached = data.get("Cached")

        if total is None or available is None:
            return "Non è stato possibile ottenere i dettagli della RAM." 

        used = total - available
        percent = round(used / total * 100, 1) if total else 0.0

        def mb(value: int) -> str:
            return f"{value // 1024} MB"

        details = [
            f"RAM totale: {mb(total)}",
            f"RAM disponibile: {mb(available)}",
            f"RAM usata: {mb(used)} ({percent}%)",
        ]
        if free is not None:
            details.append(f"RAM libera: {mb(free)}")
        if buffers is not None:
            details.append(f"Buffers: {mb(buffers)}")
        if cached is not None:
            details.append(f"Cache: {mb(cached)}")
        return ". ".join(details)

    return "Il controllo RAM è supportato solo su Linux in questa versione di JARVIS."


def open_firefox(search: Optional[str] = None) -> str:
    url = "https://www.google.com"
    if search:
        url = f"https://www.google.com/search?q={quote_plus(search)}"

    try:
        opened = webbrowser.open(url, new=2)
        if opened:
            if search:
                return f"Apro Firefox e cerco: {search}"
            return "Apro Firefox."
    except Exception:
        pass

    try:
        if search:
            subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Apro Firefox e cerco: {search}"
        subprocess.Popen(["firefox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Apro Firefox."
    except FileNotFoundError:
        return "Firefox non è installato o non è trovato nel PATH."
    except Exception as exc:
        return f"Impossibile aprire Firefox: {exc}"


def system_command(query: str) -> Optional[str]:
    q = query.lower().strip()

    if any(phrase in q for phrase in ("che distro", "controlla distro", "mostra distro", "nome distro", "che sistema")):
        return get_system_info()

    if any(phrase in q for phrase in ("ram", "memoria", "quanta ram", "memoria disponibile", "memoria libera", "controlla la mia ram", "controlla ram")):
        return get_ram_info()

    if any(phrase in q for phrase in ("aggiorna sistema", "aggiorna pacchetti", "installa aggiornamenti", "system update", "apt update", "pacman -syu")):
        return update_system()

    if "apri firefox" in q or "cerca su firefox" in q or "apri browser" in q:
        search = ""
        if "cerca" in q:
            words = q.split("cerca", 1)[1].strip()
            if words:
                search = words
        return open_firefox(search or None)

    if q.startswith("firefox") and "cerca" in q:
        words = q.split("cerca", 1)[1].strip()
        return open_firefox(words or None)

    if q.startswith("apri "):
        app = q[5:].strip().split()[0]  # take first word
        if app:
            try:
                subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Aperto {app}."
            except FileNotFoundError:
                return f"{app} non trovato nel PATH."
            except Exception as e:
                return f"Errore nell'aprire {app}: {e}"

    if any(phrase in q for phrase in ("cpu", "processori", "quanti cpu", "cpu info", "numero cpu", "quante cpu")):
        try:
            result = subprocess.run(["nproc"], capture_output=True, text=True, check=True)
            num_cpu = result.stdout.strip()
            return f"Numero di CPU logici: {num_cpu}"
        except subprocess.CalledProcessError:
            return "Impossibile determinare il numero di CPU."
        except FileNotFoundError:
            return "Comando 'nproc' non disponibile."

    if any(phrase in q for phrase in ("mi chiamo", "il mio nome è")):
        # Extract name - only match "mi chiamo" or "il mio nome è", not bare "sono"
        import re
        match = re.search(r'(?:mi chiamo|il mio nome è)\s+(.+)', q, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            return f"Ok, mi ricorderò che ti chiami {name}."
    
    if q.startswith("sono ") and " in " not in q and " a " not in q:
        # Only match "sono [name]" at the start, not "sono in/a [city]"
        import re
        match = re.search(r'^sono\s+([a-z]+)(?:\s|$)', q, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            return f"Ok, mi ricorderò che ti chiami {name}."

    return None
