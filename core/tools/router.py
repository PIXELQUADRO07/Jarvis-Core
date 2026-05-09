"""
core/tools/router.py — Router query con supporto plugin, web search, e tutti i tool.
"""
import re
from typing import Optional
from logger import debug


def route_query(query: str) -> Optional[str]:
    """
    Routizza la query al tool o plugin appropriato.
    Priorità:
      1. Plugin esterni (auto-caricati)
      2. Comandi sistema
      3. Orario città
      4. Wikipedia
      5. URL scraping
      6. Calcoli matematici
      7. Meteo
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
            if "Risultato:" in result:
                return result

    # ── Meteo ────────────────────────────────────────────────────────────
    if config.enable_weather and any(
        kw in q for kw in ("meteo", "tempo", "previsione", "previsioni", "weather", "forecast")
    ):
        from core.tools.api_weather import get_weather
        city = "Napoli"
        match = re.search(r"(?:meteo|tempo|previsione[i]?)(?:\s+(?:a|di|in|per))?\s+(.+)", q)
        if match:
            candidate = match.group(1).strip(" ?!.,")
            if candidate and len(candidate) > 1:
                city = candidate
        result = get_weather(city)
        if result and "Impossibile" not in result:
            return result

    # ── Web search (ultimo fallback prima del LLM) ────────────────────────
    if config.enable_web_search:
        # Solo per query che sembrano richiedere informazioni esterne/recenti
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
