"""LangChain MCP adapter client for TrackFlow company tools."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8006/mcp")
MCP_AGENT_ACCESS_TOKEN = os.environ.get("MCP_AGENT_ACCESS_TOKEN", "")


def _server_config() -> dict[str, Any]:
    headers: dict[str, str] = {}
    token = MCP_AGENT_ACCESS_TOKEN.strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return {
        "company_tools": {
            "url": MCP_SERVER_URL,
            "transport": "streamable_http",
            "headers": headers,
        }
    }


async def get_company_tools() -> list[Any]:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(_server_config())
    return await client.get_tools()


async def invoke_company_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tools = await get_company_tools()
    tool_map = {tool.name: tool for tool in tools}
    if tool_name not in tool_map:
        return {
            "ok": False,
            "error_code": "MCP_VALIDATION_ERROR",
            "message": f"Unknown MCP tool: {tool_name}",
        }
    raw = await tool_map[tool_name].ainvoke(arguments)
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"ok": True, "data": raw}
    if isinstance(raw, dict):
        return raw
    return {"ok": True, "data": raw}


def invoke_company_tool_sync(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    import asyncio

    return asyncio.run(invoke_company_tool(tool_name, arguments))
