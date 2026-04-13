from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import AsyncIterator

from app.agents.formatter import FormatterAgent
from app.agents.planner import PlannerAgent
from app.agents.rag import RagAgent
from app.agents.search import SearchAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.validator import ValidatorAgent
from app.llm import OllamaClient
from app.schemas import ResearchRequest, ResearchRunResponse, StreamEvent
from app.tools.rag import RagStore


class ResearchOrchestrator:
    def __init__(self) -> None:
        llm = OllamaClient()
        rag_store = RagStore()
        self.planner = PlannerAgent(llm)
        self.search = SearchAgent()
        self.rag = RagAgent(rag_store)
        self.summarizer = SummarizerAgent(llm)
        self.validator = ValidatorAgent()
        self.formatter = FormatterAgent()

    async def run(self, request: ResearchRequest) -> ResearchRunResponse:
        events = []
        report = None
        async for event in self.stream(request):
            events.append(event)
            if event.report is not None:
                report = event.report

        status = events[-1].status if events else "failed"
        return ResearchRunResponse(
            session_id=request.session_id or "unknown",
            status=status,
            report=report,
            events=events,
        )

    async def stream(self, request: ResearchRequest) -> AsyncIterator[StreamEvent]:
        try:
            yield self._event("planning_started", "running", "Planner agent is building execution plan", "planner")
            planner_result = await self.planner.run(request.query)
            plan = planner_result.output

            yield self._event(
                "planning_completed",
                "running",
                "Plan ready",
                "planner",
                data={
                    "steps": [step.step for step in plan.steps],
                    "focus_areas": plan.focus_areas,
                    "llm_model": planner_result.model,
                    "used_fallback": planner_result.used_fallback,
                },
            )

            if planner_result.used_fallback:
                yield self._event(
                    "planner_warning",
                    "running",
                    "Planner fell back to default plan because the local model response was unavailable or invalid",
                    "planner",
                    data={
                        "error": planner_result.error,
                        "llm_model": planner_result.model,
                    },
                )

            yield self._event("search_started", "running", "Search and RAG agents started", "orchestrator")
            search_results, rag_results = await asyncio.gather(
                self.search.run(plan),
                self.rag.run(request.query),
            )

            yield self._event(
                "search_completed",
                "running",
                "Evidence collection completed",
                "search",
                data={
                    "web_results": len(search_results),
                    "rag_results": len(rag_results),
                    "minimum_web_results_met": len(search_results) >= 2,
                },
            )

            if len(search_results) == 0:
                yield self._event(
                    "search_warning",
                    "running",
                    "No relevant web sources were found; the run will rely on local RAG evidence and should be treated as partial",
                    "search",
                    data={"query": request.query},
                )

            yield self._event("summarizing", "running", "Summarizer agent is drafting sections", "summarizer")
            sections = await self.summarizer.run(request.query, plan, search_results, rag_results)

            yield self._event("fact_checking", "running", "Validator agent is checking evidence support", "validator")
            evidence = search_results + rag_results
            sections, confidence = await self.validator.run(sections, evidence)

            yield self._event("formatting", "running", "Formatter agent is producing the final report", "formatter")
            report = await self.formatter.run(request.query, sections, evidence, confidence)

            web_source_count = sum(1 for source in report.sources if source.source_type == "web")
            sufficiently_supported = len(report.sources) >= 3 and web_source_count >= 2
            final_status = "completed" if sufficiently_supported else "partial"
            yield self._event(
                "completed",
                final_status,
                "Research report completed" if sufficiently_supported else "Research report completed with limited evidence",
                "formatter",
                data={
                    "source_count": len(report.sources),
                    "web_source_count": web_source_count,
                    "sufficiently_supported": sufficiently_supported,
                    "confidence_overall": report.confidence.overall,
                },
                report=report,
            )
        except Exception as exc:
            yield self._event(
                "failed",
                "failed",
                "Research orchestration failed",
                "orchestrator",
                data={"query": request.query},
                error=str(exc),
            )

    def _event(
        self,
        event_type: str,
        status: str,
        message: str,
        agent: str,
        data: dict | None = None,
        report=None,
        error: str | None = None,
    ) -> StreamEvent:
        return StreamEvent(
            type=event_type,
            status=status,  # type: ignore[arg-type]
            message=message,
            agent=agent,
            timestamp=datetime.now(UTC),
            data=data,
            report=report,
            error=error,
        )
