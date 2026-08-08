"""Memory consolidation and retention policy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

MAX_ENTRIES = 20
RETENTION_DAYS = 90


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def consolidate_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe, expire, and cap stored memory entries."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        created = _parse_iso(str(entry.get("updated_at") or entry.get("created_at")))
        if created < cutoff:
            continue
        key = (
            str(entry.get("category", "preference")),
            " ".join(str(entry.get("text", "")).casefold().split()),
        )
        existing = deduped.get(key)
        if existing is None or created >= _parse_iso(str(existing.get("updated_at"))):
            deduped[key] = dict(entry)

    sorted_entries = sorted(
        deduped.values(),
        key=lambda item: _parse_iso(
            str(item.get("updated_at") or item.get("created_at"))
        ),
        reverse=True,
    )
    return sorted_entries[:MAX_ENTRIES]
