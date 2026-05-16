"""
core/tools/router.py — Query router with plugin, web search, and tool support.
"""
import re
from typing import Optional
from logger import debug


def route_query(query: str) -> Optional[str]:
    """
    Route the query to the appropriate tool or plugin.
    Priority:
      1. External plugins (auto-loaded)
      2. System commands
      3. City time
      4. Wikipedia
      5. URL scraping
      6. Math calculations
      7. Weather
      8. Web search (DuckDuckGo)
    """
    from config import get_config
    config = get_config()
    q = query.lower().strip()
    debug(f"Routing: {q[:60]}...")

    # ── Plugin ────────────────────────────────────────────────────────────
    if config.enable_plugins:
        try:
            from core.plugin_manager import get_plugin_manager
            result = get_plugin_manager().route(query)
            if result:
                return result
        except Exception:
            pass

    # ── Code Interpreter ──────────────────────────────────────────────────
    if "python" in q or "esegui" in q:
        from core.tools.code_interpreter import handle_code_query
        result = handle_code_query(query)
        if result:
            return result

    # ── Git ───────────────────────────────────────────────────────────────

    if "git" in q:
        from core.tools.git_tool import handle_git_query
        result = handle_git_query(query)
        if result:
            return result

    # ── PDF ───────────────────────────────────────────────────────────────
    if ".pdf" in q:
        # Look for a path ending in .pdf
        match = re.search(r'(/[^\s]+\.pdf)', query)
        if not match:
            match = re.search(r'([a-zA-Z0-9_\-./]+\.pdf)', query)

        if match:
            file_path = match.group(1)
            from core.tools.pdf_tool import extract_pdf_text
            # Simple check for page range in query
            pages = None
            page_match = re.search(r'pagine?\s+(\d+-\d+|\d+(?:,\d+)*)', q)
            if page_match:
                pages = page_match.group(1)
            return extract_pdf_text(file_path, pages=pages)

    # ── Sistema ───────────────────────────────────────────────────────────

    if config.enable_system:
        from core.tools.system import system_command
        result = system_command(query)
        if result:
            return result

    # ── Orario per città ──────────────────────────────────────────────────
    if "ore" in q and ("in" in q or "a" in q):
        match = re.search(r'(?:in|a)\s+(.+)', q, re.IGNORECASE)
        if match:
            from core.tools.api_weather import get_time
            city = match.group(1).strip(" ?")
            return get_time(city)

    # ── Wikipedia ─────────────────────────────────────────────────────────
    if config.enable_wiki:
        wiki_phrases = (
            "chi è", "chi e", "cos'è", "cos e", "cosa è", "cosa e",
            "chi ha", "chi era", "che ha", "spiega", "parlami di",
            "raccontami di", "informazioni su", "dimmi di",
            "definizione di", "chi è stato", "chi sono", "che cosa è",
        )
        if any(phrase in q for phrase in wiki_phrases):
            from core.tools.api_wiki import wiki_search
            return wiki_search(query)

    # ── URL scraping ──────────────────────────────────────────────────────
    if config.enable_scraper and (q.startswith("http://") or q.startswith("https://")):
        from core.security import validate_url
        if validate_url(query):
            from core.tools.scraper import scrape_title
            return scrape_title(query)

    # ── Calcoli ───────────────────────────────────────────────────────────
    if config.enable_math and re.search(r'\d', query) and re.search(r'[+\-*/^()]', query):
        math_expr = re.sub(r'[^\d\+\-\*/\^\(\)\.\s]', '', query).strip()
        if math_expr:
            from core.tools.math import calculate
            result = calculate(math_expr)
            if "Result:" in result:
                return result

    # ── Meteo ────────────────────────────────────────────────────────────
    if config.enable_weather and any(
        kw in q for kw in ("meteo", "tempo", "previsione", "previsioni", "weather", "forecast")
    ):
        from core.tools.api_weather import get_weather
        city = "London"
        match = re.search(r"(?:meteo|tempo|previsione[i]?|weather|forecast)(?:\s+(?:a|di|in|per|in))?\s+(.+)", q)
        if match:
            candidate = match.group(1).strip(" ?!.,")
            if candidate and len(candidate) > 1:
                city = candidate
        result = get_weather(city)
        if result and not result.startswith("❌"):
            return result

    # ── Web search (ultimo fallback prima del LLM) ────────────────────────
    if config.enable_web_search:
        # Only for queries that seem to require external or recent information
        web_triggers = (
            "cerca", "search", "trova", "notizie", "news", "ultime",
            "recenti", "oggi", "ieri", "questa settimana",
            "chi ha vinto", "risultato", "aggiornamento",
        )
        if any(kw in q for kw in web_triggers):
            from core.tools.web_search import search_web
            result = search_web(query)
            if result:
                return result

    return None
