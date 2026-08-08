"""Warehouse Operations section generator."""

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
    monthly_volume = metadata.get("monthly_volume")
    capacity_units = 4000 if monthly_volume and monthly_volume <= 4000 else 6000
    body = [
        "TrackFlow will provide pallet and SKU storage aligned to the requested scope.",
        f"Committed warehouse capacity: {capacity_units} order-equivalent units per month.",
    ]
    if monthly_volume is None:
        body.append("Open question: monthly volume was not stated in the RFP.")
    claims: dict[str, Any] = {
        "warehouse_capacity_units": capacity_units,
        "monthly_volume_assumed": monthly_volume or capacity_units,
    }
    return _base_draft(
        department_id="warehouse",
        summary=summary,
        metadata=metadata,
        previous_draft=previous_draft,
        feedback=feedback,
        body_lines=body,
        structured_claims=claims,
    )
