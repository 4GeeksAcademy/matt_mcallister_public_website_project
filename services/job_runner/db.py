"""Database helpers for job_runner (Postgres via DATABASE_URL)."""

from __future__ import annotations

import os
from typing import Optional

import psycopg


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Export a Postgres connection string before running."
        )
    return url


def get_connection(conninfo: Optional[str] = None) -> psycopg.Connection:
    """Open a new psycopg connection. Caller is responsible for closing it."""
    return psycopg.connect(conninfo or get_database_url())
