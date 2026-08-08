"""Deterministic arbitration for structured CONTEXT conflicts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from data.pipelines.rfp_intake.context_config import ARBITRATION_RULES, COUNTRY_CURRENCY, DEPARTMENT_BY_ID


@dataclass(frozen=True)
class ArbitrationDecision:
    conflict_type: str
    arbiter: str
    resolution: str
    winning_department_id: str
    details: str


def detect_structured_conflicts(
    claims_by_department: dict[str, dict[str, Any]],
    *,
    draft_contents: dict[str, str] | None = None,
    client_country: str = "",
) -> list[str]:
    conflicts: list[str] = []
    draft_contents = draft_contents or {}

    warehouse_claims = claims_by_department.get("warehouse", {})
    lastmile_claims = claims_by_department.get("lastmile", {})
    warehouse_capacity = warehouse_claims.get("warehouse_capacity_units")
    lastmile_volume = lastmile_claims.get("monthly_volume")
    if warehouse_capacity is not None and lastmile_volume is not None:
        if lastmile_volume > warehouse_capacity:
            conflicts.append("volume-vs-capacity")

    combined_text = " ".join(draft_contents.values())
    if re.search(
        r"(?i)(returns?\s+(processing|turnaround).{0,60}under\s+48\s*hours?|"
        r"under\s+48\s*hours?.{0,20}returns?)",
        combined_text,
    ):
        conflicts.append("returns-sla-breach")

    currencies = {
        claims.get("quoted_currency")
        for claims in claims_by_department.values()
        if claims.get("quoted_currency")
    }
    expected = COUNTRY_CURRENCY.get(client_country)
    if len(currencies) > 1:
        conflicts.append("currency-mismatch")
    elif expected and currencies and expected not in currencies:
        conflicts.append("currency-mismatch")

    return conflicts


def resolve_conflict(conflict_type: str) -> ArbitrationDecision:
    rule = ARBITRATION_RULES[conflict_type]
    winning_department_id = "warehouse"
    if conflict_type == "returns-sla-breach":
        winning_department_id = "reverse"
    dept = DEPARTMENT_BY_ID[winning_department_id]
    return ArbitrationDecision(
        conflict_type=conflict_type,
        arbiter=rule["arbiter"],
        resolution=rule["resolution"],
        winning_department_id=winning_department_id,
        details=f"{dept.contact_name} ({rule['arbiter']}) resolved {conflict_type} via {rule['resolution']}.",
    )
