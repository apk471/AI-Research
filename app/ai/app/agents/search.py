from __future__ import annotations

from app.schemas import EvidenceItem, PlannerOutput
from app.tools.search import search_web


class SearchAgent:
    async def run(self, plan: PlannerOutput) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        seen_urls: set[str] = set()
        for query in plan.search_queries[:3]:
            results = await search_web(query, limit=4)
            for item in results:
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)
                evidence.append(item)
        return evidence[:8]
