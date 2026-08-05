"""HTTP client for the TrackFlow inventory API."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from mcps.company_tools.errors import BackendUnavailable

DEFAULT_BASE_URL = "http://localhost:8003"
DEFAULT_TIMEOUT_SECONDS = 10.0


def _base_url(value: Optional[str] = None) -> str:
    return (value or os.environ.get("INVENTORY_API_URL", DEFAULT_BASE_URL)).rstrip("/")


def _timeout(value: Optional[float] = None) -> float:
    if value is not None:
        return value
    raw = os.environ.get("MCP_BACKEND_TIMEOUT_SECONDS")
    if raw:
        return float(raw)
    return DEFAULT_TIMEOUT_SECONDS


def _service_token() -> str:
    token = os.environ.get("INVENTORY_SERVICE_TOKEN", "").strip()
    if not token:
        raise BackendUnavailable(
            "inventory-api",
            "INVENTORY_SERVICE_TOKEN is not configured for MCP inventory reads.",
        )
    return token


class InventoryClient:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        service_token: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._base_url = _base_url(base_url)
        self._timeout = _timeout(timeout)
        self._service_token = service_token
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=self._timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "InventoryClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        token = self._service_token or _service_token()
        return {"Authorization": f"Bearer {token}"}

    def list_products(self) -> list[dict[str, Any]]:
        try:
            response = self._client.get(
                f"{self._base_url}/inventory/products",
                headers=self._headers(),
            )
        except httpx.TimeoutException as exc:
            raise BackendUnavailable("inventory-api", "Inventory API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable("inventory-api", "Inventory API request failed.") from exc

        if response.status_code == 401:
            raise BackendUnavailable(
                "inventory-api",
                "Inventory service token was rejected (HTTP 401).",
            )
        if response.status_code >= 400:
            raise BackendUnavailable(
                "inventory-api",
                f"Inventory API returned HTTP {response.status_code}.",
            )
        return response.json()
