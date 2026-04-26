import json
import urllib.request
import urllib.error
from typing import Generator
from datetime import datetime

from core.memory import load_memory, save_memory

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"


def get_system_prompt() -> dict:
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    weekdays = ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato', 'domenica']
    day_str = weekdays[now.weekday()]
    content = (
        f"Sei JARVIS, un assistente AI avanzato e affidabile.\n"
        f"Oggi è {day_str} {date_str}, ora attuale {time_str}.\n"
        "Istruzioni:\n"
        "- Fornisci risposte accurate, concise e utili.\n"
        "- Usa gli strumenti disponibili quando necessario (meteo, Wikipedia, calcoli matematici, ecc.).\n"
        "- Se una domanda richiede calcolo, usa lo strumento matematico.\n"
        "- Per informazioni generali, consulta Wikipedia.\n"
        "- Non inventare informazioni; se non sai, dì 'Non lo so'.\n"
        "- Non menzionare modelli AI, tecnologie come BERT, Transformer, GPT, o dettagli tecnici sui modelli.\n"
        "- Mantieni un tono professionale ma amichevole.\n"
        "- Ricorda il contesto della conversazione dalla memoria.\n"
    )
    return {
        "role": "system",
        "content": content
    }


def stream_llm(text: str) -> Generator[str, None, None]:
    history = load_memory()
    history.append({"role": "user", "content": text})

    payload = json.dumps({
        "model": MODEL,
        "messages": [get_system_prompt()] + history,
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
