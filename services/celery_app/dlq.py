"""Dead-letter queue recorder for exhausted Celery task retries."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import psycopg


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Export a Postgres connection string before "
            "recording task failures."
        )
    return url


def record_failure(
    task_id: str,
    attempt: int,
    error_message: str,
    failed_at: datetime | None = None,
) -> None:
    """Insert a row into task_failures when a task exceeds max_retries."""
    ts = failed_at or datetime.now(timezone.utc)
    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO task_failures (task_id, attempt, error_message, failed_at)
                VALUES (%s, %s, %s, %s)
                """,
                (task_id, attempt, error_message, ts),
            )
        conn.commit()
