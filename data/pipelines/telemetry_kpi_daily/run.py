"""Nightly telemetry KPI aggregation pipeline.

Reads from the database (telemetry_events), never from CSV snapshots.
Persists one idempotent row per UTC day in reporting.telemetry_kpi_daily and
records each execution in pipeline_runs (separate from job_runs).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

from data.pipelines.tracking import finish_pipeline_run, start_pipeline_run
from services.job_runner.db import get_connection

PIPELINE_NAME = "telemetry_kpi_daily"
logger = logging.getLogger(__name__)


def aggregate_daily_kpis(cur: Any, day: date) -> dict[str, Any]:
    """Compute volume, active-user, and event-mix KPIs for one UTC day."""
    cur.execute(
        """
        WITH daily AS (
            SELECT event_type, user_id
            FROM telemetry_events
            WHERE occurred_at >= %s::date
              AND occurred_at < (%s::date + INTERVAL '1 day')
        ),
        by_type AS (
            SELECT event_type, COUNT(*)::bigint AS event_count
            FROM daily
            GROUP BY event_type
        )
        SELECT
            (SELECT COUNT(*)::bigint FROM daily) AS event_count,
            (SELECT COUNT(DISTINCT user_id)::bigint FROM daily) AS unique_user_count,
            COALESCE(
                (SELECT jsonb_object_agg(event_type, event_count) FROM by_type),
                '{}'::jsonb
            ) AS event_type_counts
        """,
        (day, day),
    )
    row = cur.fetchone()
    event_type_counts = row[2] or {}
    if isinstance(event_type_counts, str):
        event_type_counts = json.loads(event_type_counts)
    return {
        "target_date": day,
        "event_count": int(row[0]),
        "unique_user_count": int(row[1]),
        "event_type_counts": dict(event_type_counts),
    }


def persist_daily_kpis(cur: Any, kpis: dict[str, Any]) -> None:
    """Upsert the daily grain so retries replace, rather than duplicate, KPIs."""
    cur.execute("CREATE SCHEMA IF NOT EXISTS reporting")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reporting.telemetry_kpi_daily (
            target_date DATE PRIMARY KEY,
            event_count BIGINT NOT NULL,
            unique_user_count BIGINT NOT NULL,
            event_type_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
            computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        INSERT INTO reporting.telemetry_kpi_daily (
            target_date, event_count, unique_user_count,
            event_type_counts, computed_at
        )
        VALUES (%s, %s, %s, %s::jsonb, NOW())
        ON CONFLICT (target_date) DO UPDATE SET
            event_count = EXCLUDED.event_count,
            unique_user_count = EXCLUDED.unique_user_count,
            event_type_counts = EXCLUDED.event_type_counts,
            computed_at = EXCLUDED.computed_at
        """,
        (
            kpis["target_date"],
            kpis["event_count"],
            kpis["unique_user_count"],
            json.dumps(kpis["event_type_counts"], sort_keys=True),
        ),
    )


def run(*, target_date: date | None = None, no_prefect: bool = True) -> int:
    """Aggregate and idempotently persist telemetry KPIs for the target day."""
    day = target_date or (datetime.now(timezone.utc).date() - timedelta(days=1))
    logger.info(
        "telemetry_kpi_daily start target_date=%s no_prefect=%s",
        day,
        no_prefect,
    )
    pipeline_run = start_pipeline_run(PIPELINE_NAME, day)
    run_id = int(pipeline_run["id"])
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                kpis = aggregate_daily_kpis(cur, day)
                persist_daily_kpis(cur, kpis)
            conn.commit()
        finish_pipeline_run(run_id, status="completed")
        logger.info(
            "telemetry_kpi_daily finished target_date=%s event_count=%s "
            "unique_user_count=%s pipeline_run_id=%s",
            day,
            kpis["event_count"],
            kpis["unique_user_count"],
            run_id,
        )
        return 0
    except Exception as exc:
        finish_pipeline_run(run_id, status="failed", error_message=str(exc))
        logger.exception("telemetry_kpi_daily failed target_date=%s", day)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Telemetry KPI daily pipeline")
    parser.add_argument(
        "--no-prefect",
        action="store_true",
        help="Run without Prefect orchestration (default for nightly trigger)",
    )
    parser.add_argument(
        "--target-date",
        type=date.fromisoformat,
        default=None,
        help="UTC calendar day to process (YYYY-MM-DD); defaults to yesterday UTC",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return run(target_date=args.target_date, no_prefect=args.no_prefect)


if __name__ == "__main__":
    sys.exit(main())
