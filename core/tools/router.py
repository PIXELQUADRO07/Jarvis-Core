import re

from core.tools.api_wiki import wiki_search
from core.tools.api_weather import get_weather, get_time
from core.tools.scraper import scrape_title
from core.tools.system import system_command
from core.tools.math import calculate


def route_query(query: str):
    q = query.lower().strip()

    # Check time queries BEFORE system_command to avoid conflicts
    if "ore" in q and ("in" in q or "a" in q):
        match = re.search(r'(?:in|a)\s+(.+)', q, re.IGNORECASE)
        if match:
            city = match.group(1).strip(" ?")
            return get_time(city)

    # Check Wikipedia queries BEFORE system_command to prioritize info lookup
    if any(phrase in q for phrase in ("chi è", "chi e", "cos'è", "cos e", "cosa è", "cosa e", "chi ha", "chi era", "che ha", "che ha creato", "che ha inventato", "spiega", "parlami di", "raccontami di")):
        return wiki_search(query)

    system_result = system_command(query)
    if system_result:
        return system_result

    if "meteo" in q or "tempo" in q:
        city = "Napoli"
        match = re.search(r"(?:meteo|tempo)(?:\s+(?:a|di|in|per))?\s+(.+)", q)
        if match:
            city_candidate = match.group(1).strip(" ?")
            if city_candidate:
                city = city_candidate
        result = get_weather(city)
        return result

    if q.startswith("http://") or q.startswith("https://"):
        return scrape_title(q)

    # Controlla se sembra un'espressione matematica
    if re.search(r'\d', query) and re.search(r'[+\-*/^()]', query):
        math_expr = re.sub(r'[^\d\+\-\*/\^\(\)\.\s]', '', query).strip()
        if math_expr:
            return calculate(math_expr)

    return None
