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

    When config.use_native_tool_calling is on, the model is given the
    registered tool schemas (core/tools/registry.py) and can request tool
    calls instead of answering directly. We execute those, feed the
    results back, and let the model continue — up to
    config.max_tool_call_rounds round trips — before streaming its final,
    human-readable answer. Intermediate tool-call plumbing is not saved
    to long-term memory; only the final Q&A pair is.
    """
    config  = get_config()
    history = load_memory()
    history.append({"role": "user", "content": text})

    prompt_tokens = TokenCounter.estimate_tokens(
        text + "".join(m.get("content", "") for m in history), config.model
    )

    tools = None
    if config.use_native_tool_calling:
        try:
            from core.tools.registry import get_enabled_tools
            tools = get_enabled_tools(config) or None
        except Exception as e:
            warning(f"Tool registry unavailable, continuing without tools: {e}")

    messages = [get_system_prompt()] + history
    full_reply = ""
    tool_round = 0
    debug(f"LLM stream → {config.ollama_url} model={config.model} tools={'on' if tools else 'off'}")

    try:
        while True:
            payload_dict = {
                "model":   config.model,
                "messages": messages,
                "stream":  True,
                "options": {"temperature": config.temperature},
            }
            if tools:
                payload_dict["tools"] = tools

            payload = json.dumps(payload_dict).encode("utf-8")
            req = urllib.request.Request(
                config.ollama_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                resp = ollama_call(lambda: urllib.request.urlopen(req, timeout=config.request_timeout))
            except urllib.error.HTTPError as e:
                # Some Ollama versions / models reject an unknown `tools`
                # field outright. Degrade to a normal, tool-less request
                # once instead of failing the whole conversation.
                if tools and e.code == 400:
                    warning("Ollama rejected 'tools' (model/server may not support it) — retrying without tools")
                    tools = None
                    continue
                raise

            pending_tool_calls = []
            ctkns = TokenCounter.estimate_tokens(full_reply, config.model)

            for raw_line in resp:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue

                message = data.get("message", {})
                token = message.get("content", "") or ""
                if message.get("tool_calls"):
                    pending_tool_calls.extend(message["tool_calls"])

                if token:
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
                    debug(f"LLM round done: {len(full_reply)} chars, ~{ctkns} tokens, "
                          f"tool_calls={len(pending_tool_calls)}")
                    break

            if pending_tool_calls and tool_round < config.max_tool_call_rounds:
                tool_round += 1
                from core.tools.registry import execute_tool_call
                messages.append({"role": "assistant", "content": "", "tool_calls": pending_tool_calls})
                for call in pending_tool_calls:
                    fn = call.get("function", {})
                    name = fn.get("name", "")
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    result = execute_tool_call(name, args, config)
                    messages.append({"role": "tool", "content": result, "name": name})
                continue  # ask the model to continue with the tool results

            if pending_tool_calls and tool_round >= config.max_tool_call_rounds:
                warning(f"Hit max_tool_call_rounds ({config.max_tool_call_rounds}) — stopping tool loop")
                if not full_reply:
                    fallback = "I wasn't able to finish that after several tool calls — could you rephrase?"
                    ctkns = TokenCounter.estimate_tokens(fallback, config.model)
                    yield fallback, {"prompt_tokens": prompt_tokens, "completion_tokens": ctkns,
                                      "total_tokens": prompt_tokens + ctkns}

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
