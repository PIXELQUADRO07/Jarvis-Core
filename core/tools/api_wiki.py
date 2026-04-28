import requests
from urllib.parse import quote

from core.tools.cache import get as cache_get, set_cache
from core.tools.scraper import scrape_wikipedia_summary
from logger import debug, warning

NORMALIZE_PREFIXES = (
    "chi è",
    "chi e",
    "cos'è",
    "cos e",
    "cosa è",
    "cosa e",
    "spiega chi è",
    "spiega cos'è",
    "parlami di",
    "raccontami di",
)


def _normalize_query(query: str) -> str:
    """Normalizza la query rimuovendo prefissi comuni"""
    q = query.strip().lower()
    for prefix in NORMALIZE_PREFIXES:
        if q.startswith(prefix):
            q = q[len(prefix) :].strip(" ?")
            break
    return q.strip(" ?")


def wiki_search(query: str) -> str:
    """Cerca informazioni su Wikipedia"""
    query = _normalize_query(query)
    if not query:
        return "❌ Query non valida."

    cache_key = f"wiki:{query}"
    cached = cache_get(cache_key)
    if cached:
        debug(f"Wiki cache hit for {query}")
        return cached

    encoded = quote(query.replace(" ", "_"), safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    headers = {
        "User-Agent": "jarvis-bot/1.0 (mailto:jarvis@example.com)",
        "Accept": "application/json",
    }

    debug(f"Searching Wikipedia for: {query}")

    try:
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        extract = data.get("extract")
        if extract:
            set_cache(cache_key, extract)
            return extract
    except requests.exceptions.Timeout:
        warning(f"Wiki timeout for {query}")
    except requests.RequestException as e:
        warning(f"Wiki API error for {query}: {e}")

    # Fallback a scraping
    debug(f"Trying Wikipedia scraper for {query}")
    fallback = scrape_wikipedia_summary(query)
    if fallback:
        set_cache(cache_key, fallback)
        return fallback

    return f"❌ Nessuna info trovata su {query}. Prova con un altro termine."
