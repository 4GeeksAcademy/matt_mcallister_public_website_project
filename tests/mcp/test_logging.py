"""Invocation logging tests for MCP tools."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

from mcps.company_tools.logging import log_tool_invocation
from mcps.company_tools.errors import IncidentNotFound
from mcps.company_tools.tools import incidents as incident_tools


def test_log_tool_invocation_emits_structured_json(caplog) -> None:
    caplog.set_level(logging.INFO, logger="mcp.company_tools")
    log_tool_invocation(
        client_id="playground-client",
        tool="incidents_get",
        success=True,
    )
    assert caplog.records
    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "mcp_tool_invocation"
    assert payload["client_id"] == "playground-client"
    assert payload["tool"] == "incidents_get"
    assert payload["success"] is True
    assert payload["error_code"] is None


def test_failed_tool_logs_error_code(caplog) -> None:
    caplog.set_level(logging.INFO, logger="mcp.company_tools")

    class _AuthInfo:
        client_id = "test-client"
        scopes = ["incidents:read"]

    with patch(
        "mcps.company_tools.tools.incidents.require_scopes",
        return_value=_AuthInfo(),
    ):
        incident_tools._handle_tool(
            mcp_auth=object(),
            tool_name="incidents_get",
            required_scopes=("incidents:read",),
            action=lambda: (_ for _ in ()).throw(IncidentNotFound("inc_" + "0" * 32)),
        )

    payload = json.loads(caplog.records[-1].message)
    assert payload["success"] is False
    assert payload["error_code"] == "INCIDENT_NOT_FOUND"
