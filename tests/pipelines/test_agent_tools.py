"""Routing evals for MCP ticket tool vs RAG paths in the support agent graph."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest

INCIDENT_API_ROOT = Path(__file__).resolve().parents[2] / "services" / "incident-api"

from agents.mcp.ticket_lookup import lookup_incident_via_mcp
from agents.support_agent.graph import run_agent
from agents.support_agent.trace import clear_traces, get_trace
from agents.tools.incident_lookup import TicketLookupInput


class _TestClientTransport(httpx.BaseTransport):
    """Bridge FastAPI TestClient to httpx for incident-api backed MCP mocks."""

    def __init__(self, test_client) -> None:
        self._test_client = test_client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        response = self._test_client.request(
            request.method,
            path,
            content=request.content,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() not in {"host", "content-length"}
            },
        )
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )


def _return_window_chunks() -> list[dict]:
    return [
        {
            "company": "trackflow",
            "source_document": "returns-policy",
            "section": "Standard return window",
            "language": "en",
            "chunk_index": 0,
            "text": (
                "The standard return window is 30 calendar days from the date of "
                "delivery to the end consumer."
            ),
            "_score": 0.91,
        }
    ]


def _mcp_invoke_from_incident_api(test_client):
    from mcps.company_tools.clients.incidents import IncidentsClient
    from mcps.company_tools.errors import IncidentNotFound

    transport = _TestClientTransport(test_client)
    http_client = httpx.Client(transport=transport, base_url="http://testserver")
    incidents = IncidentsClient(client=http_client, base_url="http://testserver")

    def invoke(tool_name: str, arguments: dict):
        try:
            if tool_name == "incidents_get":
                data = incidents.get_incident(arguments["incident_id"])
                return {"ok": True, "data": data}
            if tool_name == "incidents_list":
                data = incidents.list_incidents(**arguments)
                return {"ok": True, "data": data}
        except IncidentNotFound as exc:
            return {"ok": False, **exc.to_dict()}
        return {"ok": False, "error_code": "MCP_VALIDATION_ERROR", "message": tool_name}

    def lookup(tool_input: TicketLookupInput):
        return lookup_incident_via_mcp(tool_input, invoke_tool=invoke)

    return lookup


@pytest.fixture
def mcp_lookup_via_app(tmp_path, monkeypatch):
    monkeypatch.setenv("INCIDENTS_DB_PATH", str(tmp_path / "incidents.db"))
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://trackflow:trackflow@localhost:5432/trackflow"
    )

    from tests.service_paths import prefer_service_path

    prefer_service_path("incident-api")
    from fastapi.testclient import TestClient
    from app.main import app

    test_client = TestClient(app)
    lookup_fn = _mcp_invoke_from_incident_api(test_client)

    created = test_client.post(
        "/api/incidents",
        json={
            "title": "Delayed carrier scan",
            "description": "No scan reported for twelve hours.",
            "category": "carrier_issue",
            "status": "open",
            "origin": "customer",
            "branch": "la_office",
        },
    )
    assert created.status_code == 201
    incident_id = created.json()["data"]["id"]
    return lookup_fn, incident_id


def test_eval_routes_ticket_question_to_mcp_tool(mcp_lookup_via_app) -> None:
    """Tool-routed question uses MCP-backed ticket lookup."""
    lookup_fn, incident_id = mcp_lookup_via_app
    clear_traces()

    result = run_agent(
        f"What is the status of incident {incident_id}?",
        lookup_fn=lookup_fn,
    )

    trace = get_trace(result["trace_id"])
    node_names = [entry["node"] for entry in trace]
    assert "classify_route" in node_names
    assert "mcp_ticket_lookup_node" in node_names
    assert "format_ticket_answer" in node_names
    assert "retrieve_node" not in node_names
    assert "generate_node" not in node_names
    assert result["sources_used"] == ["mcp_ticket_tool"]
    assert "open" in result["answer"].casefold()
    assert incident_id in result["answer"]


def test_eval_routes_policy_question_to_rag() -> None:
    """Policy questions stay on the RAG path without invoking the ticket tool."""
    clear_traces()

    def fake_retrieve(_question: str, **_kwargs) -> list[dict]:
        return _return_window_chunks()

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        "The standard return window is 30 calendar days from "
                        "delivery to the end consumer."
                    )
                )
            )
        ]
    )

    result = run_agent(
        "What is the standard return window for eligible products?",
        retrieve_fn=fake_retrieve,
        openai_client=mock_openai,
    )

    trace = get_trace(result["trace_id"])
    node_names = [entry["node"] for entry in trace]
    assert "classify_route" in node_names
    assert "retrieve_node" in node_names
    assert "generate_node" in node_names
    assert "mcp_ticket_lookup_node" not in node_names
    assert result["sources_used"] == ["rag"]


def test_eval_ticket_fallback_on_not_found(mcp_lookup_via_app) -> None:
    """Missing ticket IDs return an honest fallback without inventing status."""
    lookup_fn, _incident_id = mcp_lookup_via_app
    clear_traces()

    missing_id = "inc_" + ("0" * 32)
    result = run_agent(
        f"What is the status of incident {missing_id}?",
        lookup_fn=lookup_fn,
    )

    assert "couldn't find an incident" in result["answer"].casefold()
    assert result["sources_used"] == ["mcp_ticket_tool"]
    trace = get_trace(result["trace_id"])
    ticket_step = next(
        entry for entry in trace if entry["node"] == "mcp_ticket_lookup_node"
    )
    assert ticket_step["output_summary"]["ok"] is False
    assert ticket_step["output_summary"]["error_code"] == "not_found"


def test_eval_ticket_fallback_on_timeout(mcp_lookup_via_app) -> None:
    """Timeouts surface a user-safe message instead of fabricated ticket data."""
    _lookup_fn, incident_id = mcp_lookup_via_app
    clear_traces()

    def timeout_lookup(tool_input: TicketLookupInput):
        def invoke(_tool_name: str, _arguments: dict):
            raise httpx.TimeoutException("timed out")

        return lookup_incident_via_mcp(tool_input, invoke_tool=invoke)

    result = run_agent(
        f"What is the status of incident {incident_id}?",
        lookup_fn=timeout_lookup,
    )

    assert "couldn't confirm that ticket's status" in result["answer"].casefold()
    assert incident_id not in result["answer"]
