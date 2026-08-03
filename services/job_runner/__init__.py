"""Job run tracking against the job_runs table."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

import psycopg
from psycopg.rows import dict_row

from .db import get_connection

JobStatus = str  # pending | processing | completed | failed


def create_run(
    job_name: str,
    target_date: date,
    status: JobStatus = "pending",
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Insert a job_runs row and return it."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO job_runs (job_name, target_date, status, started_at, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    job_name,
                    target_date,
                    status,
                    datetime.now(timezone.utc) if status == "processing" else None,
                    datetime.now(timezone.utc),
                ),
            )
            row = cur.fetchone()
            if owns_conn:
                conn.commit()
            return dict(row) if row else {}
    finally:
        if owns_conn:
            conn.close()


def ensure_pending_run(
    job_name: str,
    target_date: date,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Create or reset a job_runs row to pending for (job_name, target_date).

    Reuses a prior failed/pending row. Raises if the row is processing or completed.
    """
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    now = datetime.now(timezone.utc)
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO job_runs (
                    job_name, target_date, status, started_at, finished_at,
                    error_message, created_at
                )
                VALUES (%s, %s, 'pending', NULL, NULL, NULL, %s)
                ON CONFLICT (job_name, target_date) DO UPDATE
                SET status = 'pending',
                    started_at = NULL,
                    finished_at = NULL,
                    error_message = NULL
                WHERE job_runs.status IN ('pending', 'failed')
                RETURNING *
                """,
                (job_name, target_date, now),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(
                    f"Cannot create pending run for {job_name} on {target_date}: "
                    "row exists with status processing or completed"
                )
            if owns_conn:
                conn.commit()
            return dict(row)
    finally:
        if owns_conn:
            conn.close()


def mark_processing(
    run_id: int,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Transition a job_runs row from pending to processing."""
    return update_run(run_id, status="processing", conn=conn)


def start_run(
    job_name: str,
    target_date: date,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Ensure pending, then transition to processing (full state-machine start)."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        pending = ensure_pending_run(job_name, target_date, conn=conn)
        result = mark_processing(int(pending["id"]), conn=conn)
        if owns_conn:
            conn.commit()
        return result
    finally:
        if owns_conn:
            conn.close()


def update_run(
    run_id: int,
    *,
    status: Optional[JobStatus] = None,
    error_message: Optional[str] = None,
    finished: bool = False,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Update status / error / finished_at on a job_runs row."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        sets: list[str] = []
        params: list[Any] = []
        if status is not None:
            sets.append("status = %s")
            params.append(status)
            if status == "processing":
                sets.append("started_at = %s")
                params.append(datetime.now(timezone.utc))
        if error_message is not None:
            sets.append("error_message = %s")
            params.append(error_message)
        if finished or status in ("completed", "failed"):
            sets.append("finished_at = %s")
            params.append(datetime.now(timezone.utc))
        if not sets:
            raise ValueError("update_run requires at least one field to update")
        params.append(run_id)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"UPDATE job_runs SET {', '.join(sets)} WHERE id = %s RETURNING *",
                params,
            )
            row = cur.fetchone()
            if owns_conn:
                conn.commit()
            return dict(row) if row else {}
    finally:
        if owns_conn:
            conn.close()


def get_run(run_id: int, *, conn: Optional[psycopg.Connection] = None) -> Optional[dict[str, Any]]:
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM job_runs WHERE id = %s", (run_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        if owns_conn:
            conn.close()


def get_run_for_date(
    job_name: str,
    target_date: date,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> Optional[dict[str, Any]]:
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM job_runs
                WHERE job_name = %s AND target_date = %s
                """,
                (job_name, target_date),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        if owns_conn:
            conn.close()


def has_processing_lock(
    job_name: str,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> bool:
    """True if any job_runs row for job_name is currently processing."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM job_runs
                WHERE job_name = %s AND status = 'processing'
                LIMIT 1
                """,
                (job_name,),
            )
            return cur.fetchone() is not None
    finally:
        if owns_conn:
            conn.close()


def has_completed_for_date(
    job_name: str,
    target_date: date,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> bool:
    """True if a completed run already exists for (job_name, target_date)."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    assert conn is not None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM job_runs
                WHERE job_name = %s
                  AND target_date = %s
                  AND status = 'completed'
                LIMIT 1
                """,
                (job_name, target_date),
            )
            return cur.fetchone() is not None
    finally:
        if owns_conn:
            conn.close()


def mark_failed(
    run_id: int,
    error_message: str,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    """Set status to failed with error_message; never leave processing."""
    return update_run(
        run_id,
        status="failed",
        error_message=error_message,
        finished=True,
        conn=conn,
    )


def mark_completed(
    run_id: int,
    *,
    conn: Optional[psycopg.Connection] = None,
) -> dict[str, Any]:
    return update_run(run_id, status="completed", finished=True, conn=conn)
