"""Reverse Logistics section generator."""

from __future__ import annotations

from typing import Any

from data.pipelines.rfp_intake.draft.generators._shared import _base_draft
from data.pipelines.rfp_intake.models import DepartmentSummary, SectionDraft


def generate(
    *,
    summary: DepartmentSummary,
    metadata: dict[str, Any],
    previous_draft: SectionDraft | None = None,
    feedback: str = "",
) -> SectionDraft:
    body = [
        "Returns processing turnaround: 72 hours from receipt at the returns hub.",
        "Returns processing cost follows TrackFlow standard reverse logistics rate card.",
    ]
    claims: dict[str, Any] = {"returns_turnaround_hours": 72}
    return _base_draft(
        department_id="reverse",
        summary=summary,
        metadata=metadata,
        previous_draft=previous_draft,
        feedback=feedback,
        body_lines=body,
        structured_claims=claims,
    )
