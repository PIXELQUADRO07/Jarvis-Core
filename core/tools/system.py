import os
import platform
import re
import shlex
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from logger import warning

OS_RELEASE = Path("/etc/os-release")

# Package/service/hostname names must match this to be passed to a shell
# package manager. This blocks shell metacharacters (`;`, `&&`, `|`, `$()`,
# backticks, quotes, whitespace...) that would otherwise let a chat message
# break out of the intended argument and run arbitrary commands.
_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+._@-]{0,127}$")


def _validate_safe_name(value: str, kind: str = "name") -> Optional[str]:
    """Return the value if it looks like a single safe token, else None."""
    value = value.strip()
    if not value or not _SAFE_NAME_RE.match(value):
        warning(f"Rejected unsafe {kind}: {value!r}")
        return None
    return value


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
    status = "Running as root." if _is_root() else "Not running as root."
    return f"{header}\n{status}"


def _run_argv_sequence(commands: list, timeout: int) -> str:
    """Run a sequence of argv lists (no shell, so no injection surface),
    stopping and reporting on the first failure."""
    outputs = []
    for argv in commands:
        try:
            result = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return f"Command not found: {argv[0]}"
        except subprocess.TimeoutExpired:
            return f"Command timed out: {' '.join(argv)}"
        outputs.append(result.stdout.strip())
        if result.returncode != 0:
            return f"Command failed ({' '.join(argv)}):\n{(result.stderr or result.stdout).strip()}"
    return "\n".join(o for o in outputs if o) or "(no output)"


def update_system() -> str:
    from config import get_config
    if not get_config().enable_package_management:
        return ("System updates are disabled. Set enable_package_management: true "
                "in jarvis_config.json (or JARVIS_ENABLE_PACKAGE_MANAGEMENT=true) "
                "to allow JARVIS to manage packages.")

    distro = detect_distro().lower()
    if not _is_root():
        return "System updates are blocked: run JARVIS as root or use sudo."

    if "arch" in distro or "manjaro" in distro:
        commands = [["pacman", "-Syu", "--noconfirm"]]
    elif any(d in distro for d in ("ubuntu", "debian", "linux mint", "popos")):
        commands = [["apt", "update"], ["apt", "upgrade", "-y"]]
    elif "fedora" in distro:
        commands = [["dnf", "upgrade", "--refresh", "-y"]]
    elif any(d in distro for d in ("opensuse", "suse")):
        commands = [["zypper", "refresh"], ["zypper", "update", "-y"]]
    else:
        return f"Unknown distribution for automatic updates: {distro}."

    try:
        return f"Update completed.\n{_run_argv_sequence(commands, timeout=1200)[:2000]}"
    except Exception as exc:
        return f"Unable to perform update: {exc}"


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
            return "Unable to read RAM information from the system."

        total = data.get("MemTotal")
        free = data.get("MemFree")
        available = data.get("MemAvailable")
        buffers = data.get("Buffers")
        cached = data.get("Cached")

        if total is None or available is None:
            return "Unable to get RAM details."

        used = total - available
        percent = round(used / total * 100, 1) if total else 0.0

        def mb(value: int) -> str:
            return f"{value // 1024} MB"

        details = [
            f"Total RAM: {mb(total)}",
            f"Available RAM: {mb(available)}",
            f"Used RAM: {mb(used)} ({percent}%)",
        ]
        if free is not None:
            details.append(f"Free RAM: {mb(free)}")
        if buffers is not None:
            details.append(f"Buffers: {mb(buffers)}")
        if cached is not None:
            details.append(f"Cache: {mb(cached)}")
        return ". ".join(details)
    return "RAM check is supported only on Linux in this version of JARVIS."


def get_disk_usage() -> str:
    """Show disk usage."""
    try:
        result = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
        return f"Disk usage:\n{result.stdout.strip()}"
    except subprocess.CalledProcessError:
        return "Unable to get disk usage information."
    except FileNotFoundError:
        return "The 'df' command is not available."


def get_uptime() -> str:
    """Show system uptime."""
    try:
        result = subprocess.run(["uptime", "-p"], capture_output=True, text=True, check=True)
        return f"Uptime: {result.stdout.strip()}"
    except subprocess.CalledProcessError:
        try:
            result = subprocess.run(["uptime"], capture_output=True, text=True, check=True)
            return f"Uptime: {result.stdout.strip()}"
        except subprocess.CalledProcessError:
            return "Unable to get uptime."
    except FileNotFoundError:
        return "The 'uptime' command is not available."


