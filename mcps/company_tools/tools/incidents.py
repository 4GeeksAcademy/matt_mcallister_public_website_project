"""Incident manager MCP tools backed by the real incident-api."""

import json
from typing import Any, Callable, Optional

from mcp.server.fastmcp import FastMCP
from mcpauth import MCPAuth
from pydantic import BaseModel, Field
from mcps.company_tools.auth import require_scopes
from mcps.company_tools.clients.incidents import IncidentsClient
from mcps.company_tools.errors import MCPToolError
from mcps.company_tools.logging import log_tool_invocation


class IncidentCreateInput(BaseModel):
    title: str = Field(min_length=1, max_length=120, description="Short incident title.")
    description: str = Field(
        min_length=1,
        max_length=5000,
        description="Detailed incident description.",
    )
    category: str = Field(description="Incident category from the TrackFlow domain.")
    status: str = Field(description="Initial status, typically open.")
    origin: str = Field(description="Incident origin (customer, branch, internal).")
    branch: str = Field(description="TrackFlow branch identifier.")


class IncidentGetInput(BaseModel):
    incident_id: str = Field(description="Incident identifier, e.g. inc_abc123...")


class IncidentListInput(BaseModel):
    status: Optional[str] = Field(default=None, description="Filter by status.")
    category: Optional[str] = Field(default=None, description="Filter by category.")
    origin: Optional[str] = Field(default=None, description="Filter by origin.")
    branch: Optional[str] = Field(default=None, description="Filter by branch.")


class IncidentUpdateStatusInput(BaseModel):
    incident_id: str = Field(description="Incident identifier to update.")
    status: str = Field(description="Target status using the lifecycle endpoint.")


def _client_id(mcp_auth: MCPAuth) -> str:
    auth_info = mcp_auth.auth_info
    return auth_info.client_id if auth_info else "unknown"


def _tool_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def _handle_tool(
    *,
    mcp_auth: MCPAuth,
    tool_name: str,
    required_scopes: tuple[str, ...],
    action: Callable[[], Any],
) -> str:
    client_id = "unknown"
    try:
        auth_info = require_scopes(mcp_auth, *required_scopes)
        client_id = auth_info.client_id
        result = action()
        log_tool_invocation(
            client_id=client_id,
            tool=tool_name,
            success=True,
        )
        return _tool_response({"ok": True, "data": result})
    except MCPToolError as exc:
        log_tool_invocation(
            client_id=client_id,
            tool=tool_name,
            success=False,
            error_code=exc.code,
        )
        return _tool_response({"ok": False, **exc.to_dict()})
    except Exception as exc:  # pragma: no cover - defensive guardrail
        log_tool_invocation(
            client_id=client_id,
            tool=tool_name,
            success=False,
            error_code="BACKEND_UNAVAILABLE",
        )
        return _tool_response(
            {
                "ok": False,
                "error_code": "BACKEND_UNAVAILABLE",
                "message": str(exc),
            }
        )


def register_tools(mcp: FastMCP, mcp_auth: MCPAuth) -> None:
    @mcp.tool(
        name="incidents_create",
        description=(
            "Create a new incident ticket in the TrackFlow Incidents Manager. "
            "Requires scope incidents:write."
        ),
    )
    def incidents_create(
        title: str,
        description: str,
        category: str,
        status: str,
        origin: str,
        branch: str,
    ) -> str:
        payload = IncidentCreateInput(
            title=title,
            description=description,
            category=category,
            status=status,
            origin=origin,
            branch=branch,
        )

        def action() -> dict[str, Any]:
            with IncidentsClient() as client:
                return client.create_incident(payload.model_dump())

        return _handle_tool(
            mcp_auth=mcp_auth,
            tool_name="incidents_create",
            required_scopes=("incidents:write",),
            action=action,
        )

    @mcp.tool(
        name="incidents_get",
        description=(
            "Fetch one incident by ID, including its current status. "
            "Requires scope incidents:read."
        ),
    )
    def incidents_get(incident_id: str) -> str:
        payload = IncidentGetInput(incident_id=incident_id)

        def action() -> dict[str, Any]:
            with IncidentsClient() as client:
                return client.get_incident(payload.incident_id)

        return _handle_tool(
            mcp_auth=mcp_auth,
            tool_name="incidents_get",
            required_scopes=("incidents:read",),
            action=action,
        )

    @mcp.tool(
        name="incidents_list",
        description=(
            "List incidents with optional filters for status, category, origin, and branch. "
            "Requires scope incidents:read."
        ),
    )
    def incidents_list(
        status: Optional[str] = None,
        category: Optional[str] = None,
        origin: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> str:
        payload = IncidentListInput(
            status=status,
            category=category,
            origin=origin,
            branch=branch,
        )

        def action() -> list[dict[str, Any]]:
            with IncidentsClient() as client:
                return client.list_incidents(**payload.model_dump(exclude_none=True))

        return _handle_tool(
            mcp_auth=mcp_auth,
            tool_name="incidents_list",
            required_scopes=("incidents:read",),
            action=action,
        )

    @mcp.tool(
        name="incidents_update_status",
        description=(
            "Update an incident status through PATCH /api/incidents/{id}/status. "
            "Requires scope incidents:write."
        ),
    )
    def incidents_update_status(incident_id: str, status: str) -> str:
        payload = IncidentUpdateStatusInput(incident_id=incident_id, status=status)

        def action() -> dict[str, Any]:
            with IncidentsClient() as client:
                return client.update_status(payload.incident_id, payload.status)

        return _handle_tool(
            mcp_auth=mcp_auth,
            tool_name="incidents_update_status",
            required_scopes=("incidents:write",),
            action=action,
        )
