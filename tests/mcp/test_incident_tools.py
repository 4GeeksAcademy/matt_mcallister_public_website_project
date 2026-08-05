"""Incident MCP tool integration tests against the real incident-api."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

INCIDENT_API_ROOT = Path(__file__).resolve().parents[2] / "services" / "incident-api"

from mcps.company_tools.clients.incidents import IncidentsClient
from mcps.company_tools.errors import IncidentStatusTransitionInvalid
from mcps.company_tools.tools import incidents as incident_tools


class _TestClientTransport(httpx.BaseTransport):
    def __init__(self, test_client: TestClient) -> None:
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


@pytest.fixture
def incidents_client(tmp_path, monkeypatch):
    monkeypatch.setenv("INCIDENTS_DB_PATH", str(tmp_path / "incidents.db"))
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://trackflow:trackflow@localhost:5432/trackflow"
    )

    from tests.service_paths import prefer_service_path

    prefer_service_path("incident-api")
    from app.main import app

    test_client = TestClient(app)
    transport = _TestClientTransport(test_client)
    http_client = httpx.Client(transport=transport, base_url="http://testserver")
    return IncidentsClient(client=http_client, base_url="http://testserver"), test_client


def test_incident_create_get_and_status_update(incidents_client) -> None:
    client, _test_client = incidents_client
    created = client.create_incident(
        {
            "title": "MCP carrier delay",
            "description": "Created through MCP client test.",
            "category": "carrier_issue",
            "status": "open",
            "origin": "customer",
            "branch": "la_office",
        }
    )
    incident_id = created["id"]

    fetched = client.get_incident(incident_id)
    assert fetched["status"] == "open"

    updated = client.update_status(incident_id, "in_progress")
    assert updated["status"] == "in_progress"


def test_incident_status_update_uses_status_endpoint(incidents_client) -> None:
    client, test_client = incidents_client
    created = client.create_incident(
        {
            "title": "Status endpoint check",
            "description": "Verify PATCH /status path.",
            "category": "carrier_issue",
            "status": "open",
            "origin": "customer",
            "branch": "la_office",
        }
    )
    incident_id = created["id"]

    response = test_client.patch(
        f"/api/incidents/{incident_id}/status",
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "in_progress"

    with pytest.raises(IncidentStatusTransitionInvalid):
        client.update_status(incident_id, "open")


def test_incident_tool_json_reports_not_found(incidents_client, mcp_test_env) -> None:
    client, _ = incidents_client
    missing_id = "inc_" + ("f" * 32)

    class _AuthInfo:
        client_id = "test-client"
        scopes = ["incidents:read"]

    with patch(
        "mcps.company_tools.tools.incidents.require_scopes",
        return_value=_AuthInfo(),
    ):
        payload = json.loads(
            incident_tools._handle_tool(
                mcp_auth=object(),
                tool_name="incidents_get",
                required_scopes=("incidents:read",),
                action=lambda: client.get_incident(missing_id),
            )
        )
    assert payload["ok"] is False
    assert payload["error_code"] == "INCIDENT_NOT_FOUND"
