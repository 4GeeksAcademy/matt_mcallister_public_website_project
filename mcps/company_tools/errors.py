"""Stable MCP error codes for auth, authorization, validation, and backend failures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MCPToolError(Exception):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"error_code": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class MCPAuthRequired(MCPToolError):
    def __init__(self, message: str = "A valid Bearer access token is required.") -> None:
        super().__init__(code="MCP_AUTH_REQUIRED", message=message)


class MCPForbiddenScope(MCPToolError):
    def __init__(
        self,
        required: list[str],
        message: str = "The access token does not include the required scopes.",
    ) -> None:
        super().__init__(
            code="MCP_FORBIDDEN_SCOPE",
            message=message,
            details={"required_scopes": required},
        )


class MCPValidationError(MCPToolError):
    def __init__(self, message: str, *, field: Optional[str] = None) -> None:
        details = {"field": field} if field else None
        super().__init__(code="MCP_VALIDATION_ERROR", message=message, details=details)


class IncidentNotFound(MCPToolError):
    def __init__(self, incident_id: str) -> None:
        super().__init__(
            code="INCIDENT_NOT_FOUND",
            message=f"Incident {incident_id} was not found.",
            details={"incident_id": incident_id},
        )


class IncidentStatusTransitionInvalid(MCPToolError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="INCIDENT_STATUS_TRANSITION_INVALID",
            message=message,
        )


class InventoryWriteForbidden(MCPToolError):
    def __init__(self) -> None:
        super().__init__(
            code="INVENTORY_WRITE_FORBIDDEN",
            message=(
                "Inventory write operations are not permitted through MCP. "
                "Use the inventory backoffice for product changes."
            ),
        )


class BackendUnavailable(MCPToolError):
    def __init__(self, service: str, message: str = "The upstream service is unavailable.") -> None:
        super().__init__(
            code="BACKEND_UNAVAILABLE",
            message=message,
            details={"service": service},
        )
