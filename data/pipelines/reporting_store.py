"""Reporting store helpers — no Prefect dependency.

Used by the ETL load tasks and by services/reporting query endpoints.
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "process" / "reporting.db"


def _utcnow_iso():
    # type: () -> str
    return datetime.now(timezone.utc).isoformat()


def _get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def ensure_local_schema(conn):
    # type: (sqlite3.Connection) -> None
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS weekly_warehouse_client_performance (
            id TEXT PRIMARY KEY,
            warehouse TEXT NOT NULL,
            client_id TEXT NOT NULL,
            week_start TEXT NOT NULL,
            inbound_units_count INTEGER NOT NULL DEFAULT 0,
            outbound_orders_count INTEGER NOT NULL DEFAULT 0,
            stockout_events_count INTEGER NOT NULL DEFAULT 0,
            discrepancy_events_count INTEGER NOT NULL DEFAULT 0,
            discrepancy_rate REAL NOT NULL DEFAULT 0,
            computed_at TEXT NOT NULL,
            UNIQUE (warehouse, client_id, week_start)
        );

        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id TEXT PRIMARY KEY,
            flow_run_id TEXT,
            week_start TEXT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            records_processed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            error_message TEXT
        );
        """
    )
    conn.commit()


def get_latest_pipeline_run(db_path=None):
    # type: (Optional[str]) -> Optional[Dict[str, Any]]
    """Return the most recent pipeline_runs row (Supabase or local SQLite)."""
    client = _get_supabase()
    if client is not None:
        try:
            result = (
                client.schema("reporting")
                .table("pipeline_runs")
                .select("*")
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = list(result.data or [])
            if rows:
                return rows[0]
        except Exception:
            pass

    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not path.exists():
        return None
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT id, flow_run_id, week_start, started_at, finished_at,
                   records_processed, status, error_message
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def query_weekly_performance(week_start=None, db_path=None):
    # type: (Optional[str], Optional[str]) -> Dict[str, Any]
    """Query KPI rows for a week (defaults to most recent computed week)."""
    client = _get_supabase()
    if client is not None:
        try:
            table = client.schema("reporting").table("weekly_warehouse_client_performance")
            if week_start:
                result = (
                    table.select("*")
                    .eq("week_start", week_start)
                    .order("warehouse")
                    .order("client_id")
                    .execute()
                )
                return {"week_start": week_start, "entries": list(result.data or [])}
            latest = (
                table.select("week_start")
                .order("week_start", desc=True)
                .limit(1)
                .execute()
            )
            if not latest.data:
                return {"week_start": None, "entries": []}
            ws = latest.data[0]["week_start"]
            result = (
                table.select("*")
                .eq("week_start", ws)
                .order("warehouse")
                .order("client_id")
                .execute()
            )
            return {"week_start": ws, "entries": list(result.data or [])}
        except Exception:
            pass

    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not path.exists():
        return {"week_start": week_start, "entries": []}
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        ws = week_start
        if not ws:
            row = conn.execute(
                "SELECT week_start FROM weekly_warehouse_client_performance "
                "ORDER BY week_start DESC LIMIT 1"
            ).fetchone()
            if not row:
                return {"week_start": None, "entries": []}
            ws = row["week_start"]
        rows = conn.execute(
            """
            SELECT warehouse, client_id, week_start,
                   inbound_units_count, outbound_orders_count,
                   stockout_events_count, discrepancy_events_count,
                   discrepancy_rate
            FROM weekly_warehouse_client_performance
            WHERE week_start = ?
            ORDER BY warehouse, client_id
            """,
            (ws,),
        ).fetchall()
        entries = []  # type: List[Dict[str, Any]]
        for r in rows:
            entry = dict(r)
            entry["discrepancy_rate"] = float(entry["discrepancy_rate"])
            entries.append(entry)
        return {"week_start": ws, "entries": entries}
    finally:
        conn.close()


def upsert_weekly_rows(rows, db_path=None):
    # type: (List[Dict[str, Any]], Optional[str]) -> int
    if not rows:
        return 0
    computed_at = _utcnow_iso()
    client = _get_supabase()
    if client is not None:
        try:
            payload = [dict(row, computed_at=computed_at) for row in rows]
            (
                client.schema("reporting")
                .table("weekly_warehouse_client_performance")
                .upsert(payload, on_conflict="warehouse,client_id,week_start")
                .execute()
            )
            return len(rows)
        except Exception:
            pass

    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        ensure_local_schema(conn)
        for row in rows:
            conn.execute(
                """
                INSERT INTO weekly_warehouse_client_performance (
                    id, warehouse, client_id, week_start,
                    inbound_units_count, outbound_orders_count,
                    stockout_events_count, discrepancy_events_count,
                    discrepancy_rate, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(warehouse, client_id, week_start) DO UPDATE SET
                    inbound_units_count = excluded.inbound_units_count,
                    outbound_orders_count = excluded.outbound_orders_count,
                    stockout_events_count = excluded.stockout_events_count,
                    discrepancy_events_count = excluded.discrepancy_events_count,
                    discrepancy_rate = excluded.discrepancy_rate,
                    computed_at = excluded.computed_at
                """,
                (
                    str(uuid.uuid4()),
                    row["warehouse"],
                    row["client_id"],
                    row["week_start"],
                    row["inbound_units_count"],
                    row["outbound_orders_count"],
                    row["stockout_events_count"],
                    row["discrepancy_events_count"],
                    row["discrepancy_rate"],
                    computed_at,
                ),
            )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def insert_pipeline_run(row, db_path=None):
    # type: (Dict[str, Any], Optional[str]) -> Dict[str, Any]
    client = _get_supabase()
    if client is not None:
        try:
            client.schema("reporting").table("pipeline_runs").insert(row).execute()
            return row
        except Exception:
            pass

    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        ensure_local_schema(conn)
        conn.execute(
            """
            INSERT INTO pipeline_runs (
                id, flow_run_id, week_start, started_at, finished_at,
                records_processed, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row.get("flow_run_id"),
                row["week_start"],
                row["started_at"],
                row.get("finished_at"),
                row.get("records_processed", 0),
                row["status"],
                row.get("error_message"),
            ),
        )
        conn.commit()
        return row
    finally:
        conn.close()
