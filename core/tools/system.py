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
    else:
        return "Il controllo RAM è supportato solo su Linux in questa versione di JARVIS."


def get_disk_usage() -> str:
    """Mostra l'utilizzo dello spazio su disco"""
    try:
        result = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
        return f"Utilizzo spazio disco:\n{result.stdout.strip()}"
    except subprocess.CalledProcessError:
        return "Impossibile ottenere informazioni sul disco."
    except FileNotFoundError:
        return "Comando 'df' non disponibile."


def get_uptime() -> str:
    """Mostra il tempo di attività del sistema"""
    try:
        result = subprocess.run(["uptime", "-p"], capture_output=True, text=True, check=True)
        return f"Tempo di attività: {result.stdout.strip()}"
    except subprocess.CalledProcessError:
        try:
            # Fallback per sistemi che non hanno -p
            result = subprocess.run(["uptime"], capture_output=True, text=True, check=True)
            return f"Uptime: {result.stdout.strip()}"
        except subprocess.CalledProcessError:
            return "Impossibile ottenere l'uptime."
    except FileNotFoundError:
        return "Comando 'uptime' non disponibile."


def get_network_info() -> str:
    """Mostra informazioni sulla rete"""
    try:
        result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True, check=True)
        # Filtra solo le interfacce attive per brevità
        lines = result.stdout.strip().split('\n')
        filtered = []
        current_iface = None
        for line in lines:
            if line.startswith(' ') and current_iface:
                if 'inet ' in line or 'inet6 ' in line:
                    filtered.append(f"{current_iface}: {line.strip()}")
            elif not line.startswith(' ') and ':' in line:
                current_iface = line.split(':')[1].strip()
        if filtered:
            return "Interfacce di rete:\n" + '\n'.join(filtered[:5])  # Limita a 5 interfacce
        return "Nessuna interfaccia di rete attiva trovata."
    except subprocess.CalledProcessError:
        return "Impossibile ottenere informazioni di rete."
    except FileNotFoundError:
        return "Comando 'ip' non disponibile."


