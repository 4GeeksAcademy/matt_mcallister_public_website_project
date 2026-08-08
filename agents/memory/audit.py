"""Append-only auditable memory decision log."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Optional

_LOCK = Lock()
_ENTRIES: list[dict[str, Any]] = []


def _audit_path() -> Path:
    raw = os.environ.get(
        "AGENT_MEMORY_AUDIT_PATH",
        "data/agent-memory-audit.jsonl",
    )
    return Path(raw)


def log_memory_event(
    *,
    thread_id: str,
    user_id: str,
    proposal: Optional[dict[str, Any]],
    user_message: str,
    outcome: str,
    committed_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thread_id": thread_id,
        "user_id": user_id,
        "proposal": proposal,
        "user_message": user_message,
        "outcome": outcome,
        "committed_entry": committed_entry,
    }
    with _LOCK:
        _ENTRIES.append(record)
        path = _audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def get_audit_entries() -> list[dict[str, Any]]:
    with _LOCK:
        return list(_ENTRIES)


def reset_audit_log() -> None:
    with _LOCK:
        _ENTRIES.clear()
