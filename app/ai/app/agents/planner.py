from __future__ import annotations

from dataclasses import dataclass

from app.llm import LLMGenerationResult, OllamaClient
from app.schemas import PlannerOutput, PlanStep


@dataclass
class PlannerRunResult:
    output: PlannerOutput
    used_fallback: bool
    error: str | None
    model: str | None


class PlannerAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    async def run(self, query: str) -> PlannerRunResult:
        fallback = {
            "steps": [
                {"step": "Search recent research and statistics"},
                {"step": "Retrieve related internal research notes"},
                {"step": "Synthesize findings into report sections"},
                {"step": "Validate claims against available sources"},
            ],
            "search_queries": [query, f"{query} recent research", f"{query} statistics"],
            "focus_areas": ["market adoption", "clinical outcomes", "risks and limitations"],
        }
        prompt = (
            "You are a research planner. Return JSON with keys steps, search_queries, focus_areas. "
            f"User query: {query}"
        )
        result: LLMGenerationResult = await self.llm.generate_json(prompt, fallback)
        data = result.data
        return PlannerRunResult(
            output=PlannerOutput(
                steps=[PlanStep(**step) for step in data.get("steps", fallback["steps"])],
                search_queries=data.get("search_queries", fallback["search_queries"]),
                focus_areas=data.get("focus_areas", fallback["focus_areas"]),
            ),
            used_fallback=result.used_fallback,
            error=result.error,
            model=result.model,
        )