def get_network_info() -> str:
    """Show network information."""
    try:
        result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True, check=True)
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
            return "Network interfaces:\n" + '\n'.join(filtered[:5])
        return "No active network interfaces found."
    except subprocess.CalledProcessError:
        return "Unable to get network information."
    except FileNotFoundError:
        return "The 'ip' command is not available."


def get_processes() -> str:
    """Show running processes (top 10 by CPU)."""
    try:
        result = subprocess.run(["ps", "aux", "--sort=-%cpu"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        header = lines[0] if lines else ""
        processes = lines[1:11]
        return f"Processes (sorted by CPU):\n{header}\n" + '\n'.join(processes)
    except subprocess.CalledProcessError:
        return "Unable to get process list."
    except FileNotFoundError:
        return "The 'ps' command is not available."


def get_temperature() -> str:
    """Show system temperature if available."""
    try:
        result = subprocess.run(["sensors"], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output:
            lines = output.split('\n')
            temps = [line for line in lines if '°C' in line and not line.startswith('Adapter')]
            if temps:
                return "System temperatures:\n" + '\n'.join(temps[:5])
        return "Temperature information is not available."
    except subprocess.CalledProcessError:
        return "Unable to get temperature data."
    except FileNotFoundError:
        return "The 'sensors' command is not available (install lm-sensors)."


def get_battery_info() -> str:
    """Show battery information if available."""
    try:
        result = subprocess.run(["upower", "-e"], capture_output=True, text=True, check=True)
        batteries = [line for line in result.stdout.strip().split('\n') if 'battery' in line]
        if batteries:
            for battery in batteries[:1]:
                info = subprocess.run(["upower", "-i", battery], capture_output=True, text=True, check=True)
                return f"Battery information:\n{info.stdout.strip()}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    battery_path = Path("/sys/class/power_supply")
    if battery_path.exists():
        batteries = [d for d in battery_path.iterdir() if d.is_dir() and 'BAT' in d.name]
        if batteries:
            bat = batteries[0]
            try:
                capacity = (bat / "capacity").read_text().strip()
                status = (bat / "status").read_text().strip()
                return f"Battery: {capacity}% ({status})"
            except FileNotFoundError:
                pass

    return "No battery detected."


def install_package(package: str) -> str:
    """Install a package (requires root + explicit opt-in + a safe package name)."""
    from config import get_config
    if not get_config().enable_package_management:
        return ("Package management is disabled. Set enable_package_management: true "
                "in jarvis_config.json to allow JARVIS to install/remove packages.")
    if not _is_root():
        return "Package installation requires root privileges."

    safe_pkg = _validate_safe_name(package, kind="package name")
    if safe_pkg is None:
        return f"Refused: '{package}' is not a valid package name."

    distro = detect_distro().lower()
    if "arch" in distro or "manjaro" in distro:
        commands = [["pacman", "-S", "--noconfirm", safe_pkg]]
    elif any(d in distro for d in ("ubuntu", "debian", "linux mint", "popos")):
        commands = [["apt", "update"], ["apt", "install", "-y", safe_pkg]]
    elif "fedora" in distro:
        commands = [["dnf", "install", "-y", safe_pkg]]
    elif any(d in distro for d in ("opensuse", "suse")):
        commands = [["zypper", "install", "-y", safe_pkg]]
    else:
        return f"Package installation not supported for: {distro}"

    try:
        _run_argv_sequence(commands, timeout=300)
        return f"Package '{safe_pkg}' installed successfully."
    except Exception as exc:
        return f"Unable to install '{safe_pkg}': {exc}"


def remove_package(package: str) -> str:
    """Remove a package (requires root + explicit opt-in + a safe package name)."""
    from config import get_config
    if not get_config().enable_package_management:
        return ("Package management is disabled. Set enable_package_management: true "
                "in jarvis_config.json to allow JARVIS to install/remove packages.")
    if not _is_root():
        return "Package removal requires root privileges."

    safe_pkg = _validate_safe_name(package, kind="package name")
    if safe_pkg is None:
        return f"Refused: '{package}' is not a valid package name."

    distro = detect_distro().lower()
    if "arch" in distro or "manjaro" in distro:
        commands = [["pacman", "-R", "--noconfirm", safe_pkg]]
    elif any(d in distro for d in ("ubuntu", "debian", "linux mint", "popos")):
        commands = [["apt", "remove", "-y", safe_pkg]]
    elif "fedora" in distro:
        commands = [["dnf", "remove", "-y", safe_pkg]]
    elif any(d in distro for d in ("opensuse", "suse")):
        commands = [["zypper", "remove", "-y", safe_pkg]]
    else:
        return f"Package removal not supported for: {distro}"

    try:
        _run_argv_sequence(commands, timeout=300)
        return f"Package '{safe_pkg}' removed successfully."
    except Exception as exc:
        return f"Unable to remove '{safe_pkg}': {exc}"


def manage_service(action: str, service: str) -> str:
    """Manage systemd services (requires root)."""
    if not _is_root():
        return "Service management requires root privileges."

    valid_actions = ["start", "stop", "restart", "status", "enable", "disable"]
    if action not in valid_actions:
        return f"Action '{action}' is not valid. Available actions: {', '.join(valid_actions)}"

    try:
        if action == "status":
            result = subprocess.run(["systemctl", "status", service], capture_output=True, text=True)
        else:
            result = subprocess.run(["systemctl", action, service], capture_output=True, text=True, check=True)

        if action == "status":
            return f"Service '{service}' status:\n{result.stdout.strip()[:1000]}"
        return f"Service '{service}' {action}ed successfully."
    except subprocess.CalledProcessError as exc:
        return f"Failed to {action} service '{service}': {exc.stderr.strip() or exc.stdout.strip()}"
    except FileNotFoundError:
        return "systemctl is not available (not a systemd system)."
    except Exception as exc:
        return f"Unable to manage service '{service}': {exc}"


def set_hostname(new_hostname: str) -> str:
    """Change the system hostname (requires root)."""
    if not _is_root():
        return "Changing hostname requires root privileges."

    if not new_hostname or len(new_hostname) > 64:
        return "Invalid hostname (must be non-empty and under 64 characters)."

    try:
        subprocess.run(["hostnamectl", "set-hostname", new_hostname], check=True, capture_output=True, text=True)
        return f"Hostname changed to '{new_hostname}'. Reboot to apply fully."
    except subprocess.CalledProcessError as exc:
        return f"Failed to change hostname: {exc.stderr.strip() or exc.stdout.strip()}"
    except FileNotFoundError:
        return "hostnamectl is not available."
    except Exception as exc:
        return f"Unable to change hostname: {exc}"


def get_system_logs(lines: int = 20) -> str:
    """Show the latest system logs (root may be required for complete logs)."""
    try:
        result = subprocess.run(["journalctl", "-n", str(lines), "--no-pager"], capture_output=True, text=True, check=True)
        return f"Last {lines} system logs:\n{result.stdout.strip()}"
    except subprocess.CalledProcessError as exc:
        return f"Error accessing logs: {exc.stderr.strip() or exc.stdout.strip()}"
    except FileNotFoundError:
        return "journalctl is not available (not a systemd system)."
    except Exception as exc:
        return f"Unable to access logs: {exc}"


def open_firefox(search: Optional[str] = None) -> str:
    """Open Firefox or perform a search in the browser."""
    url = "https://www.google.com"
    if search:
        url = f"https://www.google.com/search?q={quote_plus(search)}"

    try:
        opened = webbrowser.open(url, new=2)
        if opened:
            if search:
                return f"Opening Firefox and searching: {search}"
            return "Opening Firefox."
    except Exception:
        pass

    try:
        if search:
            subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opening Firefox and searching: {search}"
        subprocess.Popen(["firefox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Opening Firefox."
    except FileNotFoundError:
        return "Firefox is not installed or not found in PATH."
    except Exception as exc:
        return f"Unable to open Firefox: {exc}"


def shell_exec(command: str, timeout: int = 30) -> str:
    """Execute a shell-like command — OFF by default.

    This is the single most dangerous tool in JARVIS: it lets whoever is
    chatting with the assistant (or a plugin, or a prompt-injected web
    page it summarized) run commands on your machine. It is disabled
    unless the person running JARVIS explicitly opts in.

    Even when enabled, it never uses shell=True: the command is tokenized
    with shlex and executed as an argv list, so shell metacharacters like
    `;`, `&&`, `|`, backticks or `$()` are NOT interpreted — they're just
    inert characters in an argument, which closes the classic injection
    vector. It can still run whatever single program you name, so this is
    risk reduction, not a sandbox — see the code interpreter's isolation
    notes for what real isolation looks like.
    """
    from config import get_config
    if not get_config().enable_shell_exec:
        return ("Shell execution is disabled. Set enable_shell_exec: true in "
                "jarvis_config.json (or JARVIS_ENABLE_SHELL_EXEC=true) to enable it "
                "— only do this if you understand it gives whoever talks to JARVIS "
                "the ability to run commands as you.")

    try:
        argv = shlex.split(command)
    except ValueError as e:
        return f"Could not parse command: {e}"
    if not argv:
        return "No command provided."

    try:
        result = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=timeout)
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output or "(no output)"
    except FileNotFoundError:
        return f"Command not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"


def system_command(query: str) -> Optional[str]:

    q = query.lower().strip()

    if any(phrase in q for phrase in ("che distro", "controlla distro", "mostra distro", "nome distro", "che sistema", "system info", "what distro")):
        return get_system_info()

    if any(phrase in q for phrase in ("ram", "memoria", "quanta ram", "memoria disponibile", "memoria libera", "controlla la mia ram", "controlla ram", "ram usage", "memory usage", "memory")):
        return get_ram_info()

    if any(phrase in q for phrase in ("aggiorna sistema", "aggiorna pacchetti", "installa aggiornamenti", "system update", "apt update", "pacman -syu", "update system")):
        return update_system()

    if any(phrase in q for phrase in ("spazio disco", "disco", "quanto spazio", "spazio disponibile", "df", "disk usage", "disk space", "disk")):
        return get_disk_usage()

    if any(phrase in q for phrase in ("uptime", "tempo di attività", "quanto tempo", "da quanto è acceso", "system uptime")):
        return get_uptime()

    if any(phrase in q for phrase in ("rete", "network", "ip", "interfacce", "connessioni", "network info")):
        return get_network_info()

    if any(phrase in q for phrase in ("processi", "ps", "cosa sta girando", "programmi attivi", "process list", "running processes")):
        return get_processes()

    if any(phrase in q for phrase in ("temperatura", "temperature", "caldo", "cpu temp", "sensors", "temperature info")):
        return get_temperature()

    if any(phrase in q for phrase in ("batteria", "battery", "carica", "quanta batteria", "battery info")):
        return get_battery_info()

    if "apri firefox" in q or "cerca su firefox" in q or "apri browser" in q or "open firefox" in q or "search firefox" in q:
        search = ""
        if "cerca" in q:
            words = q.split("cerca", 1)[1].strip()
            if words:
                search = words
        elif "search" in q:
            words = q.split("search", 1)[1].strip()
            if words:
                search = words
        return open_firefox(search or None)

    if q.startswith("firefox") and "cerca" in q:
        words = q.split("cerca", 1)[1].strip()
        return open_firefox(words or None)

    if q.startswith("open "):
        parts = q.split()
        if len(parts) >= 2:
            app = parts[1]
            try:
                subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Opened {app}."
            except FileNotFoundError:
                return f"{app} not found in PATH."
            except Exception as exc:
                return f"Unable to open {app}: {exc}"

    if q.startswith("apri "):
        app = q[5:].strip().split()[0]
        if app:
            try:
                subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Opened {app}."
            except FileNotFoundError:
                return f"{app} not found in PATH."
            except Exception as exc:
                return f"Unable to open {app}: {exc}"

    if q.startswith("$ ") or q.startswith("run "):
        cmd = query[1 if q.startswith("$") else 4:].strip()
        return shell_exec(cmd)

    if any(phrase in q for phrase in ("cpu", "processori", "quanti cpu", "cpu info", "numero cpu", "quante cpu", "logical cpu", "cpu count")):

        try:
            result = subprocess.run(["nproc"], capture_output=True, text=True, check=True)
            num_cpu = result.stdout.strip()
            return f"Logical CPU count: {num_cpu}"
        except subprocess.CalledProcessError:
            return "Unable to determine CPU count."
        except FileNotFoundError:
            return "The 'nproc' command is not available."

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
            import re
            match = re.search(r'(\d+)', q)
            if match:
                lines = min(int(match.group(1)), 100)
        return get_system_logs(lines)

    return None

    return None
