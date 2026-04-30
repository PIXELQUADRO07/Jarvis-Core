import json
import urllib.request
import urllib.error
from typing import Generator, Tuple
from datetime import datetime

from core.memory import load_memory, save_memory
from core.token_counter import TokenCounter
from core.retry_handler import ollama_call, CircuitBreakerOpen
from config import get_config
from logger import debug, error, warning


def get_system_prompt() -> dict:
    """Genera il system prompt con info temporali aggiornate"""
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    weekdays = ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato', 'domenica']
    day_str = weekdays[now.weekday()]
    content = (
        f"Ti chiami JARVIS, un assistente AI avanzato e affidabile.\n"
        f"Oggi è {day_str} {date_str}, ora attuale {time_str}.\n"
        "Istruzioni:\n"
        "- Fornisci risposte accurate, concise e utili.\n"
        "- IMPORTANTE: Mantieni le risposte BREVI e CONCISE (max 2-3 frasi).\n"
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


def stream_llm(text: str) -> Generator[Tuple[str, dict], None, None]:
    """
    Esegue streaming della risposta LLM da Ollama.
    Carica storia conversazione, invia richiesta, e yield token per token con metadati.
    
    Yields:
        Tuple[str, dict]: (token_text, metadata) dove metadata include token usage
    """
    config = get_config()
    history = load_memory()
    history.append({"role": "user", "content": text})
    
    # Calcola token del prompt
    prompt_tokens = TokenCounter.estimate_tokens(
        text + "".join(msg.get("content", "") for msg in history),
        config.model
    )

    payload = json.dumps({
        "model": config.model,
        "messages": [get_system_prompt()] + history,
        "stream": True,
        "options": {"temperature": config.temperature}
    }).encode("utf-8")

    req = urllib.request.Request(
        config.ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    full_reply = ""
    debug(f"Streaming LLM request to {config.ollama_url} with model {config.model}")

    try:
        # Wrapper function for circuit breaker protection
        def make_request():
            return urllib.request.urlopen(req, timeout=config.request_timeout)
        
        resp = ollama_call(make_request)
        
        for raw_line in resp:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            token = data.get("message", {}).get("content", "")
            if not token:
                continue

            if len(full_reply) + len(token) >= config.max_response_length:
                token = token[:config.max_response_length - len(full_reply)]
                full_reply += token
                if token:
                    completion_tokens = TokenCounter.estimate_tokens(full_reply, config.model)
                    metadata = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                    yield (token, metadata)
                debug(f"Response length limit reached: {len(full_reply)} chars")
                break

            full_reply += token
            completion_tokens = TokenCounter.estimate_tokens(full_reply, config.model)
            metadata = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            yield (token, metadata)

            if data.get("done"):
                debug(f"LLM streaming complete: {len(full_reply)} chars, ~{completion_tokens} tokens")
                break
    
    except CircuitBreakerOpen as e:
        error(f"Circuit breaker open: {e}")
        fallback = "⚠️ Ollama è temporaneamente offline. Riprova tra pochi secondi."
        completion_tokens = TokenCounter.estimate_tokens(fallback, config.model)
        metadata = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "fallback": True
        }
        yield (fallback, metadata)

    except urllib.error.URLError as e:
        error(f"Ollama connection error: {e.reason}")
        raise ConnectionError(f"Ollama non raggiungibile: {e.reason}") from e

    except urllib.error.HTTPError as e:
        error(f"Ollama HTTP error: {e.code}")
        raise ConnectionError(f"Ollama error: HTTP {e.code}") from e

    except TimeoutError as e:
        error("Ollama timeout")
        raise TimeoutError("Timeout Ollama") from e

    except Exception as e:
        error(f"Unexpected error in stream_llm: {e}")
        raise RuntimeError(str(e)) from e

    if full_reply:
        history.append({"role": "assistant", "content": full_reply})
        save_memory(history)
    else:
        warning("Empty response received from LLM")
