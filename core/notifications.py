"""
core/notifications.py — Notifiche desktop cross-platform.
Usa notify-send (Linux), AppleScript (macOS) o plyer come fallback.
"""
import shutil
import subprocess
import sys
from typing import Optional
from logger import debug, error


def _notify_linux(title: str, body: str, icon: str = "dialog-information") -> bool:
    if shutil.which("notify-send"):
        result = subprocess.run(
            ["notify-send", "-i", icon, title, body],
            capture_output=True, timeout=3
        )
        return result.returncode == 0
    return False


def _notify_macos(title: str, body: str) -> bool:
    script = f'display notification "{body}" with title "{title}"'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, timeout=3
    )
    return result.returncode == 0


def _notify_plyer(title: str, body: str) -> bool:
    try:
        from plyer import notification  # type: ignore
        notification.notify(title=title, message=body, app_name="JARVIS", timeout=5)
        return True
    except Exception:
        return False


def send_notification(title: str, body: str, level: str = "info") -> bool:
    """
    Invia una notifica desktop.

    Args:
        title: Titolo notifica
        body: Corpo del messaggio
        level: "info" | "warning" | "error"
    """
    icon_map = {
        "info":    "dialog-information",
        "warning": "dialog-warning",
        "error":   "dialog-error",
    }
    icon = icon_map.get(level, "dialog-information")

    debug(f"Notification [{level}]: {title} — {body}")

    if sys.platform == "linux":
        return _notify_linux(title, body, icon)
    elif sys.platform == "darwin":
        return _notify_macos(title, body)
    else:
        return _notify_plyer(title, body)


class NotificationManager:
    """
    Gestore notifiche con filtro per livello.
    Levels: "all" | "important" | "error"
    """

    def __init__(self, level: str = "important", enabled: bool = False):
        self.enabled = enabled
        self.level = level

    def notify(self, title: str, body: str, msg_level: str = "info") -> bool:
        if not self.enabled:
            return False

        # Filtra per livello
        levels = ["info", "important", "warning", "error"]
        filter_idx = levels.index(self.level) if self.level in levels else 0
        msg_idx = levels.index(msg_level) if msg_level in levels else 0

        if msg_idx < filter_idx:
            return False

        return send_notification(title, body, msg_level)

    def jarvis_reply(self, text: str):
        """Notifica una risposta importante di JARVIS."""
        preview = text[:100] + ("…" if len(text) > 100 else "")
        self.notify("JARVIS", preview, "info")

    def error_alert(self, text: str):
        """Notifica un errore."""
        self.notify("JARVIS — Errore", text, "error")


_notifier: Optional[NotificationManager] = None


def get_notifier() -> NotificationManager:
    global _notifier
    if _notifier is None:
        from config import get_config
        cfg = get_config()
        _notifier = NotificationManager(
            level=cfg.notification_level,
            enabled=cfg.enable_notifications,
        )
    return _notifier
