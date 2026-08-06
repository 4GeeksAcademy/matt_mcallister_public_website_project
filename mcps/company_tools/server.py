"""TrackFlow company-tools MCP server entrypoint."""

from __future__ import annotations

import contextlib
import logging
import os

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

from mcps.company_tools.auth import (
    build_bearer_middleware,
    build_mcp_auth,
    protected_resource_metadata_route,
)
from mcps.company_tools.tools import incidents, inventory

logging.basicConfig(level=os.environ.get("MCP_LOG_LEVEL", "INFO"))

mcp = FastMCP(name="TrackFlow Company Tools", stateless_http=True)
_mcp_auth, _resource_id, _auth_server = build_mcp_auth()
incidents.register_tools(mcp, _mcp_auth)
inventory.register_tools(mcp, _mcp_auth)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with mcp.session_manager.run():
        yield


def create_app() -> Starlette:
    bearer_mw = build_bearer_middleware(_mcp_auth, _resource_id)
    return Starlette(
        routes=[
            protected_resource_metadata_route(_resource_id, _auth_server),
            Mount(
                "/",
                app=mcp.streamable_http_app(),
                middleware=[Middleware(bearer_mw)],
            ),
        ],
        lifespan=lifespan,
    )


app = create_app()
