"""Pipeline-internal run tracking against pipeline_runs (not job_runs)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

import psycopg
from psycopg.rows import dict_row

from services.job_runner.db import get_connection


def start_pipeline_run(
    pipeline_name: str,
    target_date: date,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Insert a pipeline_runs row in processing state."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    now = datetime.now(timezone.utc)
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO pipeline_runs (
                    pipeline_name, target_date, status,
                    started_at, created_at
                )
                VALUES (%s, %s, 'processing', %s, %s)
                RETURNING *
                """,
                (pipeline_name, target_date, now, now),
            )
            row = cur.fetchone()
            if owns_conn:
                conn.commit()
            return dict(row) if row else {}
    finally:
        if owns_conn:
            conn.close()


def finish_pipeline_run(
    run_id: int,
    *,
    status: str,
    error_message: Optional[str] = None,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Mark a pipeline run completed or failed."""
    if status not in ("completed", "failed"):
        raise ValueError("status must be 'completed' or 'failed'")
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    now = datetime.now(timezone.utc)
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE pipeline_runs
                SET status = %s,
                    finished_at = %s,
                    error_message = %s
                WHERE id = %s
                RETURNING *
                """,
                (status, now, error_message, run_id),
            )
            row = cur.fetchone()
            if owns_conn:
                conn.commit()
            return dict(row) if row else {}
    finally:
        if owns_conn:
            conn.close()
