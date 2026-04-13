from __future__ import annotations

from app.schemas import Confidence, EvidenceItem, ReportSection


class ValidatorAgent:
    async def run(self, sections: list[ReportSection], evidence: list[EvidenceItem]) -> tuple[list[ReportSection], Confidence]:
        evidence_count = len(evidence)
        web_count = sum(1 for item in evidence if item.source_type == "web")
        unique_source_count = len({item.url for item in evidence})
        supported_sections = 0
        for section in sections:
            citation_count = len(section.citations)
            if citation_count >= 2:
                supported_sections += 1
            elif citation_count == 1:
                section.content = f"{section.content} This section currently relies on a single cited source."
            elif "low confidence" not in section.content.lower():
                section.content = f"{section.content} Evidence coverage is limited, so confidence is reduced."

        data_quality = min(1.0, evidence_count / 10) if evidence_count else 0.0
        if web_count == 0:
            data_quality = min(data_quality, 0.25)
        elif web_count == 1:
            data_quality = min(data_quality, 0.45)

        source_reliability = supported_sections / max(1, len(sections))
        if unique_source_count < 3:
            source_reliability = min(source_reliability, 0.5)
        if web_count == 0:
            source_reliability = min(source_reliability, 0.55)

        overall = round((data_quality * 0.55) + (source_reliability * 0.45), 2)
        if unique_source_count < 3:
            overall = min(overall, 0.45)
        if web_count == 0:
            overall = min(overall, 0.4)

        return (
            sections,
            Confidence(
                overall=overall,
                data_quality=round(data_quality, 2),
                source_reliability=round(source_reliability, 2),
            ),
        )
