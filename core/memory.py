import json
from pathlib import Path

MEM_FILE = Path("memory.json")


def load_memory():
    if not MEM_FILE.exists():
        return []

    try:
        data = json.loads(MEM_FILE.read_text())
    except Exception:
        return []

    # filtro base anti-spazzatura
    clean = []
    for msg in data:
        content = msg.get("content", "")

        if any(x in content for x in ["BERT", "Transformer", "GPT"]):
            continue

        clean.append(msg)

    return clean


def save_memory(history):
    clean = []

    for msg in history:
        content = msg.get("content", "")

        # filtro anti hallucination
        if any(x in content for x in ["BERT", "Transformer"]):
            continue

        clean.append(msg)

    MEM_FILE.write_text(json.dumps(clean, indent=2))
