"""Pydantic models for the Agentic RFP workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReadabilityResult(BaseModel):
    pass_: bool = Field(alias="pass")
    score: float
    details: str

    model_config = {"populate_by_name": True}


class RelevanceResult(BaseModel):
    pass_: bool = Field(alias="pass")
    missing_aspects: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ComplianceResult(BaseModel):
    pass_: bool = Field(alias="pass")
    rule_ids: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class EvaluationResult(BaseModel):
    section_id: str
    department_id: str
    readability: ReadabilityResult
    relevance: RelevanceResult
    compliance: ComplianceResult
    overall_pass: bool
    feedback_for_generator: str = ""


class DepartmentSummary(BaseModel):
    department_id: str
    key_aspects: list[str] = Field(default_factory=list)
    contact_name: str = ""
    contact_email: str = ""
    raw_excerpt: str = ""


class SectionDraft(BaseModel):
    department_id: str
    version: int = 1
    iteration: int = 0
    content: str = ""
    structured_claims: dict[str, Any] = Field(default_factory=dict)


class DepartmentProgress(BaseModel):
    department_id: str
    status: str = "pending"
    iteration: int = 0
    latest_evaluation: Optional[EvaluationResult] = None


class NodeLogEntry(BaseModel):
    ticket_id: str
    department_id: Optional[str] = None
    node: str
    agent: str
    input_summary: str = ""
    output_summary: str = ""
    timestamp: str = Field(default_factory=_now_iso)


class RfpTicket(BaseModel):
    id: str = Field(default_factory=lambda: f"rfp_{uuid4().hex[:12]}")
    filename: str = ""
    status: str = "analyzing"
    pdf_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    readability_metrics: dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    department_summaries: list[DepartmentSummary] = Field(default_factory=list)
    department_progress: dict[str, DepartmentProgress] = Field(default_factory=dict)
    drafts: dict[str, SectionDraft] = Field(default_factory=dict)
    evaluations: dict[str, EvaluationResult] = Field(default_factory=dict)
    final_document: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)
