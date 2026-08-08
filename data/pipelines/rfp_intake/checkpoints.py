"""Checkpoint thread helpers and interrupt/resume state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_CHECKPOINT_DIR = Path(__file__).resolve().parents[3] / ".rfp-checkpoints"


def thread_id_for_ticket(ticket_id: str) -> str:
    return f"rfp-{ticket_id}"


def thread_id_for_department(ticket_id: str, department_id: str) -> str:
    return f"rfp-{ticket_id}:{department_id}"


def _checkpoint_path(thread_id: str) -> Path:
    return _CHECKPOINT_DIR / f"{thread_id.replace(':', '_')}.json"


def save_checkpoint(thread_id: str, payload: dict[str, Any]) -> None:
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    _checkpoint_path(thread_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_checkpoint(thread_id: str) -> Optional[dict[str, Any]]:
    path = _checkpoint_path(thread_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_checkpoints(ticket_id: str) -> None:
    if not _CHECKPOINT_DIR.is_dir():
        return
    prefix = f"rfp-{ticket_id}".replace(":", "_")
    for path in _CHECKPOINT_DIR.glob(f"{prefix}*.json"):
        path.unlink(missing_ok=True)


def reset_checkpoints() -> None:
    if _CHECKPOINT_DIR.is_dir():
        for path in _CHECKPOINT_DIR.glob("*.json"):
            path.unlink(missing_ok=True)
