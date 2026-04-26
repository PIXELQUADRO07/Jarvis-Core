import requests

from core.tools.cache import get as cache_get, set_cache


def get_weather(city: str) -> str:
    city = city.strip() or "Napoli"
    cache_key = f"weather:{city.lower()}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    url = f"https://wttr.in/{requests.utils.requote_uri(city)}?format=j1"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get('current_condition', [{}])[0]
        temp = current.get('temp_C', 'N/A')
        desc = current.get('weatherDesc', [{}])[0].get('value', 'N/A')
        local_time = current.get('localObsDateTime', 'N/A')
        area = data.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', city.title())
        text = f"{area}: {desc}, {temp}°C, ora locale {local_time}"
        set_cache(cache_key, text)
        return text
    except (requests.RequestException, KeyError, IndexError, ValueError):
        stale = cache_get(cache_key, ttl=None)
        if stale:
            return f"{stale} (dati memorizzati)"
        return "Impossibile ottenere il meteo in questo momento."


def get_time(city: str) -> str:
    city = city.strip() or "Napoli"
    cache_key = f"time:{city.lower()}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    url = f"https://wttr.in/{requests.utils.requote_uri(city)}?format=j1"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get('current_condition', [{}])[0]
        local_time = current.get('localObsDateTime', 'N/A')
        area = data.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', city.title())
        text = f"In {area} è ora {local_time}"
        set_cache(cache_key, text)
        return text
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return f"Impossibile ottenere l'ora per {city}."
