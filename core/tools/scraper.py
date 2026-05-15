import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

from logger import debug, warning


def scrape_title(url: str) -> str:
    """Scrape the title of an HTML page."""
    debug(f"Scraping title from {url[:60]}...")
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "jarvis-bot/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else None
        
        if title:
            title = title.strip()
            return f"📄 {title}"
        return "❌ No title found on the page."
    except requests.exceptions.Timeout:
        warning(f"Scraping timeout for {url}")
        return "❌ The page took too long to respond."
    except requests.exceptions.ConnectionError:
        warning(f"Scraping connection error for {url}")
        return "❌ Unable to reach the page."
    except requests.RequestException as e:
        warning(f"Scraping request error for {url}: {e}")
        return "❌ Error downloading the page."
    except Exception as e:
        warning(f"Scraping error for {url}: {e}")
        return "❌ Error scraping the page."


def scrape_wikipedia_summary(title: str) -> str:
    """Scrape the first paragraph from an Italian Wikipedia page."""
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
