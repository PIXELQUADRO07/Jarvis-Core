"""
core/tools/web_search.py — Web search via DuckDuckGo (no API key required).
"""
import json
import re
import urllib.parse
import urllib.request
from typing import List, Dict, Optional
from logger import debug, error


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JarvisBot/2.0)"
}
_TIMEOUT = 8


def _ddg_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Usa l'endpoint instant-answer JSON di DuckDuckGo.
    Non richiede API key, gratuito, rispetta ToS.
    """
    url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    })
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            data = json.loads(r.read().decode())

        results = []

        # Abstract (risposta diretta DDG)
        if data.get("AbstractText"):
            results.append({
                "title":   data.get("Heading", ""),
                "url":     data.get("AbstractURL", ""),
                "snippet": data["AbstractText"],
                "source":  data.get("AbstractSource", "DuckDuckGo"),
            })

        # Related topics
        for topic in data.get("RelatedTopics", []):
            if len(results) >= max_results:
                break
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title":   topic.get("Text", "")[:60],
                    "url":     topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "source":  "DuckDuckGo",
                })

        debug(f"DDG search '{query}': {len(results)} results")
        return results

    except Exception as e:
        error(f"Web search error: {e}")
        return []


def search_web(query: str, max_results: int = 3) -> Optional[str]:
    """
    Search the web and return a formatted response.
    Used by the router for queries not handled by other tools.
    """
    results = _ddg_search(query, max_results)
    if not results:
        return None

    lines = [f"🔍 Web results for: **{query}**\n"]
    for i, r in enumerate(results, 1):
        title   = r.get("title", "")[:80]
        snippet = r.get("snippet", "")[:200]
        url     = r.get("url", "")
        lines.append(f"**{i}. {title}**")
        lines.append(f"   {snippet}")
        if url:
            lines.append(f"   {url}")
        lines.append("")

    return "\n".join(lines)
