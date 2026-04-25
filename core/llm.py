import json
import urllib.request
import urllib.error
from typing import Generator

from core.memory import load_memory, save_memory

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sei JARVIS, un assistente tecnico locale.\n"
        "Regole obbligatorie:\n"
        "- Risposte brevi e operative\n"
        "- Niente filosofia\n"
        "- Niente emozioni\n"
        "- Niente identità inventate (non sei BERT, GPT o altro)\n"
        "- Se non sai qualcosa, dillo chiaramente\n"
    )
}


def stream_llm(text: str) -> Generator[str, None, None]:
    history = load_memory()
    history.append({"role": "user", "content": text})

    payload = json.dumps({
        "model": MODEL,
        "messages": [SYSTEM_PROMPT] + history,
        "stream": True,
        "options": {"temperature": 0.2}
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    full_reply = ""

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue

                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue

                token = data.get("message", {}).get("content", "")
                if token:
                    full_reply += token
                    yield token

                if data.get("done"):
                    break

    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama non raggiungibile: {e.reason}") from e

    except TimeoutError:
        raise TimeoutError("Timeout Ollama")

    except Exception as e:
        raise RuntimeError(str(e)) from e

    if full_reply:
        history.append({"role": "assistant", "content": full_reply})
        save_memory(history)
