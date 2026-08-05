"""MCP Auth resource-server configuration using mcpauth (not FastMCP built-in auth)."""

from __future__ import annotations

import os
from typing import Callable, Optional

import jwt
from mcpauth import MCPAuth
from mcpauth.config import AuthServerConfig, AuthServerType, AuthorizationServerMetadata
from mcpauth.types import AuthInfo
from mcpauth.utils import fetch_server_config
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcps.company_tools.errors import MCPAuthRequired, MCPForbiddenScope

SCOPES_SUPPORTED = [
    "incidents:read",
    "incidents:write",
    "inventory:read",
]


def resource_url() -> str:
    explicit = os.environ.get("MCP_RESOURCE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = os.environ.get("MCP_SERVER_HOST", "localhost")
    port = os.environ.get("MCP_SERVER_PORT", "8006")
    return f"http://{host}:{port}/mcp"


def _test_mode_enabled() -> bool:
    return os.environ.get("MCP_AUTH_TEST_MODE", "").lower() in {"1", "true", "yes"}


def _issuer_url() -> str:
    return os.environ.get("MCP_OIDC_ISSUER", "https://test-issuer.local").rstrip("/")


def _build_auth_server_config() -> AuthServerConfig:
    issuer = _issuer_url()
    if _test_mode_enabled():
        return AuthServerConfig(
            type=AuthServerType.OIDC,
            metadata=AuthorizationServerMetadata(
                issuer=issuer,
                authorization_endpoint=f"{issuer}/authorize",
                token_endpoint=f"{issuer}/token",
                jwks_uri=os.environ.get("MCP_JWKS_URI", f"{issuer}/.well-known/jwks.json"),
                response_types_supported=["code"],
                code_challenge_methods_supported=["S256"],
                scope_supported=SCOPES_SUPPORTED,
            ),
        )

    jwks_uri = os.environ.get("MCP_JWKS_URI", "").strip()
    if jwks_uri:
        return AuthServerConfig(
            type=AuthServerType.OIDC,
            metadata=AuthorizationServerMetadata(
                issuer=issuer,
                authorization_endpoint=os.environ.get(
                    "MCP_OIDC_AUTHORIZATION_ENDPOINT", f"{issuer}/authorize"
                ),
                token_endpoint=os.environ.get(
                    "MCP_OIDC_TOKEN_ENDPOINT", f"{issuer}/token"
                ),
                jwks_uri=jwks_uri,
                response_types_supported=["code"],
                code_challenge_methods_supported=["S256"],
                scope_supported=SCOPES_SUPPORTED,
            ),
        )
    return fetch_server_config(issuer=issuer, type=AuthServerType.OIDC)


def build_mcp_auth() -> tuple[MCPAuth, str, AuthServerConfig]:
    resource_id = resource_url()
    auth_server = _build_auth_server_config()
    mcp_auth = MCPAuth(server=auth_server)
    return mcp_auth, resource_id, auth_server


def _parse_scopes(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        return [part for part in raw.split() if part]
    return []


def build_test_token_verifier(
    secret: str,
    *,
    issuer: str,
) -> Callable[[str], AuthInfo]:
    from mcpauth.exceptions import (
        MCPAuthTokenVerificationException,
        MCPAuthTokenVerificationExceptionCode,
    )

    def verify(token: str) -> AuthInfo:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                issuer=issuer,
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise MCPAuthTokenVerificationException(
                MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN,
                cause=exc,
            ) from exc
        scopes = _parse_scopes(payload.get("scope") or payload.get("scopes") or [])
        return AuthInfo(
            token=token,
            issuer=str(payload.get("iss") or issuer),
            subject=str(payload.get("sub") or "test-user"),
            client_id=str(payload.get("client_id") or payload.get("azp") or "test-client"),
            scopes=scopes,
            audience=payload.get("aud"),
            claims=dict(payload),
        )

    return verify


def build_bearer_middleware(mcp_auth: MCPAuth, resource_id: str):
    """Return a Starlette middleware class from mcpauth bearer_auth_middleware."""
    audience = os.environ.get("MCP_AUDIENCE", resource_id)
    if _test_mode_enabled():
        secret = os.environ.get("MCP_TEST_JWT_SECRET") or os.environ.get(
            "SECRET_KEY", "local-development-secret-change-me"
        )
        verify = build_test_token_verifier(secret, issuer=_issuer_url())
        return mcp_auth.bearer_auth_middleware(
            verify,
            audience=audience,
        )

    return mcp_auth.bearer_auth_middleware(
        "jwt",
        audience=audience,
    )


def protected_resource_metadata_route(resource_id: str, auth_server: AuthServerConfig) -> Route:
    async def endpoint(request: Request) -> Response:
        if request.method == "OPTIONS":
            response = Response(status_code=204)
        else:
            response = JSONResponse(
                {
                    "resource": resource_id,
                    "authorization_servers": [auth_server.metadata.issuer],
                    "scopes_supported": SCOPES_SUPPORTED,
                    "bearer_methods_supported": ["header"],
                },
                status_code=200,
            )
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    return Route(
        "/.well-known/oauth-protected-resource/mcp",
        endpoint,
        methods=["GET", "OPTIONS"],
    )


def require_auth_info(mcp_auth: MCPAuth) -> AuthInfo:
    auth_info = mcp_auth.auth_info
    if auth_info is None:
        raise MCPAuthRequired()
    return auth_info


def require_scopes(mcp_auth: MCPAuth, *scopes: str) -> AuthInfo:
    auth_info = require_auth_info(mcp_auth)
    missing = [scope for scope in scopes if scope not in auth_info.scopes]
    if missing:
        raise MCPForbiddenScope(missing)
    return auth_info
