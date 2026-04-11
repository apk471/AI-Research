from __future__ import annotations

from app.schemas import Confidence, EvidenceItem, ReportSection, ReportSource, ResearchReport


class FormatterAgent:
    async def run(
        self,
        query: str,
        sections: list[ReportSection],
        evidence: list[EvidenceItem],
        confidence: Confidence,
    ) -> ResearchReport:
        unique_sources: dict[str, ReportSource] = {}
        for item in evidence:
            unique_sources[item.url] = ReportSource(
                title=item.title,
                url=item.url,
                source_type=item.source_type,
            )

        summary = sections[0].content[:280] if sections else f"Research report for {query}"
        return ResearchReport(
            title=f"Research Report: {query}",
            summary=summary,
            sections=sections,
            sources=list(unique_sources.values())[:10],
            confidence=confidence,
        )
