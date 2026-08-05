"""HTTP client for incident ticket lookup against the real incident manager API."""

from __future__ import annotations

import os
import re
import time
from typing import Any, Optional

import httpx
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

DEFAULT_BASE_URL = "http://localhost:8001"
DEFAULT_TIMEOUT_SECONDS = 5.0

MSG_TIMEOUT = (
    "I couldn't confirm that ticket's status right now. Please try again shortly."
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


def _base_url(value: Optional[str] = None) -> str:
    return (value or os.environ.get("INCIDENTS_API_URL", DEFAULT_BASE_URL)).rstrip("/")


def _timeout(value: Optional[float] = None) -> float:
    if value is not None:
        return value
    raw = os.environ.get("INCIDENT_TOOL_TIMEOUT_SECONDS")
    if raw:
        return float(raw)
    return DEFAULT_TIMEOUT_SECONDS


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


def _summary_from_payload(payload: dict[str, Any]) -> IncidentSummary:
    return IncidentSummary(
        id=str(payload["id"]),
        title=str(payload["title"]),
        status=str(payload["status"]),
        category=str(payload["category"]),
        origin=str(payload["origin"]),
        branch=str(payload["branch"]),
        created_at=str(payload["created_at"]),
        updated_at=str(payload["updated_at"]),
    )


def lookup_incident(
    tool_input: TicketLookupInput,
    *,
    client: Optional[httpx.Client] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
) -> TicketLookupResult:
    """Query the incident manager over HTTP; never simulate incident rows."""
    base = _base_url(base_url)
    timeout_seconds = _timeout(timeout)
    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout_seconds)

    try:
        if tool_input.incident_id:
            path = f"/api/incidents/{tool_input.incident_id}"
            started = time.perf_counter()
            response = http_client.get(f"{base}{path}")
            duration_ms = int((time.perf_counter() - started) * 1000)
            if response.status_code == 404:
                return TicketLookupResult(
                    ok=False,
                    error_code="not_found",
                    error_message=MSG_NOT_FOUND,
                    http_method="GET",
                    http_path=path,
                    duration_ms=duration_ms,
                )
            if response.status_code >= 400:
                return TicketLookupResult(
                    ok=False,
                    error_code="http_error",
                    error_message=MSG_UNAVAILABLE,
                    http_method="GET",
                    http_path=path,
                    duration_ms=duration_ms,
                )
            payload = response.json().get("data")
            if not payload:
                return TicketLookupResult(
                    ok=False,
                    error_code="http_error",
                    error_message=MSG_UNAVAILABLE,
                    http_method="GET",
                    http_path=path,
                    duration_ms=duration_ms,
                )
            return TicketLookupResult(
                ok=True,
                incidents=[_summary_from_payload(payload)],
                http_method="GET",
                http_path=path,
                duration_ms=duration_ms,
            )

        if not any(
            (
                tool_input.status,
                tool_input.category,
                tool_input.origin,
                tool_input.branch,
            )
        ):
            return TicketLookupResult(
                ok=False,
                error_code="missing_id",
                error_message=MSG_MISSING_ID,
            )

        params = {
            key: value
            for key, value in tool_input.model_dump().items()
            if key != "incident_id" and value
        }
        path = "/api/incidents"
        started = time.perf_counter()
        response = http_client.get(f"{base}{path}", params=params)
        duration_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            return TicketLookupResult(
                ok=False,
                error_code="http_error",
                error_message=MSG_UNAVAILABLE,
                http_method="GET",
                http_path=path,
                duration_ms=duration_ms,
            )
        rows = response.json().get("data") or []
        if not rows:
            return TicketLookupResult(
                ok=False,
                error_code="empty_list",
                error_message=MSG_EMPTY_LIST,
                http_method="GET",
                http_path=path,
                duration_ms=duration_ms,
            )
        return TicketLookupResult(
            ok=True,
            incidents=[_summary_from_payload(row) for row in rows],
            http_method="GET",
            http_path=path,
            duration_ms=duration_ms,
        )
    except httpx.TimeoutException:
        return TicketLookupResult(
            ok=False,
            error_code="timeout",
            error_message=MSG_TIMEOUT,
            http_method="GET",
            http_path=(
                f"/api/incidents/{tool_input.incident_id}"
                if tool_input.incident_id
                else "/api/incidents"
            ),
        )
    except httpx.HTTPError:
        return TicketLookupResult(
            ok=False,
            error_code="unavailable",
            error_message=MSG_UNAVAILABLE,
            http_method="GET",
            http_path=(
                f"/api/incidents/{tool_input.incident_id}"
                if tool_input.incident_id
                else "/api/incidents"
            ),
        )
    finally:
        if owns_client:
            http_client.close()


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
