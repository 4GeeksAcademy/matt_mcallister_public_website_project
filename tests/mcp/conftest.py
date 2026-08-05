"""Shared fixtures for MCP server tests."""

from __future__ import annotations

import os
import time
from typing import Iterable

import jwt
import pytest

TEST_ISSUER = "https://test-issuer.local"
TEST_AUDIENCE = "http://testserver/mcp"
TEST_SECRET = "test-mcp-secret"


@pytest.fixture(autouse=True)
def mcp_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TEST_MODE", "1")
    monkeypatch.setenv("MCP_OIDC_ISSUER", TEST_ISSUER)
    monkeypatch.setenv("MCP_RESOURCE_URL", TEST_AUDIENCE)
    monkeypatch.setenv("MCP_AUDIENCE", TEST_AUDIENCE)
    monkeypatch.setenv("MCP_TEST_JWT_SECRET", TEST_SECRET)
    monkeypatch.setenv("MCP_SERVER_HOST", "testserver")
    monkeypatch.setenv("MCP_SERVER_PORT", "8006")


def make_test_token(
    scopes: Iterable[str],
    *,
    secret: str = TEST_SECRET,
    issuer: str = TEST_ISSUER,
    audience: str = TEST_AUDIENCE,
    client_id: str = "playground-client",
) -> str:
    return jwt.encode(
        {
            "iss": issuer,
            "sub": "eval-user-1",
            "client_id": client_id,
            "scope": " ".join(scopes),
            "aud": audience,
            "exp": int(time.time()) + 3600,
        },
        secret,
        algorithm="HS256",
    )


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = make_test_token(
        ["incidents:read", "incidents:write", "inventory:read"]
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def read_only_headers() -> dict[str, str]:
    token = make_test_token(["incidents:read"])
    return {"Authorization": f"Bearer {token}"}