def get_processes() -> str:
    """Mostra i processi in esecuzione (primi 10)"""
    try:
        result = subprocess.run(["ps", "aux", "--sort=-%cpu"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        header = lines[0] if lines else ""
        processes = lines[1:11]  # Header + primi 10 processi
        return f"Processi (ordinati per CPU):\n{header}\n" + '\n'.join(processes)
    except subprocess.CalledProcessError:
        return "Impossibile ottenere la lista dei processi."
    except FileNotFoundError:
        return "Comando 'ps' non disponibile."


def get_temperature() -> str:
    """Mostra la temperatura del sistema se disponibile"""
    try:
        result = subprocess.run(["sensors"], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output:
            # Estrai solo le temperature principali
            lines = output.split('\n')
            temps = [line for line in lines if '°C' in line and not line.startswith('Adapter')]
            if temps:
                return "Temperature sistema:\n" + '\n'.join(temps[:5])
        return "Informazioni temperatura non disponibili."
    except subprocess.CalledProcessError:
        return "Impossibile ottenere le temperature."
    except FileNotFoundError:
        return "Comando 'sensors' non disponibile (installa lm-sensors)."


def get_battery_info() -> str:
    """Mostra informazioni sulla batteria se disponibile"""
    try:
        # Prova prima con upower
        result = subprocess.run(["upower", "-e"], capture_output=True, text=True, check=True)
        batteries = [line for line in result.stdout.strip().split('\n') if 'battery' in line]
        if batteries:
            for battery in batteries[:1]:  # Prima batteria
                info = subprocess.run(["upower", "-i", battery], capture_output=True, text=True, check=True)
                return f"Informazioni batteria:\n{info.stdout.strip()}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: controlla /sys/class/power_supply/
    battery_path = Path("/sys/class/power_supply")
    if battery_path.exists():
        batteries = [d for d in battery_path.iterdir() if d.is_dir() and 'BAT' in d.name]
        if batteries:
            bat = batteries[0]
            try:
                capacity = (bat / "capacity").read_text().strip()
                status = (bat / "status").read_text().strip()
                return f"Batteria: {capacity}% ({status})"
            except FileNotFoundError:
                pass

    return "Nessuna batteria rilevata."


def install_package(package: str) -> str:
    """Installa un pacchetto (richiede root)"""
    if not _is_root():
        return "Installazione pacchetti richiede privilegi di root."

    distro = detect_distro().lower()
    if "arch" in distro or "manjaro" in distro:
        cmd = f"pacman -S --noconfirm {package}"
    elif any(d in distro for d in ("ubuntu", "debian", "linux mint", "popos")):
        cmd = f"apt update && apt install -y {package}"
    elif "fedora" in distro:
        cmd = f"dnf install -y {package}"
    elif any(d in distro for d in ("opensuse", "suse")):
        cmd = f"zypper install -y {package}"
    else:
        return f"Installazione pacchetti non supportata per: {distro}"

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, timeout=300)
        return f"Pacchetto '{package}' installato con successo."
    except subprocess.CalledProcessError as exc:
        return f"Errore nell'installazione di '{package}': {exc.stderr.strip() or exc.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return f"Installazione di '{package}' scaduta."
    except Exception as exc:
        return f"Impossibile installare '{package}': {exc}"


def remove_package(package: str) -> str:
    """Rimuove un pacchetto (richiede root)"""
    if not _is_root():
        return "Rimozione pacchetti richiede privilegi di root."

    distro = detect_distro().lower()
    if "arch" in distro or "manjaro" in distro:
        cmd = f"pacman -R --noconfirm {package}"
    elif any(d in distro for d in ("ubuntu", "debian", "linux mint", "popos")):
        cmd = f"apt remove -y {package}"
    elif "fedora" in distro:
        cmd = f"dnf remove -y {package}"
    elif any(d in distro for d in ("opensuse", "suse")):
        cmd = f"zypper remove -y {package}"
    else:
        return f"Gestione pacchetti non supportata per: {distro}"

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, timeout=300)
        return f"Pacchetto '{package}' rimosso con successo."
    except subprocess.CalledProcessError as exc:
        return f"Errore nella rimozione di '{package}': {exc.stderr.strip() or exc.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return f"rimozione di '{package}' scaduta."
    except Exception as exc:
        return f"Impossibile rimuovere '{package}': {exc}"


def manage_service(action: str, service: str) -> str:
    """Gestisce servizi systemd (richiede root)"""
    if not _is_root():
        return "Gestione servizi richiede privilegi di root."

    valid_actions = ["start", "stop", "restart", "status", "enable", "disable"]
    if action not in valid_actions:
        return f"Azione '{action}' non valida. Azioni disponibili: {', '.join(valid_actions)}"

    try:
        if action == "status":
            result = subprocess.run(["systemctl", "status", service], capture_output=True, text=True)
        else:
            result = subprocess.run(["systemctl", action, service], capture_output=True, text=True, check=True)
        
        if action == "status":
            return f"Stato servizio '{service}':\n{result.stdout.strip()[:1000]}"
        else:
            return f"Servizio '{service}' {action}ato con successo."
    except subprocess.CalledProcessError as exc:
        return f"Errore nella gestione del servizio '{service}': {exc.stderr.strip() or exc.stdout.strip()}"
    except FileNotFoundError:
        return "systemctl non disponibile (non è un sistema systemd)."
    except Exception as exc:
        return f"Impossibile gestire il servizio '{service}': {exc}"


def set_hostname(new_hostname: str) -> str:
    """Cambia l'hostname del sistema (richiede root)"""
    if not _is_root():
        return "Cambio hostname richiede privilegi di root."

    # Valida hostname
    if not new_hostname or len(new_hostname) > 64:
        return "Hostname non valido (deve essere non vuoto e < 64 caratteri)."

    try:
        # Cambia hostname temporaneamente
        subprocess.run(["hostnamectl", "set-hostname", new_hostname], check=True, capture_output=True, text=True)
        return f"Hostname cambiato a '{new_hostname}'. Riavvia per applicare completamente."
    except subprocess.CalledProcessError as exc:
        return f"Errore nel cambio hostname: {exc.stderr.strip() or exc.stdout.strip()}"
    except FileNotFoundError:
        return "hostnamectl non disponibile."
    except Exception as exc:
        return f"Impossibile cambiare hostname: {exc}"


def get_system_logs(lines: int = 20) -> str:
    """Mostra gli ultimi log di sistema (richiede root per log completi)"""
    try:
        result = subprocess.run(["journalctl", "-n", str(lines), "--no-pager"], capture_output=True, text=True, check=True)
        return f"Ultimi {lines} log di sistema:\n{result.stdout.strip()}"
    except subprocess.CalledProcessError as exc:
        return f"Errore nell'accesso ai log: {exc.stderr.strip() or exc.stdout.strip()}"
    except FileNotFoundError:
        return "journalctl non disponibile (non è un sistema systemd)."
    except Exception as exc:
        return f"Impossibile accedere ai log: {exc}"
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

    if any(phrase in q for phrase in ("spazio disco", "disco", "quanto spazio", "spazio disponibile", "df", "disk usage")):
        return get_disk_usage()

    if any(phrase in q for phrase in ("uptime", "tempo di attività", "quanto tempo", "da quanto è acceso")):
        return get_uptime()

    if any(phrase in q for phrase in ("rete", "network", "ip", "interfacce", "connessioni")):
        return get_network_info()

    if any(phrase in q for phrase in ("processi", "ps", "cosa sta girando", "programmi attivi")):
        return get_processes()

    if any(phrase in q for phrase in ("temperatura", "temperature", "caldo", "cpu temp", "sensors")):
        return get_temperature()

    if any(phrase in q for phrase in ("batteria", "battery", "carica", "quanta batteria")):
        return get_battery_info()

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

    # Comandi che richiedono root
    if q.startswith("installa ") or q.startswith("install "):
        package = q.split(" ", 1)[1].strip()
        return install_package(package)

    if q.startswith("rimuovi ") or q.startswith("remove ") or q.startswith("uninstall "):
        package = q.split(" ", 1)[1].strip()
        return remove_package(package)

    if any(phrase in q for phrase in ("servizio ", "service ")):
        parts = q.split()
        if len(parts) >= 3:
            action = parts[1]
            service = parts[2]
            return manage_service(action, service)

    if q.startswith("hostname ") or q.startswith("cambia hostname "):
        if "hostname " in q:
            hostname_part = q.split("hostname ", 1)[1].strip()
        else:
            hostname_part = q.split("cambia hostname ", 1)[1].strip()
        return set_hostname(hostname_part)

    if any(phrase in q for phrase in ("log", "logs", "journal", "system logs")):
        lines = 20
        if "ultimi" in q or "last" in q:
            # Cerca numero
            import re
            match = re.search(r'(\d+)', q)
            if match:
                lines = min(int(match.group(1)), 100)  # Max 100 righe
        return get_system_logs(lines)

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
