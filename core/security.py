"""
core/security.py — Security: AES memory encryption, input validation, rate limiting.
"""
import re
import time
import threading
from collections import deque
from pathlib import Path
from typing import Optional
from logger import debug, warning


# ── Input Sanitization ───────────────────────────────────────────────────────

# Dangerous patterns to block
_INJECTION_PATTERNS = [
    r"<script.*?>.*?</script>",
    r"javascript:",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"subprocess",
    r"os\.system",
    r"DROP\s+TABLE",
    r"DELETE\s+FROM",
    r"INSERT\s+INTO.*?--",
]
_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PATTERNS]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing dangerous patterns.
    Does not block text — it cleans and warns.
    """
    if not text:
        return text

    cleaned = text
    for pattern in _COMPILED:
        if pattern.search(cleaned):
            warning(f"Security: injection pattern detected and removed")
            cleaned = pattern.sub("", cleaned)

    # Limit maximum input length to prevent DoS
    if len(cleaned) > 4096:
        warning("Security: input truncated (>4096 chars)")
        cleaned = cleaned[:4096]

    return cleaned.strip()


def validate_url(url: str) -> bool:
    """Verify the URL is safe (no file://, no localhost for external calls)."""
    url = url.lower().strip()
    if url.startswith("file://"):
        return False
    return url.startswith("http://") or url.startswith("https://")


# ── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding window rate limiter thread-safe.
    Default: 60 requests / 60 seconds.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._timestamps: deque = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Return True if the request is allowed, False if the rate limit is exceeded."""
        now = time.monotonic()
        with self._lock:
            # Rimuovi timestamp fuori finestra
            while self._timestamps and now - self._timestamps[0] > self.window:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_requests:
                warning(f"RateLimit: {self.max_requests} requests/{self.window}s exceeded")
                return False

            self._timestamps.append(now)
            return True

    def wait_time(self) -> float:
        """Secondi da aspettare prima della prossima richiesta permessa."""
        now = time.monotonic()
        with self._lock:
            if not self._timestamps:
                return 0.0
            oldest = self._timestamps[0]
            elapsed = now - oldest
            if elapsed >= self.window:
                return 0.0
            return self.window - elapsed


# ── AES Memory Encryption ────────────────────────────────────────────────────

def _load_or_create_key(key_file: str) -> bytes:
    """Load or generate an AES-256 key."""
    path = Path(key_file)
    if path.exists():
        return path.read_bytes()
    try:
        from cryptography.fernet import Fernet  # type: ignore
        key = Fernet.generate_key()
        path.write_bytes(key)
        path.chmod(0o600)
        debug(f"Generated new encryption key: {key_file}")
        return key
    except ImportError:
        warning("cryptography not installed — encryption disabled")
        return b""


def encrypt_text(text: str, key_file: str = ".jarvis_key") -> Optional[bytes]:
    """Encrypt text with AES (Fernet). Returns None if crypto is unavailable."""
    try:
        from cryptography.fernet import Fernet  # type: ignore
        key = _load_or_create_key(key_file)
        if not key:
            return None
        f = Fernet(key)
        return f.encrypt(text.encode("utf-8"))
    except Exception as e:
        warning(f"Encryption failed: {e}")
        return None


def decrypt_text(data: bytes, key_file: str = ".jarvis_key") -> Optional[str]:
    """Decrypt AES text. Returns None on error."""
    try:
        from cryptography.fernet import Fernet  # type: ignore
        key = _load_or_create_key(key_file)
        if not key:
            return None
        f = Fernet(key)
        return f.decrypt(data).decode("utf-8")
    except Exception as e:
        warning(f"Decryption failed: {e}")
        return None


def encrypt_json_file(path: str, data: object, key_file: str = ".jarvis_key") -> bool:
    """Scrive un file JSON cifrato."""
    import json
    text = json.dumps(data, ensure_ascii=False)
    encrypted = encrypt_text(text, key_file)
    if encrypted is None:
        # Fallback non cifrato
        Path(path).write_text(text, encoding="utf-8")
        return True
    Path(path + ".enc").write_bytes(encrypted)
    return True


def decrypt_json_file(path: str, key_file: str = ".jarvis_key") -> Optional[object]:
    """Legge un file JSON cifrato (o non cifrato come fallback)."""
    import json
    enc_path = Path(path + ".enc")
    plain_path = Path(path)
    if enc_path.exists():
        text = decrypt_text(enc_path.read_bytes(), key_file)
        if text:
            return json.loads(text)
    if plain_path.exists():
        return json.loads(plain_path.read_text(encoding="utf-8"))
    return None


# ── Singleton rate limiter ───────────────────────────────────────────────────
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        from config import get_config
        cfg = get_config()
        _rate_limiter = RateLimiter(cfg.rate_limit_requests, cfg.rate_limit_window)
    return _rate_limiter
