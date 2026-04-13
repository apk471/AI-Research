from __future__ import annotations

import re
from typing import Iterable, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

from app.schemas import EvidenceItem

ALLOWED_DOMAIN_HINTS = {
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "who.int",
    "nature.com",
    "thelancet.com",
    "nejm.org",
    "jama.com",
    "bmj.com",
    "sciencedirect.com",
    "healthcareitnews.com",
    "statnews.com",
    "healthaffairs.org",
    "mayoclinic.org",
    "clevelandclinic.org",
    "medrxiv.org",
    "arxiv.org",
}

BLOCKED_DOMAIN_HINTS = {
    "baidu.com",
    "wordreference.com",
    "dictionary.com",
    "wiktionary.org",
    "quora.com",
    "reddit.com",
    "pinterest.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
}

REQUIRED_TOPIC_TERMS = {
    "ai",
    "artificial intelligence",
    "machine learning",
    "healthcare",
    "health care",
    "medical",
    "clinical",
    "hospital",
    "diagnostic",
    "patient",
}


async def search_web(query: str, limit: int = 5) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=limit * 3))
    except Exception:
        results = []

    for result in results:
        url = result.get("href") or result.get("url")
        if not url:
            continue

        title = result.get("title") or url
        snippet = result.get("body") or result.get("snippet") or ""
        if not is_candidate_relevant(query=query, title=title, snippet=snippet, url=url):
            continue

        content = await scrape_article(url)
        normalized_content = normalize_text(content or snippet)
        if not is_candidate_relevant(query=query, title=title, snippet=normalized_content, url=url):
            continue

        score = relevance_score(query=query, title=title, snippet=normalized_content, url=url)
        if score < 0.55:
            continue

        items.append(
            EvidenceItem(
                title=title,
                url=url,
                snippet=normalized_content[:1000],
                source_type="web",
                published_at=None,
                score=score,
            )
        )

    items.sort(key=lambda item: item.score, reverse=True)
    return items[:limit]


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


def is_candidate_relevant(query: str, title: str, snippet: str, url: str) -> bool:
    normalized_title = normalize_text(title).lower()
    normalized_snippet = normalize_text(snippet).lower()
    normalized_query = query.lower()
    host = (urlparse(url).hostname or "").lower()
    combined = " ".join([normalized_title, normalized_snippet, normalized_query, host])

    if any(blocked in host for blocked in BLOCKED_DOMAIN_HINTS):
        return False

    query_terms = [term for term in normalized_query.split() if len(term) > 3]
    query_overlap = sum(1 for term in query_terms if term in combined)
    topic_overlap = sum(1 for term in REQUIRED_TOPIC_TERMS if term in combined)
    trusted_domain = any(allowed in host for allowed in ALLOWED_DOMAIN_HINTS)

    if trusted_domain and topic_overlap >= 1:
        return True

    return topic_overlap >= 2 and query_overlap >= 2


def relevance_score(query: str, title: str, snippet: str, url: str) -> float:
    normalized_title = normalize_text(title).lower()
    normalized_snippet = normalize_text(snippet).lower()
    normalized_query = query.lower()
    host = (urlparse(url).hostname or "").lower()
    combined = " ".join([normalized_title, normalized_snippet, normalized_query, host])

    query_terms = [term for term in normalized_query.split() if len(term) > 3]
    query_overlap = sum(1 for term in query_terms if term in combined)
    topic_overlap = sum(1 for term in REQUIRED_TOPIC_TERMS if term in combined)
    trusted_domain_bonus = 0.2 if any(allowed in host for allowed in ALLOWED_DOMAIN_HINTS) else 0.0
    title_bonus = 0.1 if "health" in normalized_title or "medical" in normalized_title else 0.0

    score = min(1.0, 0.15 * query_overlap + 0.12 * topic_overlap + trusted_domain_bonus + title_bonus)
    return round(score, 2)


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


def build_search_variants(query: str, focus_areas: Iterable[str]) -> list[str]:
    variants = [query, f"{query} recent research", f"{query} statistics", f"{query} study OR report"]
    for focus in focus_areas:
        variants.append(f"{query} {focus}")
        variants.append(f"{query} {focus} recent statistics")
    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        key = variant.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(variant)
    return deduped
