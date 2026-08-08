"""Shared helpers for department generators."""

from __future__ import annotations

from typing import Any

from data.pipelines.rfp_intake.context_config import DEPARTMENT_BY_ID
from data.pipelines.rfp_intake.models import DepartmentSummary, SectionDraft


def _base_draft(
    *,
    department_id: str,
    summary: DepartmentSummary,
    metadata: dict[str, Any],
    previous_draft: SectionDraft | None,
    feedback: str,
    body_lines: list[str],
    structured_claims: dict[str, Any],
) -> SectionDraft:
    dept = DEPARTMENT_BY_ID[department_id]
    iteration = 0 if previous_draft is None else previous_draft.iteration + 1
    currency = metadata.get("currency", "USD")
    aspect_lines = "\n".join(f"- {aspect}: covered per TrackFlow standard operations." for aspect in summary.key_aspects)
    content = (
        f"## {dept.title}\n"
        f"Contact: {summary.contact_name} ({summary.contact_email})\n\n"
        f"{aspect_lines}\n"
        + "\n".join(body_lines)
    )
    if feedback:
        content += f"\nRevision note: {feedback}\n"
    content += (
        f"\nOn-time delivery SLA commitment: 96%.\n"
        f"Volume-based discount tier table ({currency}):\n"
        f"| Monthly volume | Discount |\n"
        f"| --- | --- |\n"
        f"| 0-2,499 orders | 0% |\n"
        f"| 2,500-4,999 orders | 3% |\n"
        f"| 5,000+ orders | 5% |\n"
        f"All pricing quoted in {currency} for {metadata.get('client_country', 'US')} operations.\n"
    )
    structured_claims.setdefault("quoted_currency", currency)
    structured_claims.setdefault("ontime_sla_pct", 96)
    return SectionDraft(
        department_id=department_id,
        version=1 if previous_draft is None else previous_draft.version + 1,
        iteration=iteration,
        content=content,
        structured_claims=structured_claims,
    )
