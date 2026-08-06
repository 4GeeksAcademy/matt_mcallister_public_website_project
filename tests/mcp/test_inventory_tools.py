"""Inventory MCP tool tests including explicit write rejection."""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

from mcps.company_tools.clients.inventory import InventoryClient
from mcps.company_tools.errors import BackendUnavailable
from mcps.company_tools.tools import inventory as inventory_tools


def test_inventory_list_products_via_client() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": 1,
            "name": "MCP Test SKU",
            "sku": "MCP-001",
            "warehouse_location": "los_angeles",
            "client_brand": "TrackFlow",
            "low_stock_threshold": 10,
            "current_stock": 5,
        }
    ]
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    client = InventoryClient(
        client=mock_client,
        base_url="http://testserver",
        service_token="test-token",
    )
    listed = client.list_products()
    assert listed[0]["sku"] == "MCP-001"
    mock_client.get.assert_called_once()
    assert mock_client.get.call_args.kwargs["headers"]["Authorization"] == "Bearer test-token"


def test_inventory_list_products_requires_service_token(monkeypatch) -> None:
    monkeypatch.delenv("INVENTORY_SERVICE_TOKEN", raising=False)
    client = InventoryClient(client=MagicMock(), service_token="")
    try:
        client.list_products()
    except BackendUnavailable as exc:
        assert exc.code == "BACKEND_UNAVAILABLE"
    else:
        raise AssertionError("Expected BACKEND_UNAVAILABLE when token missing")


def test_inventory_create_product_is_forbidden(mcp_test_env) -> None:
    class _AuthInfo:
        client_id = "playground-client"
        scopes = ["inventory:read"]

    with patch(
        "mcps.company_tools.tools.inventory.require_scopes",
        return_value=_AuthInfo(),
    ):
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        inventory_tools.register_tools(mcp, object())
        tool_fn = mcp._tool_manager._tools["inventory_create_product"].fn
        payload = json.loads(
            tool_fn(
                name="Blocked Product",
                sku="BLOCK-001",
                warehouse_location="los_angeles",
                client_brand="TrackFlow",
            )
        )

    assert payload["ok"] is False
    assert payload["error_code"] == "INVENTORY_WRITE_FORBIDDEN"


def test_inventory_create_product_invalid_input_returns_validation_error(mcp_test_env) -> None:
    class _AuthInfo:
        client_id = "playground-client"
        scopes = ["inventory:read"]

    with patch(
        "mcps.company_tools.tools.inventory.require_scopes",
        return_value=_AuthInfo(),
    ):
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        inventory_tools.register_tools(mcp, object())
        tool_fn = mcp._tool_manager._tools["inventory_create_product"].fn
        payload = json.loads(
            tool_fn(
                name="Blocked Product",
                sku="BLOCK-001",
                warehouse_location="los_angeles",
                client_brand="TrackFlow",
                low_stock_threshold=-1,
            )
        )

    assert payload["ok"] is False
    assert payload["error_code"] == "MCP_VALIDATION_ERROR"


def test_inventory_validation_error_is_logged(caplog, mcp_test_env) -> None:
    caplog.set_level(logging.INFO, logger="mcp.company_tools")

    class _AuthInfo:
        client_id = "playground-client"
        scopes = ["inventory:read"]

    with patch(
        "mcps.company_tools.tools.inventory.require_scopes",
        return_value=_AuthInfo(),
    ):
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        inventory_tools.register_tools(mcp, object())
        tool_fn = mcp._tool_manager._tools["inventory_create_product"].fn
        _ = tool_fn(
            name="Blocked Product",
            sku="BLOCK-001",
            warehouse_location="los_angeles",
            client_brand="TrackFlow",
            low_stock_threshold=-1,
        )

    payload = json.loads(caplog.records[-1].message)
    assert payload["tool"] == "inventory_create_product"
    assert payload["success"] is False
    assert payload["error_code"] == "MCP_VALIDATION_ERROR"
