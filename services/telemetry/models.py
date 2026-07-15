"""Pydantic models for telemetry events (shared by stub and real endpoint)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class TelemetryEvent(BaseModel):
    eventId: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)
    sessionId: str = Field(..., min_length=1)
    userId: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    schemaVersion: str = Field(..., min_length=1)
    requestId: str = Field(..., min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class TelemetryBatch(BaseModel):
    """Loose batch wrapper — events validated individually in the handler."""

    events: list[Any] = Field(default_factory=list)
