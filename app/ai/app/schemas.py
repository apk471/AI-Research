from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


ResearchStatus = Literal["queued", "running", "completed", "failed", "partial"]


class ResearchRequest(BaseModel):
    query: str = Field(min_length=10, max_length=500)
    session_id: str | None = None


class PlanStep(BaseModel):
    step: str


class PlannerOutput(BaseModel):
    steps: list[PlanStep]
    search_queries: list[str]
    focus_areas: list[str]


class EvidenceItem(BaseModel):
    title: str
    url: str
    snippet: str
    source_type: Literal["web", "pdf", "internal_doc"]
    published_at: str | None = None
    score: float = 0.5


class ReportSection(BaseModel):
    heading: str
    content: str
    citations: list[str]


class ReportSource(BaseModel):
    title: str
    url: HttpUrl | str
    source_type: Literal["web", "pdf", "internal_doc"]


class Confidence(BaseModel):
    overall: float
    data_quality: float
    source_reliability: float


class ResearchReport(BaseModel):
    title: str
    summary: str
    sections: list[ReportSection]
    sources: list[ReportSource]
    confidence: Confidence


class StreamEvent(BaseModel):
    type: str
    status: ResearchStatus
    message: str
    agent: str | None = None
    timestamp: datetime
    data: dict[str, Any] | None = None
    report: ResearchReport | None = None
    error: str | None = None


class ResearchRunResponse(BaseModel):
    session_id: str
    status: ResearchStatus
    report: ResearchReport | None = None
    events: list[StreamEvent]
