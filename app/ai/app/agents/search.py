from __future__ import annotations

from app.schemas import EvidenceItem, PlannerOutput
from app.tools.search import build_search_variants, search_web


class SearchAgent:
    async def run(self, plan: PlannerOutput) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        seen_urls: set[str] = set()
        queries = build_search_variants(" ".join(plan.search_queries[:1]) or "healthcare ai", plan.focus_areas[:3])
        queries = plan.search_queries[:3] + [query for query in queries if query not in plan.search_queries[:3]]
        for query in queries[:8]:
            results = await search_web(query, limit=4)
            for item in results:
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)
                evidence.append(item)
            if len(evidence) >= 6:
                break
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[:8]
