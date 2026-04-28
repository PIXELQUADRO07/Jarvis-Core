import requests

from core.tools.cache import get as cache_get, set_cache
from logger import debug, warning


def get_weather(city: str) -> str:
    """Ottiene previsioni meteo da wttr.in"""
    city = city.strip() or "Napoli"
    cache_key = f"weather:{city.lower()}"
    cached = cache_get(cache_key)
    if cached:
        debug(f"Weather cache hit for {city}")
        return cached

    url = f"https://wttr.in/{requests.utils.requote_uri(city)}?format=j1"
    debug(f"Fetching weather for {city} from {url}")

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get('current_condition', [{}])[0]
        temp = current.get('temp_C', 'N/A')
        desc = current.get('weatherDesc', [{}])[0].get('value', 'N/A')
        local_time = current.get('localObsDateTime', 'N/A')
        area = data.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', city.title())
        
        text = f"🌍 {area}: {desc}, {temp}°C, ora locale {local_time}"
        set_cache(cache_key, text)
        return text
    except requests.exceptions.Timeout:
        warning(f"Weather timeout for {city}")
        return f"❌ Il servizio meteo sta impiegando troppo tempo per {city}."
    except requests.exceptions.ConnectionError:
        warning(f"Weather connection error for {city}")
        return f"❌ Impossibile raggiungere il servizio meteo per {city}."
    except (KeyError, IndexError, ValueError) as e:
        warning(f"Weather parsing error for {city}: {e}")
        stale = cache_get(cache_key, ttl=None)
        if stale:
            return f"{stale} (dati memorizzati)"
        return f"❌ Impossibile ottenere il meteo per {city}. Prova con un'altra città."
    except Exception as e:
        warning(f"Unexpected weather error for {city}: {e}")
        return "❌ Errore nel servizio meteo. Riprova più tardi."


def get_time(city: str) -> str:
    """Ottiene l'ora locale di una città"""
    city = city.strip() or "Napoli"
    cache_key = f"time:{city.lower()}"
    cached = cache_get(cache_key)
    if cached:
        debug(f"Time cache hit for {city}")
        return cached

    url = f"https://wttr.in/{requests.utils.requote_uri(city)}?format=j1"
    debug(f"Fetching time for {city}")

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get('current_condition', [{}])[0]
        local_time = current.get('localObsDateTime', 'N/A')
        area = data.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', city.title())
        
        text = f"🕐 In {area} sono le {local_time}"
        set_cache(cache_key, text)
        return text
    except Exception as e:
        warning(f"Time fetch error for {city}: {e}")
        return f"❌ Impossibile ottenere l'ora per {city}."
