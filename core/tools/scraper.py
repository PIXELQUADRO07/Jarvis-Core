import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

from logger import debug, warning


def scrape_title(url: str) -> str:
    """Scrapa il titolo di una pagina HTML"""
    debug(f"Scraping title from {url[:60]}...")
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "jarvis-bot/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else None
        
        if title:
            title = title.strip()
            return f"📄 {title}"
        return "❌ Nessun titolo trovato nella pagina."
    except requests.exceptions.Timeout:
        warning(f"Scraping timeout for {url}")
        return "❌ La pagina ha impiegato troppo tempo per rispondere."
    except requests.exceptions.ConnectionError:
        warning(f"Scraping connection error for {url}")
        return "❌ Impossibile raggiungere la pagina."
    except requests.RequestException as e:
        warning(f"Scraping request error for {url}: {e}")
        return "❌ Errore nel download della pagina."
    except Exception as e:
        warning(f"Scraping error for {url}: {e}")
        return "❌ Errore nello scraping della pagina."


def scrape_wikipedia_summary(title: str) -> str:
    """Scrapa il primo paragrafo di Wikipedia italiano"""
    title = title.strip()
    if not title:
        return ""

    encoded = quote(title.replace(" ", "_"), safe="")
    url = f"https://it.wikipedia.org/wiki/{encoded}"
    debug(f"Scraping Wikipedia for {title}")

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "jarvis-bot/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for paragraph in soup.select("div.mw-parser-output > p"):
            text = paragraph.get_text(strip=True)
            if text and len(text) > 20:  # Solo paragrafi significativi
                return text
        warning(f"No Wikipedia summary found for {title}")
        return ""
    except requests.exceptions.Timeout:
        warning(f"Wikipedia scraping timeout for {title}")
        return ""
    except requests.RequestException as e:
        warning(f"Wikipedia scraping error for {title}: {e}")
        return ""
    except Exception as e:
        warning(f"Unexpected Wikipedia scraping error for {title}: {e}")
        return ""
