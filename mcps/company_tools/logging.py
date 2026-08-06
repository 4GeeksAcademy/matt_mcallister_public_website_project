"""Structured logging for MCP tool invocations."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger("mcp.company_tools")


def log_tool_invocation(
    *,
    client_id: Optional[str],
    tool: str,
    success: bool,
    error_code: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    payload: dict[str, Any] = {
        "event": "mcp_tool_invocation",
        "client_id": client_id or "unknown",
        "tool": tool,
        "success": success,
        "error_code": error_code,
    }
    if extra:
        payload.update(extra)
    logger.info(json.dumps(payload, sort_keys=True))
