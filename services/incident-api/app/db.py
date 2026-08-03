"""SQLite persistence for TrackFlow incidents."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = _REPO_ROOT / "data" / "process" / "incidents.db"
_initialized = False


def db_path() -> Path:
    return Path(os.environ.get("INCIDENTS_DB_PATH", str(DEFAULT_DB_PATH)))


def ensure_db() -> None:
    global _initialized
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                origin TEXT NOT NULL,
                branch TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                seed_key TEXT UNIQUE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    _initialized = True


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    ensure_db()
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "status": row["status"],
        "origin": row["origin"],
        "branch": row["branch"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
