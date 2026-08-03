"""
core/tools/registry.py — Native tool-calling registry for Ollama.

Replaces keyword/regex routing (core/tools/router.py) as the *primary*
mechanism when the model supports tool calls: instead of JARVIS guessing
what a message means from substrings ("meteo", "cerca", ".pdf"...), the
LLM itself decides — from the conversation — whether a tool is needed,
which one, and with what arguments. This fixes the classic false-positive/
false-negative failures of keyword routing (e.g. "quanto fa 2+2 a Londra"
being misrouted) because the model reasons over the whole query instead
of pattern-matching fragments of it.

Security note (deliberate): only read-only, side-effect-free tools are
registered here. `install_package`, `remove_package`, and `shell_exec`
are intentionally NEVER exposed to the model as callable tools — those
stay behind the explicit human opt-in flags in config.py and are not
things an LLM should be able to decide to invoke on its own. If you add
a tool here, ask whether a model hallucinating a bad call to it could
hurt the user; if yes, it probably belongs in router.py (or nowhere)
instead of here.

Each entry pairs an Ollama/OpenAI-style function schema with the Python
callable it dispatches to. Ollama's /api/chat `tools` parameter uses
this exact schema shape.
"""
from typing import Any, Callable, Dict, List, Optional

from logger import debug, warning


def _tool_weather(city: str) -> str:
    from core.tools.api_weather import get_weather
    return get_weather(city)


def _tool_time(city: str) -> str:
    from core.tools.api_weather import get_time
    return get_time(city)


def _tool_wiki(query: str) -> str:
    from core.tools.api_wiki import wiki_search
    return wiki_search(query)


def _tool_math(expression: str) -> str:
    from core.tools.math import calculate
    return calculate(expression)


def _tool_web_search(query: str) -> str:
    from core.tools.web_search import search_web
    result = search_web(query)
    return result or "No results found."


def _tool_pdf_extract(file_path: str, pages: Optional[str] = None) -> str:
    from core.tools.pdf_tool import extract_pdf_text
    return extract_pdf_text(file_path, pages=pages)


def _tool_system_info(info_type: str) -> str:
    """Read-only system info only — never routes to install/remove/shell_exec."""
    from core.tools import system as sysm
    dispatch = {
        "distro": sysm.get_system_info,
        "ram": sysm.get_ram_info,
        "disk": sysm.get_disk_usage,
        "uptime": sysm.get_uptime,
        "network": sysm.get_network_info,
        "processes": sysm.get_processes,
        "temperature": sysm.get_temperature,
        "battery": sysm.get_battery_info,
    }
    fn = dispatch.get(info_type)
    if fn is None:
        return f"Unknown info_type '{info_type}'. Valid: {', '.join(dispatch)}"
    return fn()


# ── Schema + dispatch table ──────────────────────────────────────────────────
# `enabled_when` names the matching config.enable_* flag, so a tool that's
# turned off in config is also invisible to the model, not just to the
# keyword router.

_REGISTRY: List[Dict[str, Any]] = [
    {
        "enabled_when": "enable_weather",
        "callable": _tool_weather,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather forecast for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name, e.g. 'Naples' or 'Milan'."},
                    },
                    "required": ["city"],
                },
            },
        },
    },
    {
        "enabled_when": "enable_weather",
        "callable": _tool_time,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Get the current local time in a given city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name."},
                    },
                    "required": ["city"],
                },
            },
        },
    },
    {
        "enabled_when": "enable_wiki",
        "callable": _tool_wiki,
        "schema": {
            "type": "function",
            "function": {
                "name": "wiki_search",
                "description": "Look up a factual/encyclopedic summary of a topic, person, or thing on Wikipedia.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Topic to look up."},
                    },
                    "required": ["query"],
                },
            },
        },
    },
    {
        "enabled_when": "enable_math",
        "callable": _tool_math,
        "schema": {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Evaluate a mathematical expression (arithmetic, powers, parentheses).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "e.g. '(3 + 4) * 2 ^ 3'."},
                    },
                    "required": ["expression"],
                },
            },
        },
    },
    {
        "enabled_when": "enable_web_search",
        "callable": _tool_web_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for current information (news, recent events, anything outside the model's training data).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                    },
                    "required": ["query"],
                },
            },
        },
    },
    {
        "enabled_when": "enable_scraper",  # gated the same as URL scraping generally
        "callable": _tool_pdf_extract,
        "schema": {
            "type": "function",
            "function": {
                "name": "extract_pdf_text",
                "description": "Extract text content from a local PDF file the user referenced by path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the .pdf file."},
                        "pages": {"type": "string", "description": "Optional page range, e.g. '1-3' or '1,4,7'."},
                    },
                    "required": ["file_path"],
                },
            },
        },
    },
    {
        "enabled_when": "enable_system",
        "callable": _tool_system_info,
        "schema": {
            "type": "function",
            "function": {
                "name": "system_info",
                "description": "Get read-only information about the local machine (RAM, disk, uptime, network, processes, temperature, battery, distro).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "info_type": {
                            "type": "string",
                            "enum": ["distro", "ram", "disk", "uptime", "network", "processes", "temperature", "battery"],
                        },
                    },
                    "required": ["info_type"],
                },
            },
        },
    },
]


def get_enabled_tools(config) -> List[Dict[str, Any]]:
    """Ollama-format tool schema list for the tools currently enabled in config."""
    return [
        entry["schema"] for entry in _REGISTRY
        if getattr(config, entry["enabled_when"], False)
    ]


def get_dispatch_map(config) -> Dict[str, Callable[..., str]]:
    """name -> callable, restricted to what's enabled — a tool_call for a
    disabled/unknown tool is refused, not attempted."""
    return {
        entry["schema"]["function"]["name"]: entry["callable"]
        for entry in _REGISTRY
        if getattr(config, entry["enabled_when"], False)
    }


def execute_tool_call(name: str, arguments: Dict[str, Any], config) -> str:
    """Run one tool call requested by the model, defensively."""
    dispatch = get_dispatch_map(config)
    fn = dispatch.get(name)
    if fn is None:
        warning(f"Model requested unknown/disabled tool: {name}")
        return f"Error: tool '{name}' is not available."
    try:
        debug(f"Tool call: {name}({arguments})")
        return str(fn(**arguments))
    except TypeError as e:
        warning(f"Tool call '{name}' got bad arguments {arguments}: {e}")
        return f"Error: invalid arguments for '{name}': {e}"
    except Exception as e:
        warning(f"Tool call '{name}' raised: {e}")
        return f"Error running '{name}': {e}"
