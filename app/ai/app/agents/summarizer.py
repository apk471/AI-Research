from __future__ import annotations

from collections import defaultdict
import re

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
        focus_areas = plan.focus_areas[:3] or ["findings"]
        for item in evidence:
            focus = self._assign_focus_area(item, focus_areas)
            grouped[focus].append(item)

        sections: list[ReportSection] = []
        for heading in focus_areas:
            items = grouped.get(heading, [])
            citations = self._unique_citations(items)
            content = self._build_section_content(heading, items)
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

    def _assign_focus_area(self, item: EvidenceItem, focus_areas: list[str]) -> str:
        combined = f"{item.title} {item.snippet}".lower()
        scores = []
        for focus in focus_areas:
            terms = [term for term in re.split(r"[^a-zA-Z]+", focus.lower()) if len(term) > 2]
            score = sum(1 for term in terms if term in combined)
            scores.append((score, focus))
        scores.sort(reverse=True)
        if scores and scores[0][0] > 0:
            return scores[0][1]
        if item.source_type == "web":
            return focus_areas[0]
        return focus_areas[-1]

    def _build_section_content(self, heading: str, items: list[EvidenceItem]) -> str:
        if not items:
            return f"Evidence for {heading} was limited in this run. Treat this section as incomplete and low confidence."

        sentences = self._ranked_sentences(items)
        top_sentences = sentences[:3]
        if not top_sentences:
            return f"Evidence for {heading} was collected, but the extracted passages were too noisy to support a clean summary."

        lead = self._section_lead(heading, items)
        return " ".join([lead, *top_sentences]).strip()

    def _ranked_sentences(self, items: list[EvidenceItem]) -> list[str]:
        ranked: list[tuple[float, str]] = []
        seen: set[str] = set()
        for item in items[:4]:
            for sentence in self._split_sentences(item.snippet):
                normalized = sentence.lower()
                if normalized in seen:
                    continue
                seen.add(normalized)
                length = len(sentence.split())
                if length < 8 or length > 40:
                    continue
                score = item.score
                if any(token in normalized for token in ("%", "percent", "study", "trial", "survey", "hospital", "patient")):
                    score += 0.12
                if item.source_type == "web":
                    score += 0.08
                ranked.append((score, sentence))

        ranked.sort(key=lambda value: value[0], reverse=True)
        return [sentence for _, sentence in ranked]

    def _split_sentences(self, text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text).strip().replace("#", "")
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        return [part.strip() for part in parts if part.strip()]

    def _section_lead(self, heading: str, items: list[EvidenceItem]) -> str:
        web_count = sum(1 for item in items if item.source_type == "web")
        if web_count >= 2:
            return f"Recent evidence suggests the main pattern in {heading} is becoming clearer."
        if web_count == 1:
            return f"Available evidence points to early signals in {heading}, but external coverage is still limited."
        return f"This section is driven mostly by local reference material rather than recent external reporting."

    def _unique_citations(self, items: list[EvidenceItem]) -> list[str]:
        citations: list[str] = []
        seen: set[str] = set()
        for item in items[:4]:
            if item.url in seen:
                continue
            seen.add(item.url)
            citations.append(item.url)
        return citations
