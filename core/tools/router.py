import re

from core.tools.api_wiki import wiki_search
from core.tools.api_weather import get_weather, get_time
from core.tools.scraper import scrape_title
from core.tools.system import system_command
from core.tools.math import calculate
from logger import debug


def route_query(query: str):
    """
    Routizza la query al tool appropriato.
    Priorità:
    1. Comandi sistema (distro, RAM, CPU)
    2. Query temporali
    3. Query Wikipedia
    4. Calcoli matematici
    5. URL scraping
    6. Query meteo
    """
    q = query.lower().strip()
    debug(f"Routing query: {q[:50]}...")

    # ─── Sistema (priorità alta) ─────────────────────────────────────────
    system_result = system_command(query)
    if system_result:
        return system_result

    # ─── Query temporali ────────────────────────────────────────────────
    if "ore" in q and ("in" in q or "a" in q):
        match = re.search(r'(?:in|a)\s+(.+)', q, re.IGNORECASE)
        if match:
            city = match.group(1).strip(" ?")
            return get_time(city)

    # ─── Query Wikipedia (priorità media-alta) ──────────────────────────
    wiki_phrases = (
        "chi è", "chi e", "cos'è", "cos e", "cosa è", "cosa e", 
        "chi ha", "chi era", "che ha", "che ha creato", "che ha inventato", 
        "spiega", "parlami di", "raccontami di", "informazioni su", 
        "dimmi di", "definizione di", "chi è stato", "chi sono",
        "che cosa è"
    )
    if any(phrase in q for phrase in wiki_phrases):
        return wiki_search(query)

    # ─── URL scraping ──────────────────────────────────────────────────
    if q.startswith("http://") or q.startswith("https://"):
        return scrape_title(q)

    # ─── Calcoli matematici ────────────────────────────────────────────
    if re.search(r'\d', query) and re.search(r'[+\-*/^()]', query):
        math_expr = re.sub(r'[^\d\+\-\*/\^\(\)\.\s]', '', query).strip()
        if math_expr:
            result = calculate(math_expr)
            if "Risultato:" in result:  # Se il calcolo è riuscito
                return result

    # ─── Meteo (priorità bassa) ────────────────────────────────────────
    if "meteo" in q or "tempo" in q or "previsione" in q or "previsioni" in q:
        city = "Napoli"
        match = re.search(r"(?:meteo|tempo|previsione[i]?)(?:\s+(?:a|di|in|per))?\s+(.+)", q)
        if match:
            city_candidate = match.group(1).strip(" ?!.,")
            if city_candidate and len(city_candidate) > 1:
                city = city_candidate
        result = get_weather(city)
        if result and "Impossibile" not in result:
            return result

    return None
