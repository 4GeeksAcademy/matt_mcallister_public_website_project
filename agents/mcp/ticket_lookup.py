"""Ticket lookup via MCP company tools (no direct incident-api HTTP from the agent)."""

from __future__ import annotations

import time
from typing import Any, Optional

from agents.mcp.client import invoke_company_tool_sync
from agents.tools.incident_lookup import (
    MSG_EMPTY_LIST,
    MSG_MISSING_ID,
    MSG_NOT_FOUND,
    MSG_UNAVAILABLE,
    IncidentSummary,
    TicketLookupInput,
    TicketLookupResult,
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


def _map_mcp_error(result: dict[str, Any]) -> TicketLookupResult:
    code = str(result.get("error_code") or "unavailable")
    if code == "INCIDENT_NOT_FOUND":
        return TicketLookupResult(
            ok=False,
            error_code="not_found",
            error_message=MSG_NOT_FOUND,
            http_method="MCP",
            http_path="incidents_get",
        )
    if code in {"MCP_AUTH_REQUIRED", "MCP_FORBIDDEN_SCOPE"}:
        return TicketLookupResult(
            ok=False,
            error_code="auth_error",
            error_message=MSG_UNAVAILABLE,
            http_method="MCP",
            http_path="company_tools",
        )
    return TicketLookupResult(
        ok=False,
        error_code="unavailable",
        error_message=MSG_UNAVAILABLE,
        http_method="MCP",
        http_path="company_tools",
    )


def lookup_incident_via_mcp(
    tool_input: TicketLookupInput,
    *,
    invoke_tool: Optional[Any] = None,
) -> TicketLookupResult:
    """Query incidents through MCP tools loaded via langchain-mcp-adapters."""
    invoke = invoke_tool or invoke_company_tool_sync
    started = time.perf_counter()

    if tool_input.incident_id:
        try:
            raw = invoke("incidents_get", {"incident_id": tool_input.incident_id})
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return TicketLookupResult(
                ok=False,
                error_code="timeout",
                error_message=MSG_UNAVAILABLE,
                http_method="MCP",
                http_path="incidents_get",
                duration_ms=duration_ms,
            )
        duration_ms = int((time.perf_counter() - started) * 1000)
        if not raw.get("ok"):
            mapped = _map_mcp_error(raw)
            mapped.duration_ms = duration_ms
            return mapped
        payload = raw.get("data")
        if not payload:
            return TicketLookupResult(
                ok=False,
                error_code="unavailable",
                error_message=MSG_UNAVAILABLE,
                http_method="MCP",
                http_path="incidents_get",
                duration_ms=duration_ms,
            )
        return TicketLookupResult(
            ok=True,
            incidents=[_summary_from_payload(payload)],
            http_method="MCP",
            http_path="incidents_get",
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
            http_method="MCP",
            http_path="incidents_list",
        )

    params = {
        key: value
        for key, value in tool_input.model_dump().items()
        if key != "incident_id" and value
    }
    try:
        raw = invoke("incidents_list", params)
    except Exception:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return TicketLookupResult(
            ok=False,
            error_code="timeout",
            error_message=MSG_UNAVAILABLE,
            http_method="MCP",
            http_path="incidents_list",
            duration_ms=duration_ms,
        )
    duration_ms = int((time.perf_counter() - started) * 1000)
    if not raw.get("ok"):
        mapped = _map_mcp_error(raw)
        mapped.duration_ms = duration_ms
        return mapped

    rows = raw.get("data") or []
    if not rows:
        return TicketLookupResult(
            ok=False,
            error_code="empty_list",
            error_message=MSG_EMPTY_LIST,
            http_method="MCP",
            http_path="incidents_list",
            duration_ms=duration_ms,
        )
    return TicketLookupResult(
        ok=True,
        incidents=[_summary_from_payload(row) for row in rows],
        http_method="MCP",
        http_path="incidents_list",
        duration_ms=duration_ms,
    )
