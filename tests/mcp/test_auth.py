"""Authentication and protected-resource metadata tests for the MCP server."""

from __future__ import annotations

import importlib

import pytest
from starlette.testclient import TestClient

from tests.mcp.conftest import TEST_AUDIENCE, make_test_token


@pytest.fixture
def mcp_client(mcp_test_env) -> TestClient:
    import mcps.company_tools.server as server_module

    importlib.reload(server_module)
    with TestClient(server_module.create_app()) as client:
        yield client


def test_protected_resource_metadata_is_public(mcp_client: TestClient) -> None:
    response = mcp_client.get("/.well-known/oauth-protected-resource/mcp")
    assert response.status_code == 200
    body = response.json()
    assert body["resource"] == TEST_AUDIENCE
    assert "authorization_servers" in body
    assert "incidents:read" in body.get("scopes_supported", [])


def test_mcp_endpoint_requires_bearer_token(mcp_client: TestClient) -> None:
    response = mcp_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert response.status_code == 401
    body = response.json()
    assert body.get("error") or body.get("error_code") or "invalid" in str(body).lower()


def test_invalid_bearer_token_is_rejected(mcp_client: TestClient) -> None:
    response = mcp_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_valid_token_allows_mcp_session(auth_headers: dict[str, str], mcp_client: TestClient) -> None:
    response = mcp_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        headers={
            **auth_headers,
            "Host": "testserver",
        },
    )
    assert response.status_code != 401
