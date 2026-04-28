import json
from pathlib import Path
from typing import List, Dict

from config import get_config
from logger import debug, error


def load_memory() -> List[Dict]:
    """Carica cronologia conversazioni da file JSON"""
    config = get_config()
    mem_file = Path(config.memory_file)
    
    if not mem_file.exists():
        debug("Memory file not found, returning empty history")
        return []

    try:
        data = json.loads(mem_file.read_text())
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in memory file: {e}")
        return []
    except Exception as e:
        error(f"Error loading memory: {e}")
        return []

    # Filtro anti-spazzatura
    clean = []
    for msg in data:
        if not isinstance(msg, dict):
            continue
        
        content = msg.get("content", "")

        # Filtra messaggi con hallucinations comuni
        if any(x in content for x in ["BERT", "Transformer", "GPT", "qwen", "ollama"]):
            continue

        clean.append(msg)

    # Limita a max_history_messages
    if len(clean) > config.max_history_messages:
        debug(f"Trimming history from {len(clean)} to {config.max_history_messages}")
        clean = clean[-config.max_history_messages:]

    return clean


def save_memory(history: List[Dict]) -> bool:
    """Salva cronologia conversazioni in file JSON"""
    config = get_config()
    mem_file = Path(config.memory_file)
    
    clean = []

    for msg in history:
        if not isinstance(msg, dict):
            continue
            
        content = msg.get("content", "")

        # Filtro anti hallucination (coerente con load_memory)
        if any(x in content for x in ["BERT", "Transformer", "GPT", "qwen", "ollama"]):
            continue

        clean.append(msg)

    # Limita a max_history_messages
    if len(clean) > config.max_history_messages:
        clean = clean[-config.max_history_messages:]

    try:
        mem_file.write_text(json.dumps(clean, indent=2, ensure_ascii=False))
        debug(f"Memory saved: {len(clean)} messages")
        return True
    except Exception as e:
        error(f"Failed to save memory: {e}")
        return False


def clear_memory() -> bool:
    """Azzera completamente la memoria"""
    config = get_config()
    mem_file = Path(config.memory_file)
    try:
        mem_file.write_text(json.dumps([], indent=2))
        debug("Memory cleared")
        return True
    except Exception as e:
        error(f"Failed to clear memory: {e}")
        return False


def get_memory_stats() -> Dict:
    """Ritorna statistiche sulla memoria"""
    history = load_memory()
    user_msgs = [m for m in history if m.get("role") == "user"]
    assistant_msgs = [m for m in history if m.get("role") == "assistant"]
    
    total_chars = sum(len(m.get("content", "")) for m in history)
    
    return {
        "total_messages": len(history),
        "user_messages": len(user_msgs),
        "assistant_messages": len(assistant_msgs),
        "total_characters": total_chars,
        "avg_message_length": total_chars // len(history) if history else 0
    }
