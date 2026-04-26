import requests
from urllib.parse import quote

from core.tools.cache import get as cache_get, set_cache
from core.tools.scraper import scrape_wikipedia_summary

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
    q = query.strip().lower()
    for prefix in NORMALIZE_PREFIXES:
        if q.startswith(prefix):
            q = q[len(prefix) :].strip(" ?")
            break
    return q.strip(" ?")


def wiki_search(query: str) -> str:
    query = _normalize_query(query)
    if not query:
        return "Nessuna info trovata."

    cache_key = f"wiki:{query}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    encoded = quote(query.replace(" ", "_"), safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    headers = {
        "User-Agent": "jarvis-bot/1.0 (mailto:jarvis@example.com)",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        extract = data.get("extract")
        if extract:
            set_cache(cache_key, extract)
            return extract
    except requests.RequestException:
        pass

    fallback = scrape_wikipedia_summary(query)
    if fallback:
        set_cache(cache_key, fallback)
        return fallback

    return "Nessuna info trovata da Wikipedia."
