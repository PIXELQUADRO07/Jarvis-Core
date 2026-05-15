"""
core/memory.py — Conversation memory with SQLite persistence and optional encryption.
"""
import json
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

    # Save to DB
    try:
        db = get_db()
        # The DB accumulates data — save only the last assistant message to avoid duplication
        if clean and clean[-1]["role"] == "assistant":
            last = clean[-1]
            db.save_message(
                session=session_name,
                role=last["role"],
                content=last["content"],
                model=config.model,
                language=config.language,
            )
        session_mgr.update_session_stats(len(clean))
        debug(f"Memory saved to DB: {len(clean)} msgs (session={session_name})")
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
    """Clear the current session memory."""
    session_mgr = get_session_manager()
    mem_file = Path(session_mgr.get_session_file())
    try:
        mem_file.write_text(json.dumps([], indent=2), encoding="utf-8")
        debug("Memory cleared")
        return True
    except Exception as e:
        error(f"Clear memory failed: {e}")
        return False


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
    BAD = {"BERT", "Transformer", "GPT", "qwen", "ollama"}
    return [
        m for m in messages
        if isinstance(m, dict) and not any(x in m.get("content", "") for x in BAD)
    ]


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
