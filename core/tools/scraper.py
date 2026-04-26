import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


def scrape_title(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "jarvis-bot/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else "Nessun titolo"
        return title.strip()
    except requests.RequestException:
        return "Non è stato possibile scaricare la pagina."
    except Exception:
        return "Errore nello scraping."


def scrape_wikipedia_summary(title: str) -> str:
    title = title.strip()
    if not title:
        return ""

    encoded = quote(title.replace(" ", "_"), safe="")
    url = f"https://it.wikipedia.org/wiki/{encoded}"

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "jarvis-bot/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for paragraph in soup.select("div.mw-parser-output > p"):
            text = paragraph.get_text(strip=True)
            if text:
                return text
        return ""
    except requests.RequestException:
        return ""
    except Exception:
        return ""
