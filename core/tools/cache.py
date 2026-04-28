import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

CACHE_PATH = Path(__file__).resolve().parent / "cache.json"
DEFAULT_TTL = 3600


def _load() -> dict:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get(key: str, ttl: Optional[int] = DEFAULT_TTL) -> Optional[Any]:
    data = _load()
    item = data.get(key)
    if not item:
        return None

    if ttl is None:
        return item.get("value")

    timestamp = item.get("ts")
    if timestamp is None:
        return item.get("value")

    try:
        created = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    if datetime.now(timezone.utc) - created > timedelta(seconds=ttl):
        return None

    return item.get("value")


def set_cache(key: str, value: Any) -> None:
    data = _load()
    data[key] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "value": value,
    }
    _save(data)
