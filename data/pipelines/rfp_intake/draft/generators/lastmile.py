"""Last Mile and Carrier Management section generator."""

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
    monthly_volume = metadata.get("monthly_volume") or 5000
    currency = metadata.get("currency", "USD")
    body = [
        "Carrier coverage includes UPS, FedEx, and DHL for domestic lanes.",
        f"Cost per shipment is quoted as a final client rate in {currency} (carrier negotiated rates are not disclosed).",
        f"Quoted monthly shipment volume: {monthly_volume} orders/month.",
    ]
    claims: dict[str, Any] = {
        "monthly_volume": monthly_volume,
        "quoted_currency": currency,
    }
    return _base_draft(
        department_id="lastmile",
        summary=summary,
        metadata=metadata,
        previous_draft=previous_draft,
        feedback=feedback,
        body_lines=body,
        structured_claims=claims,
    )
