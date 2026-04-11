from __future__ import annotations

from app.schemas import Confidence, ReportSection


class ValidatorAgent:
    async def run(self, sections: list[ReportSection], evidence_count: int) -> tuple[list[ReportSection], Confidence]:
        supported_sections = 0
        for section in sections:
            if section.citations:
                supported_sections += 1
            elif "low confidence" not in section.content.lower():
                section.content = f"{section.content} Evidence coverage is limited, so confidence is reduced."

        data_quality = min(1.0, evidence_count / 8) if evidence_count else 0.2
        source_reliability = supported_sections / max(1, len(sections))
        overall = round((data_quality + source_reliability) / 2, 2)

        return (
            sections,
            Confidence(
                overall=overall,
                data_quality=round(data_quality, 2),
                source_reliability=round(source_reliability, 2),
            ),
        )
