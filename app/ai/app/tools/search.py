from __future__ import annotations

from typing import List

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from app.schemas import EvidenceItem


async def search_web(query: str, limit: int = 5) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=limit))
    except Exception:
        results = []

    for result in results:
        url = result.get("href") or result.get("url")
        if not url:
            continue
        snippet = result.get("body") or result.get("snippet") or ""
        content = await scrape_article(url)
        items.append(
            EvidenceItem(
                title=result.get("title") or url,
                url=url,
                snippet=(content or snippet)[:1000],
                source_type="web",
                published_at=None,
                score=0.7,
            )
        )

    return items


async def scrape_article(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "AI-Research/1.0"})
            response.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    return text[:4000]
