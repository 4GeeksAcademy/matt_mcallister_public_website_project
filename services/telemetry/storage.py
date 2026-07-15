"""Telemetry storage helpers (Supabase + in-memory mirror)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, List

from telemetry.models import TelemetryEvent

logger = logging.getLogger("trackflow.telemetry.storage")

_MEMORY_EVENTS: List[dict] = []
_supabase = None


def _get_supabase():
    global _supabase
    if _supabase is not None:
        return _supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        logger.warning("Supabase credentials missing; using in-memory telemetry store")
        return None
    try:
        from supabase import create_client

        _supabase = create_client(url, key)
        return _supabase
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase client init failed: %s", exc)
        return None


def event_to_row(event: TelemetryEvent) -> dict:
    """Map TelemetryEvent envelope → telemetry_events row."""
    tags = {
        **event.properties,
        "sessionId": event.sessionId,
        "userId": event.userId,
        "schemaVersion": event.schemaVersion,
        "requestId": event.requestId,
        "eventId": event.eventId,
    }
    return {
        "event_id": event.eventId,
        "timestamp": event.timestamp,
        "event_type": event.event_type,
        "session_id": event.sessionId,
        "user_id": event.userId,
        "schema_version": event.schemaVersion,
        "request_id": event.requestId,
        "tags": tags,
    }


def bulk_insert(events: List[TelemetryEvent]) -> int:
    if not events:
        return 0
    rows = [event_to_row(e) for e in events]
    # Always mirror locally so reports work even without SELECT privileges.
    _MEMORY_EVENTS.extend(rows)
    client = _get_supabase()
    if client is None:
        return len(rows)
    try:
        client.table("telemetry_events").insert(rows).execute()
    except Exception as exc:  # noqa: BLE001
        logger.error("Supabase insert failed (memory mirror retained): %s", exc)
    return len(rows)


def fetch_events(start: datetime, end: datetime) -> List[dict]:
    client = _get_supabase()
    start_iso = start.astimezone(timezone.utc).isoformat()
    end_iso = end.astimezone(timezone.utc).isoformat()
    if client is not None:
        try:
            result = (
                client.table("telemetry_events")
                .select("*")
                .gte("timestamp", start_iso)
                .lte("timestamp", end_iso)
                .execute()
            )
            data = list(result.data or [])
            if data:
                return data
        except Exception as exc:  # noqa: BLE001
            logger.error("Supabase fetch failed, using memory: %s", exc)
    return [
        r
        for r in _MEMORY_EVENTS
        if start_iso <= str(r.get("timestamp", "")) <= end_iso
    ]


def memory_count() -> int:
    return len(_MEMORY_EVENTS)
