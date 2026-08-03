"""
core/memory.py — Conversation memory with SQLite persistence and optional encryption.
"""
import json
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from config import get_config
from core.session_manager import get_session_manager
from core.db import get_db
from logger import debug, error


def load_memory() -> List[Dict]:
    """Load the current session history from DB or fallback to JSON file."""
    config = get_config()
    session_mgr = get_session_manager()
    session_name = session_mgr.current_session.name if session_mgr.current_session else "default"

    # Prima prova DB (persistenza completa)
    try:
        db = get_db()
        messages = db.load_session(session_name, limit=config.max_history_messages)
        if messages:
            debug(f"Memory loaded from DB: {len(messages)} msgs (session={session_name})")
            return _filter_hallucinations(messages)
    except Exception as e:
        error(f"DB load failed, falling back to file: {e}")

    # Fallback su file JSON
    mem_file = Path(session_mgr.get_session_file())
    if not mem_file.exists():
        return []
    try:
        data = json.loads(mem_file.read_text(encoding="utf-8"))
        messages = data if isinstance(data, list) else data.get("messages", [])
    except Exception as e:
        error(f"Memory file load error: {e}")
        return []

    messages = _filter_hallucinations(messages)
    if len(messages) > config.max_history_messages:
        messages = messages[-config.max_history_messages:]
    return messages


def save_memory(history: List[Dict]) -> bool:
    """Save history to the DB and fallback to JSON file if needed."""
    config = get_config()
    session_mgr = get_session_manager()
    session_name = session_mgr.current_session.name if session_mgr.current_session else "default"

    clean = _filter_hallucinations(history)
    if len(clean) > config.max_history_messages:
        clean = clean[-config.max_history_messages:]

    # Save to DB — both turns, not just the assistant reply, so
    # /history, /search, and session reload from DB aren't missing half
    # the conversation. Only persist messages not already in the DB: we
    # track how many we've saved for this session and only insert the
    # tail that's new since the last save.
    try:
        db = get_db()
        already_saved = session_mgr.current_session.message_count if session_mgr.current_session else 0
        new_messages = clean[already_saved:] if already_saved < len(clean) else clean[-2:]
        for m in new_messages:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                db.save_message(
                    session=session_name,
                    role=m["role"],
                    content=m["content"],
                    model=config.model,
                    language=config.language,
                )
        session_mgr.update_session_stats(len(clean))
        debug(f"Memory saved to DB: {len(new_messages)} new msgs (session={session_name})")
    except Exception as e:
        error(f"DB save failed: {e}")

    # Also save to JSON file for compatibility
    mem_file = Path(session_mgr.get_session_file())
    try:
        # Optional encryption
        if config.encrypt_memory:
            from core.security import encrypt_json_file
            encrypt_json_file(str(mem_file), clean, config.encryption_key_file)
        else:
            mem_file.write_text(
                json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        return True
    except Exception as e:
        error(f"Memory file save failed: {e}")
        return False


def clear_memory() -> bool:
    """Clear the current session memory (both the JSON file and the DB —
    load_memory() checks the DB first, so clearing only the file left
    old messages resurfacing on the next load)."""
    session_mgr = get_session_manager()
    session_name = session_mgr.current_session.name if session_mgr.current_session else "default"
    mem_file = Path(session_mgr.get_session_file())
    ok = True
    try:
        mem_file.write_text(json.dumps([], indent=2), encoding="utf-8")
    except Exception as e:
        error(f"Clear memory (file) failed: {e}")
        ok = False
    try:
        db = get_db()
        db.clear_session(session_name)
        session_mgr.update_session_stats(0)
    except Exception as e:
        error(f"Clear memory (DB) failed: {e}")
        ok = False
    if ok:
        debug("Memory cleared (file + DB)")
    return ok


def get_memory_stats() -> Dict:
    """Get statistics for the current session memory."""
    history = load_memory()
    user_msgs      = [m for m in history if m.get("role") == "user"]
    assistant_msgs = [m for m in history if m.get("role") == "assistant"]
    total_chars    = sum(len(m.get("content", "")) for m in history)
    return {
        "total_messages":    len(history),
        "user_messages":     len(user_msgs),
        "assistant_messages":len(assistant_msgs),
        "total_characters":  total_chars,
        "avg_message_length":total_chars // len(history) if history else 0,
    }


def _filter_hallucinations(messages: List[Dict]) -> List[Dict]:
    """Drop known hallucinated boilerplate the model sometimes emits
    (self-identification as BERT/GPT/etc. instead of answering).

    The previous version deleted ANY message merely *containing* the
    substrings "BERT", "GPT", "qwen", "ollama" — which silently wiped
    out entirely legitimate messages like "what's the difference between
    GPT and BERT?" or "which Ollama model are you using?". This now only
    drops assistant messages that are hallucinated self-identification
    (short, and essentially just naming a model), never user messages
    and never substantive answers that happen to mention these terms.
    """
    _SELF_ID_RE = re.compile(
        r"^\s*i\s*('m|am)\s*(a\s*)?(bert|gpt(-?\d)?|transformer)\b.{0,40}$",
        re.IGNORECASE,
    )
    cleaned = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        content = m.get("content", "")
        if m.get("role") == "assistant" and len(content) < 120 and _SELF_ID_RE.match(content):
            debug(f"Filtered hallucinated self-identification: {content[:60]!r}")
            continue
        cleaned.append(m)
    return cleaned


def auto_cleanup_old_messages():
    """Remove messages older than max_history_days from the DB."""
    config = get_config()
    try:
        db = get_db()
        deleted = db.cleanup_old_messages(days=config.memory_cleanup_days)
        if deleted:
            debug(f"Auto-cleanup: removed {deleted} old messages")
    except Exception as e:
        error(f"Auto-cleanup failed: {e}")
