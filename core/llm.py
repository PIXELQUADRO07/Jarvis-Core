"""
core/llm.py — Streaming LLM with retry, circuit breaker, silent mode, and multi-language support.
"""
import json
import re
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
    """Generate the system prompt in the selected language with optional silent mode."""
    from core.i18n import get_language
    config = get_config()
    now    = datetime.now()
    lang   = get_language()

    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    weekdays_it = ['lunedì','martedì','mercoledì','giovedì','venerdì','sabato','domenica']
    weekdays_en = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    day_it = weekdays_it[now.weekday()]
    day_en = weekdays_en[now.weekday()]

    silent_instruction = (
        f"\n- IMPORTANTE: Rispondi in modo MOLTO CONCISO (massimo {config.silent_max_words} parole)."
        if config.silent_mode else ""
    )

    lang_prompts = {
        "it": (
            f"Ti chiami JARVIS, un assistente AI locale.\n"
            f"Oggi è {day_it} {date_str}, ore {time_str}.\n"
            "Regole:\n"
            "- Risposte accurate, concise (max 2-3 frasi di default).\n"
            "- Non rivelare dettagli tecnici sui modelli AI.\n"
            "- Tono professionale ma amichevole.\n"
            "- Ricorda il contesto dalla memoria."
            f"{silent_instruction}"
        ),
        "en": (
            f"Your name is JARVIS, a local AI assistant.\n"
            f"Today is {day_en} {date_str}, time {time_str}.\n"
            "Rules:\n"
            "- Accurate, concise answers (max 2-3 sentences by default).\n"
            "- Do not reveal technical AI model details.\n"
            "- Professional but friendly tone.\n"
            "- Remember context from memory."
            f"{silent_instruction}"
        ),
        "es": (
            f"Te llamas JARVIS, un asistente de IA local.\n"
            f"Hoy es {day_en} {date_str}, hora {time_str}.\n"
            "Reglas:\n"
            "- Respuestas precisas y concisas (máx. 2-3 frases).\n"
            "- No reveles detalles técnicos de modelos IA.\n"
            "- Tono profesional pero amigable."
            f"{silent_instruction}"
        ),
        "fr": (
            f"Tu t'appelles JARVIS, un assistant IA local.\n"
            f"Aujourd'hui c'est {day_en} {date_str}, heure {time_str}.\n"
            "Règles:\n"
            "- Réponses précises, concises (max 2-3 phrases).\n"
            "- Ne révèle pas les détails des modèles IA.\n"
            "- Ton professionnel mais amical."
            f"{silent_instruction}"
        ),
        "de": (
            f"Dein Name ist JARVIS, ein lokaler KI-Assistent.\n"
            f"Heute ist {day_en} {date_str}, Uhrzeit {time_str}.\n"
            "Regeln:\n"
            "- Genaue, prägnante Antworten (max. 2-3 Sätze).\n"
            "- Keine technischen KI-Modelldetails preisgeben.\n"
            "- Professioneller, freundlicher Ton."
            f"{silent_instruction}"
        ),
    }

    return {"role": "system", "content": lang_prompts.get(lang, lang_prompts["en"])}


def stream_llm(text: str) -> Generator[Tuple[str, dict], None, None]:
    """
    Stream LLM response.
    Yields (chunk_str, metadata_dict).
    """
    config  = get_config()
    history = load_memory()
    history.append({"role": "user", "content": text})

    prompt_tokens = TokenCounter.estimate_tokens(
        text + "".join(m.get("content", "") for m in history), config.model
    )

    payload = json.dumps({
        "model":   config.model,
        "messages":[get_system_prompt()] + history,
        "stream":  True,
        "options": {"temperature": config.temperature},
    }).encode("utf-8")

    req = urllib.request.Request(
        config.ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    full_reply = ""
    debug(f"LLM stream → {config.ollama_url} model={config.model}")

    try:
        resp = ollama_call(lambda: urllib.request.urlopen(req, timeout=config.request_timeout))

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

            # Response length limit
            if len(full_reply) + len(token) >= config.max_response_length:
                token = token[: config.max_response_length - len(full_reply)]
                full_reply += token
                if token:
                    ctkns = TokenCounter.estimate_tokens(full_reply, config.model)
                    yield token, {"prompt_tokens": prompt_tokens,
                                  "completion_tokens": ctkns,
                                  "total_tokens": prompt_tokens + ctkns}
                break

            full_reply += token
            ctkns = TokenCounter.estimate_tokens(full_reply, config.model)
            yield token, {"prompt_tokens": prompt_tokens,
                          "completion_tokens": ctkns,
                          "total_tokens": prompt_tokens + ctkns}

            if data.get("done"):
                debug(f"LLM done: {len(full_reply)} chars, ~{ctkns} tokens")
                break

    except CircuitBreakerOpen as e:
        error(f"Circuit breaker open: {e}")
        fallback = "⚠️ Ollama is temporarily offline. Please try again in a few seconds."
        ctkns = TokenCounter.estimate_tokens(fallback, config.model)
        yield fallback, {"prompt_tokens": prompt_tokens,
                         "completion_tokens": ctkns,
                         "total_tokens": prompt_tokens + ctkns,
                         "fallback": True}
        return

    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot reach Ollama: {e.reason}") from e
    except urllib.error.HTTPError as e:
        raise ConnectionError(f"Ollama HTTP {e.code}") from e
    except TimeoutError as e:
        raise TimeoutError("Timeout Ollama") from e
    except Exception as e:
        raise RuntimeError(str(e)) from e

    if full_reply:
        history.append({"role": "assistant", "content": full_reply})
        save_memory(history)
    else:
        warning("Empty LLM response")


def strip_markdown(text: str) -> str:
    """Remove Markdown markup for TTS (text-to-speech does not read formatting)."""
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text.strip()
