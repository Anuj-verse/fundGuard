from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    case_id: str | None = None
    account_id: str
    transaction_ids: list[str] = Field(default_factory=list)
    graph_subnetwork: dict[str, Any] = Field(default_factory=dict)
    risk_score: float = Field(ge=0.0, le=1.0)
    pattern_flags: list[str] = Field(default_factory=list)


class SimilarCase(BaseModel):
    case_id: str
    summary: str
    similarity: float | None = None


class ExplainResponse(BaseModel):
    case_id: str
    account_id: str
    generated_at: datetime
    investigation_summary: str
    risk_rationale: str
    str_draft: str
    similar_cases: list[SimilarCase] = Field(default_factory=list)


class ReportRequest(BaseModel):
    title: str | None = None
