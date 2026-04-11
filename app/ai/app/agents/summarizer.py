from __future__ import annotations

from collections import defaultdict

from app.llm import OllamaClient
from app.schemas import EvidenceItem, PlannerOutput, ReportSection


class SummarizerAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    async def run(
        self, query: str, plan: PlannerOutput, search_results: list[EvidenceItem], rag_results: list[EvidenceItem]
    ) -> list[ReportSection]:
        evidence = (search_results + rag_results)[:10]
        grouped = defaultdict(list)
        for index, focus in enumerate(plan.focus_areas[:3]):
            for item in evidence[index:: max(1, len(plan.focus_areas[:3]))]:
                grouped[focus].append(item)

        sections: list[ReportSection] = []
        for heading, items in grouped.items():
            citations = [item.url for item in items[:3]]
            content = " ".join(item.snippet[:300] for item in items[:3]).strip()
            if not content:
                content = f"No strong evidence was collected for {heading}. The report should treat this as low confidence."
            sections.append(ReportSection(heading=heading.title(), content=content, citations=citations))

        if not sections:
            sections.append(
                ReportSection(
                    heading="Findings",
                    content=f"Insufficient evidence was collected to fully answer: {query}",
                    citations=[],
                )
            )
        return sections
