"""
Routing helpers and typed contracts for ticket questions.

Direct HTTP access to the Incidents Manager is deprecated. Ticket lookups must
go through the MCP company-tools server via agents.mcp.ticket_lookup.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel, Field

INCIDENT_ID_PATTERN = re.compile(r"\b(inc_[a-f0-9]{32})\b", re.IGNORECASE)
TICKET_KEYWORDS = (
    "incident",
    "ticket",
    "inc_",
    "status of",
    "open incidents",
    "list incidents",
    "carrier issue",
    "carrier incidents",
)

MSG_NOT_FOUND = "I couldn't find an incident with that ID."
MSG_EMPTY_LIST = "No incidents matched those filters."
MSG_MISSING_ID = (
    "Please provide an incident ID (inc_…) so I can look up that ticket."
)
MSG_UNAVAILABLE = (
    "I couldn't confirm that ticket's status right now. Please try again shortly."
)


class TicketLookupInput(BaseModel):
    incident_id: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    origin: Optional[str] = None
    branch: Optional[str] = None


class IncidentSummary(BaseModel):
    id: str
    title: str
    status: str
    category: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class TicketLookupResult(BaseModel):
    ok: bool
    incidents: list[IncidentSummary] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    duration_ms: Optional[int] = None


def classify_question_route(question: str) -> tuple[str, dict[str, Any]]:
    """Return route name and routing signals for trace metadata."""
    lowered = question.casefold()
    incident_match = INCIDENT_ID_PATTERN.search(question)
    matched_keywords = [kw for kw in TICKET_KEYWORDS if kw in lowered]
    if incident_match or matched_keywords:
        return "ticket", {
            "matched_incident_id": incident_match.group(1) if incident_match else None,
            "matched_keywords": matched_keywords,
        }
    return "knowledge", {"matched_incident_id": None, "matched_keywords": []}


def parse_ticket_intent(question: str) -> TicketLookupInput:
    """Build typed tool input from a natural-language ticket question."""
    incident_match = INCIDENT_ID_PATTERN.search(question)
    lowered = question.casefold()

    status = None
    for candidate in ("open", "in_progress", "resolved", "discarded"):
        if candidate.replace("_", " ") in lowered or candidate in lowered:
            status = candidate
            break

    category = None
    for candidate in (
        "lost_parcel",
        "delivery_failure",
        "carrier_issue",
        "returns_issue",
        "inventory_discrepancy",
        "warehouse_incident",
        "system_failure",
        "client_complaint",
        "other",
    ):
        token = candidate.replace("_", " ")
        if token in lowered or candidate in lowered:
            category = candidate
            break

    return TicketLookupInput(
        incident_id=incident_match.group(1) if incident_match else None,
        status=status,
        category=category,
    )


def format_ticket_answer(result: TicketLookupResult) -> str:
    """Build a user-facing answer from real tool output only."""
    if not result.ok:
        return result.error_message or MSG_UNAVAILABLE

    if len(result.incidents) == 1:
        incident = result.incidents[0]
        return (
            f"Incident {incident.id} ({incident.title}) is currently {incident.status} "
            f"(category: {incident.category}, branch: {incident.branch}, "
            f"origin: {incident.origin})."
        )

    lines = [
        (
            f"- {incident.id}: {incident.title} — status {incident.status}, "
            f"category {incident.category}, branch {incident.branch}"
        )
        for incident in result.incidents[:10]
    ]
    suffix = ""
    if len(result.incidents) > 10:
        suffix = f" Showing 10 of {len(result.incidents)} matching incidents."
    return "Matching incidents:\n" + "\n".join(lines) + suffix
