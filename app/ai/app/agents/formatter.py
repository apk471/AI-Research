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
        for item in sorted(evidence, key=lambda current: current.score, reverse=True):
            unique_sources[item.url] = ReportSource(
                title=item.title,
                url=item.url,
                source_type=item.source_type,
            )

        cleaned_sections = [self._clean_section(section) for section in sections]
        summary = self._build_summary(cleaned_sections, query)
        return ResearchReport(
            title=f"Research Report: {query}",
            summary=summary,
            sections=cleaned_sections,
            sources=list(unique_sources.values())[:10],
            confidence=confidence,
        )

    def _clean_section(self, section: ReportSection) -> ReportSection:
        content = " ".join(section.content.replace("#", " ").split())
        return ReportSection(
            heading=section.heading,
            content=content,
            citations=list(dict.fromkeys(section.citations)),
        )

    def _build_summary(self, sections: list[ReportSection], query: str) -> str:
        if not sections:
            return f"Research report for {query}"

        summary_parts: list[str] = []
        for section in sections[:2]:
            sentence = section.content.split(". ")[0].strip()
            if sentence and sentence not in summary_parts:
                summary_parts.append(sentence.rstrip(".") + ".")
        summary = " ".join(summary_parts).strip()
        if not summary:
            return f"Research report for {query}"
        return summary[:320]
