"""Inventory MCP tools: read-only listing plus explicit write rejection."""

import json
from typing import Any, Literal, Optional

from mcp.server.fastmcp import FastMCP
from mcpauth import MCPAuth
from pydantic import BaseModel, Field

from mcps.company_tools.auth import require_scopes
from mcps.company_tools.clients.inventory import InventoryClient
from mcps.company_tools.errors import InventoryWriteForbidden, MCPToolError
from mcps.company_tools.logging import log_tool_invocation


class InventoryCreateProductInput(BaseModel):
    name: str = Field(description="Product display name.")
    sku: str = Field(description="Unique SKU.")
    warehouse_location: Literal["los_angeles", "zaragoza"] = Field(
        description="Warehouse location code."
    )
    client_brand: str = Field(description="Client brand associated with the product.")
    low_stock_threshold: int = Field(
        default=10,
        ge=0,
        description="Low stock alert threshold.",
    )


def _tool_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def register_tools(mcp: FastMCP, mcp_auth: MCPAuth) -> None:
    @mcp.tool(
        name="inventory_list_products",
        description=(
            "Read-only inventory query that lists products from GET /inventory/products. "
            "Requires scope inventory:read."
        ),
    )
    def inventory_list_products() -> str:
        client_id = "unknown"

        def action() -> list[dict[str, Any]]:
            with InventoryClient() as client:
                return client.list_products()

        try:
            auth_info = require_scopes(mcp_auth, "inventory:read")
            client_id = auth_info.client_id
            data = action()
            log_tool_invocation(
                client_id=client_id,
                tool="inventory_list_products",
                success=True,
            )
            return _tool_response({"ok": True, "data": data})
        except MCPToolError as exc:
            log_tool_invocation(
                client_id=client_id,
                tool="inventory_list_products",
                success=False,
                error_code=exc.code,
            )
            return _tool_response({"ok": False, **exc.to_dict()})

    @mcp.tool(
        name="inventory_create_product",
        description=(
            "Attempt to create a product. This MCP server explicitly rejects all inventory "
            "write operations with INVENTORY_WRITE_FORBIDDEN."
        ),
    )
    def inventory_create_product(
        name: str,
        sku: str,
        warehouse_location: Literal["los_angeles", "zaragoza"],
        client_brand: str,
        low_stock_threshold: int = 10,
    ) -> str:
        _ = InventoryCreateProductInput(
            name=name,
            sku=sku,
            warehouse_location=warehouse_location,
            client_brand=client_brand,
            low_stock_threshold=low_stock_threshold,
        )
        client_id = "unknown"
        try:
            auth_info = require_scopes(mcp_auth, "inventory:read")
            client_id = auth_info.client_id
            raise InventoryWriteForbidden()
        except MCPToolError as exc:
            log_tool_invocation(
                client_id=client_id,
                tool="inventory_create_product",
                success=False,
                error_code=exc.code,
            )
            return _tool_response({"ok": False, **exc.to_dict()})
