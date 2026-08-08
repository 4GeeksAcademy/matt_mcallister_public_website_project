"""Guardrail trigger logging and session summaries."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

_COUNTERS: Counter[str] = Counter()
_TYPE_COUNTERS: Counter[str] = Counter()
_LOCK = Lock()


def record_guardrail_trigger(
    *,
    rule: str,
    guardrail_type: str,
    thread_id: str | None = None,
    question: str | None = None,
) -> None:
    with _LOCK:
        _COUNTERS[rule] += 1
        _TYPE_COUNTERS[guardrail_type] += 1
    logger.info(
        "guardrail_trigger type=%s rule=%s thread_id=%s question=%r",
        guardrail_type,
        rule,
        thread_id,
        (question or "")[:120],
    )


def get_guardrail_summary(*, reset: bool = False) -> dict[str, Any]:
    with _LOCK:
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "by_rule": dict(_COUNTERS),
            "by_type": dict(_TYPE_COUNTERS),
            "total": sum(_COUNTERS.values()),
        }
        if reset:
            _COUNTERS.clear()
            _TYPE_COUNTERS.clear()
    return summary


def reset_guardrail_summary() -> None:
    with _LOCK:
        _COUNTERS.clear()
        _TYPE_COUNTERS.clear()
