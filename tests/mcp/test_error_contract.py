"""Error contract regression tests for auth, authorization, and validation paths."""

from __future__ import annotations

import json
from unittest.mock import patch

from pydantic import BaseModel, Field

from mcps.company_tools.errors import MCPAuthRequired, MCPForbiddenScope
from mcps.company_tools.tools import incidents as incident_tools


class _InvalidModel(BaseModel):
    title: str = Field(min_length=1)


def _raise_validation_error() -> None:
    _InvalidModel(title="")


def test_auth_required_returns_distinct_code() -> None:
    with patch(
        "mcps.company_tools.tools.incidents.require_scopes",
        side_effect=MCPAuthRequired(),
    ):
        payload = json.loads(
            incident_tools._handle_tool(
                mcp_auth=object(),
                tool_name="incidents_get",
                required_scopes=("incidents:read",),
                action=lambda: {"id": "inc_test"},
            )
        )

    assert payload["ok"] is False
    assert payload["error_code"] == "MCP_AUTH_REQUIRED"


def test_forbidden_scope_returns_distinct_code() -> None:
    with patch(
        "mcps.company_tools.tools.incidents.require_scopes",
        side_effect=MCPForbiddenScope(["incidents:write"]),
    ):
        payload = json.loads(
            incident_tools._handle_tool(
                mcp_auth=object(),
                tool_name="incidents_create",
                required_scopes=("incidents:write",),
                action=lambda: {"id": "inc_test"},
            )
        )

    assert payload["ok"] is False
    assert payload["error_code"] == "MCP_FORBIDDEN_SCOPE"


def test_validation_error_returns_distinct_code() -> None:
    class _AuthInfo:
        client_id = "test-client"
        scopes = ["incidents:write"]

    with patch(
        "mcps.company_tools.tools.incidents.require_scopes",
        return_value=_AuthInfo(),
    ):
        payload = json.loads(
            incident_tools._handle_tool(
                mcp_auth=object(),
                tool_name="incidents_create",
                required_scopes=("incidents:write",),
                action=_raise_validation_error,
            )
        )

    assert payload["ok"] is False
    assert payload["error_code"] == "MCP_VALIDATION_ERROR"
