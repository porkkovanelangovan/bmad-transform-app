"""
Web Search — Real web search via DuckDuckGo HTML scraping or Brave Search API.
Falls back gracefully: Brave -> DuckDuckGo -> empty list.
"""

import os
import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


async def search_web(query: str, num_results: int = 5) -> list[dict]:
    """Search the web. Tries Brave Search API first, falls back to DuckDuckGo scraping."""
    if BRAVE_API_KEY:
        try:
            results = await _brave_search(query, num_results)
            if results:
                return results
        except Exception as e:
            logger.warning("Brave Search failed, falling back to DuckDuckGo: %s", e)

    try:
        return await _duckduckgo_search(query, num_results)
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)
        return []


async def _brave_search(query: str, num_results: int) -> list[dict]:
    """Search via Brave Search API (requires BRAVE_SEARCH_API_KEY)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": num_results},
            headers={
                "X-Subscription-Token": BRAVE_API_KEY,
                "Accept": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("web", {}).get("results", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
        })
    return results


async def _duckduckgo_search(query: str, num_results: int) -> list[dict]:
    """Scrape DuckDuckGo HTML search results (no API key needed)."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for result_div in soup.select(".result"):
        # Skip ad results
        if result_div.get("class") and "result--ad" in result_div.get("class", []):
            continue

        title_tag = result_div.select_one(".result__title a, .result__a")
        snippet_tag = result_div.select_one(".result__snippet")

        title = title_tag.get_text(strip=True) if title_tag else ""
        url = ""
        if title_tag and title_tag.get("href"):
            url = title_tag["href"]
            # DuckDuckGo wraps URLs in redirect; extract actual URL if possible
            if "uddg=" in url:
                from urllib.parse import unquote, urlparse, parse_qs
                parsed = parse_qs(urlparse(url).query)
                url = unquote(parsed.get("uddg", [url])[0])
            # Skip remaining ad/tracking URLs that slipped through
            elif url.startswith("https://duckduckgo.com/y.js"):
                continue
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

        if title:
            results.append({"title": title, "url": url, "snippet": snippet})
            if len(results) >= num_results:
                break

    return results
