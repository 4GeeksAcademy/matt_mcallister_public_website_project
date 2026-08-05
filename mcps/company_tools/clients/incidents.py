"""HTTP client for the TrackFlow incident manager API."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from mcps.company_tools.errors import (
    BackendUnavailable,
    IncidentNotFound,
    IncidentStatusTransitionInvalid,
)

DEFAULT_BASE_URL = "http://localhost:8001"
DEFAULT_TIMEOUT_SECONDS = 10.0


def _base_url(value: Optional[str] = None) -> str:
    return (value or os.environ.get("INCIDENTS_API_URL", DEFAULT_BASE_URL)).rstrip("/")


def _timeout(value: Optional[float] = None) -> float:
    if value is not None:
        return value
    raw = os.environ.get("MCP_BACKEND_TIMEOUT_SECONDS")
    if raw:
        return float(raw)
    return DEFAULT_TIMEOUT_SECONDS


class IncidentsClient:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._base_url = _base_url(base_url)
        self._timeout = _timeout(timeout)
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=self._timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "IncidentsClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def create_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(f"{self._base_url}/api/incidents", json=payload)
        except httpx.TimeoutException as exc:
            raise BackendUnavailable("incident-api", "Incident API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable("incident-api", "Incident API request failed.") from exc

        if response.status_code == 422:
            body = response.json()
            error = body.get("error") or {}
            raise IncidentStatusTransitionInvalid(
                error.get("message") or "Incident validation failed."
            )
        if response.status_code >= 400:
            raise BackendUnavailable(
                "incident-api",
                f"Incident API returned HTTP {response.status_code}.",
            )
        data = response.json().get("data")
        if not data:
            raise BackendUnavailable("incident-api", "Incident API returned an empty payload.")
        return data

    def get_incident(self, incident_id: str) -> dict[str, Any]:
        try:
            response = self._client.get(f"{self._base_url}/api/incidents/{incident_id}")
        except httpx.TimeoutException as exc:
            raise BackendUnavailable("incident-api", "Incident API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable("incident-api", "Incident API request failed.") from exc

        if response.status_code == 404:
            raise IncidentNotFound(incident_id)
        if response.status_code >= 400:
            raise BackendUnavailable(
                "incident-api",
                f"Incident API returned HTTP {response.status_code}.",
            )
        data = response.json().get("data")
        if not data:
            raise BackendUnavailable("incident-api", "Incident API returned an empty payload.")
        return data

    def list_incidents(
        self,
        *,
        status: Optional[str] = None,
        category: Optional[str] = None,
        origin: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        params = {
            key: value
            for key, value in {
                "status": status,
                "category": category,
                "origin": origin,
                "branch": branch,
            }.items()
            if value
        }
        try:
            response = self._client.get(f"{self._base_url}/api/incidents", params=params)
        except httpx.TimeoutException as exc:
            raise BackendUnavailable("incident-api", "Incident API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable("incident-api", "Incident API request failed.") from exc

        if response.status_code >= 400:
            raise BackendUnavailable(
                "incident-api",
                f"Incident API returned HTTP {response.status_code}.",
            )
        return response.json().get("data") or []

    def update_status(self, incident_id: str, status: str) -> dict[str, Any]:
        try:
            response = self._client.patch(
                f"{self._base_url}/api/incidents/{incident_id}/status",
                json={"status": status},
            )
        except httpx.TimeoutException as exc:
            raise BackendUnavailable("incident-api", "Incident API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable("incident-api", "Incident API request failed.") from exc

        if response.status_code == 404:
            raise IncidentNotFound(incident_id)
        if response.status_code == 409:
            body = response.json()
            error = body.get("error") or {}
            raise IncidentStatusTransitionInvalid(
                error.get("message") or "Invalid incident status transition."
            )
        if response.status_code >= 400:
            raise BackendUnavailable(
                "incident-api",
                f"Incident API returned HTTP {response.status_code}.",
            )
        data = response.json().get("data")
        if not data:
            raise BackendUnavailable("incident-api", "Incident API returned an empty payload.")
        return data
