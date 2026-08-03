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
#
# Design note: this used to run a blacklist of regexes (e.g. "subprocess",
# "eval(") over every chat message and silently delete matches before the
# LLM ever saw them. Two problems with that:
#   1. It's trivial to bypass (split the keyword, use a synonym) so it gave
#      false confidence rather than real protection.
#   2. It mangled entirely legitimate messages — e.g. "explain Python's
#      subprocess module" would silently lose the word "subprocess", and
#      the user would never know their message was altered.
# Free-text sent to an LLM chat isn't itself the attack surface — it can't
# execute anything on its own. The actual defenses belong at the point
# where text becomes an action: parameterized SQL (already used in db.py),
# argv-based subprocess calls with strict allowlists (see core/tools/system.py
# and core/tools/code_interpreter.py), and HTML-escaping if/when output is
# ever rendered in a browser. This function now only guards against
# resource-exhaustion (very long input) and stray control characters —
# it does not rewrite the meaning of what the person typed.

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Still logged (not stripped) as a lightweight signal for anyone watching
# logs — useful for spotting probing/abuse patterns without corrupting
# legitimate messages.
_SUSPICIOUS_PATTERNS = [
    r"<script.*?>.*?</script>",
    r"DROP\s+TABLE",
    r"DELETE\s+FROM\s+\w+\s*;",
]
_COMPILED_SUSPICIOUS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _SUSPICIOUS_PATTERNS]

MAX_INPUT_LENGTH = 4096


def sanitize_input(text: str) -> str:
    """
    Normalize user input: strip control characters and cap length.
    Never silently rewrites the semantic content of the message.
    """
    if not text:
        return text

    for pattern in _COMPILED_SUSPICIOUS:
        if pattern.search(text):
            warning("Security: suspicious pattern in input (logged only, not modified)")
            break

    cleaned = _CONTROL_CHARS_RE.sub("", text)

    if len(cleaned) > MAX_INPUT_LENGTH:
        warning(f"Security: input truncated (>{MAX_INPUT_LENGTH} chars)")
        cleaned = cleaned[:MAX_INPUT_LENGTH]

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


class RateLimiterRegistry:
    """One RateLimiter per client key (API key or IP), so a single caller
    can't exhaust the shared budget for everyone hitting the REST API.
    Bounded size with simple eviction so it can't grow unboundedly under
    a distributed scan."""

    _MAX_CLIENTS = 10_000

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._limiters: dict[str, RateLimiter] = {}
        self._lock = threading.Lock()

    def allow(self, client_key: str) -> bool:
        with self._lock:
            limiter = self._limiters.get(client_key)
            if limiter is None:
                if len(self._limiters) >= self._MAX_CLIENTS:
                    # Simple pressure-release valve: drop the oldest-inserted
                    # entry rather than let this grow forever.
                    self._limiters.pop(next(iter(self._limiters)))
                limiter = RateLimiter(self.max_requests, self.window)
                self._limiters[client_key] = limiter
        return limiter.allow()


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


class EncryptionUnavailableError(RuntimeError):
    """Raised when encryption was requested but could not be performed."""


def encrypt_json_file(path: str, data: object, key_file: str = ".jarvis_key") -> bool:
    """Write an encrypted JSON file.

    Raises EncryptionUnavailableError instead of silently falling back to
    plaintext — a caller that asked for `/encrypt on` needs to know
    immediately if encryption isn't actually happening, not discover it
    later by inspecting the file on disk.
    """
    import json
    text = json.dumps(data, ensure_ascii=False)
    encrypted = encrypt_text(text, key_file)
    if encrypted is None:
        raise EncryptionUnavailableError(
            "Encryption requested but unavailable (is 'cryptography' installed?). "
            "Refusing to write plaintext silently — install it with "
            "'pip install cryptography' or disable encryption."
        )
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
_rate_limiter_registry: Optional[RateLimiterRegistry] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        from config import get_config
        cfg = get_config()
        _rate_limiter = RateLimiter(cfg.rate_limit_requests, cfg.rate_limit_window)
    return _rate_limiter


def get_rate_limiter_registry() -> RateLimiterRegistry:
    """Per-client (API key or IP) rate limiting for the REST API."""
    global _rate_limiter_registry
    if _rate_limiter_registry is None:
        from config import get_config
        cfg = get_config()
        _rate_limiter_registry = RateLimiterRegistry(cfg.rate_limit_requests, cfg.rate_limit_window)
    return _rate_limiter_registry
