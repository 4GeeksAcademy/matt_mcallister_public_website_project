"""Minimal telemetry KPI daily pipeline stub.

Reads from the database (telemetry_events), never from CSV snapshots.
Records each execution in pipeline_runs (separate from job_runs).
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, timedelta, timezone

from data.pipelines.tracking import finish_pipeline_run, start_pipeline_run
from services.job_runner.db import get_connection

PIPELINE_NAME = "telemetry_kpi_daily"
logger = logging.getLogger(__name__)


def run(*, target_date: date | None = None, no_prefect: bool = True) -> int:
    """Count telemetry events for the target day; track via pipeline_runs."""
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
                cur.execute(
                    """
                    SELECT COUNT(*) FROM telemetry_events
                    WHERE occurred_at >= %s::date
                      AND occurred_at < (%s::date + INTERVAL '1 day')
                    """,
                    (day, day),
                )
                count = cur.fetchone()[0]
        finish_pipeline_run(run_id, status="completed")
        logger.info(
            "telemetry_kpi_daily finished target_date=%s event_count=%s "
            "pipeline_run_id=%s",
            day,
            count,
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
