"""Telemetry router: ingest events + reporting endpoint."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import ValidationError

from telemetry import analysis, storage
from telemetry.models import TelemetryBatch, TelemetryEvent

logger = logging.getLogger("trackflow.telemetry")

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

_REPORT_CACHE: dict = {}
_CACHE_TTL_SECONDS = 60.0


@router.post("/events")
def post_events(body: TelemetryBatch) -> dict:
    """Accept a batch, validate per-event, persist valid rows, reject the rest."""
    raw_events = body.events or []
    received = len(raw_events)
    logger.info("telemetry batch received: %s events", received)

    valid = []
    rejected = 0
    for raw in raw_events:
        try:
            event = TelemetryEvent.model_validate(raw)
            logger.info("event_type=%s", event.event_type)
            valid.append(event)
        except ValidationError as exc:
            rejected += 1
            logger.warning("rejected event: %s", exc.errors())

    stored = storage.bulk_insert(valid)
    return {"received": received, "stored": stored, "rejected": rejected}


@router.get("/report")
def get_report(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
) -> dict:
    now = datetime.now(timezone.utc)
    if end_date:
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    else:
        end = now
    if start_date:
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    else:
        start = end - timedelta(days=7)

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    cache_key = f"{start.isoformat()}|{end.isoformat()}"
    cached = _REPORT_CACHE.get(cache_key)
    if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    rows = storage.fetch_events(start, end)
    report = {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "metrics": {
            "events_per_day": analysis.events_per_day(rows, start, end),
            "order_volume_by_warehouse": analysis.order_volume_by_warehouse(
                rows, start, end
            ),
            "stock_threshold_rate_by_client": analysis.stock_threshold_rate_by_client(
                rows, start, end
            ),
            "discrepancy_rate_by_warehouse": analysis.discrepancy_rate_by_warehouse(
                rows, start, end
            ),
            "error_rate_by_type": analysis.error_rate_by_type(rows, start, end),
            "auth_failure_rate": analysis.auth_failure_rate(rows, start, end),
        },
    }
    _REPORT_CACHE[cache_key] = (time.monotonic(), report)
    return report
