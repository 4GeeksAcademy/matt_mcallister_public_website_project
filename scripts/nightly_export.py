#!/usr/bin/env python3
"""Nightly telemetry export orchestration job.

Exports the previous day's telemetry_events to a CSV audit snapshot under
data/raw/, then triggers the telemetry_kpi_daily pipeline. Execution is
tracked in job_runs. Pipeline-internal executions are tracked separately in
pipeline_runs (written by the pipeline itself).

Usage:
    python scripts/nightly_export.py

Env:
    DATABASE_URL   Postgres connection string (required)
    TARGET_DATE    Optional YYYY-MM-DD override (default: yesterday UTC)
"""

from __future__ import annotations

import csv
import logging
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Repo root on PYTHONPATH so services/ and data/ import as packages.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.job_runner import (  # noqa: E402
    ensure_pending_run,
    has_completed_for_date,
    has_processing_lock,
    mark_completed,
    mark_failed,
    mark_processing,
)
from services.job_runner.db import get_connection  # noqa: E402

JOB_NAME = "nightly_export"
RAW_DIR = REPO_ROOT / "data" / "raw"

logger = logging.getLogger(JOB_NAME)


def _log(level: int, message: str, *, status: str) -> None:
    logger.log(
        level,
        "%s job=%s status=%s %s",
        datetime.now(timezone.utc).isoformat(),
        JOB_NAME,
        status,
        message,
    )


def resolve_target_date() -> date:
    raw = os.environ.get("TARGET_DATE")
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def csv_path_for(target_date: date) -> Path:
    return RAW_DIR / f"telemetry_{target_date.isoformat()}.csv"


def export_telemetry_csv(target_date: date, path: Path) -> int:
    """Write telemetry_events for target_date to CSV. Returns row count."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    day_start = target_date
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, occurred_at, event_type, user_id, properties, created_at
                FROM telemetry_events
                WHERE occurred_at >= %s::date
                  AND occurred_at < (%s::date + INTERVAL '1 day')
                ORDER BY occurred_at, id
                """,
                (day_start, day_start),
            )
            rows = cur.fetchall()
            colnames = [desc.name for desc in cur.description]

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(colnames)
        for row in rows:
            writer.writerow(row)
    return len(rows)


def trigger_pipeline(target_date: date) -> None:
    cmd = [
        sys.executable,
        "-m",
        "data.pipelines.telemetry_kpi_daily.run",
        "--no-prefect",
        "--target-date",
        target_date.isoformat(),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    ).rstrip(os.pathsep)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        logger.info(result.stdout.rstrip())
    if result.stderr:
        logger.error(result.stderr.rstrip())
    if result.returncode != 0:
        raise RuntimeError(
            f"telemetry_kpi_daily exited with code {result.returncode}"
        )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    target_date = resolve_target_date()
    run_id: int | None = None
    succeeded = False
    error_message: str | None = None

    _log(logging.INFO, f"start target_date={target_date}", status="pending")

    if has_processing_lock(JOB_NAME):
        _log(
            logging.INFO,
            "cancelled: another nightly_export is already processing",
            status="cancelled",
        )
        return 0

    if has_completed_for_date(JOB_NAME, target_date):
        _log(
            logging.INFO,
            f"skipped: already completed for target_date={target_date}",
            status="completed",
        )
        return 0

    try:
        try:
            pending = ensure_pending_run(JOB_NAME, target_date)
        except RuntimeError as lock_err:
            _log(
                logging.INFO,
                f"cancelled: {lock_err}",
                status="cancelled",
            )
            return 0

        run_id = int(pending["id"])
        _log(
            logging.INFO,
            f"run_id={run_id} target_date={target_date} created",
            status="pending",
        )

        mark_processing(run_id)
        _log(logging.INFO, f"run_id={run_id} marked processing", status="processing")

        path = csv_path_for(target_date)
        if path.exists():
            _log(
                logging.INFO,
                f"csv already exists, skipping export path={path}",
                status="processing",
            )
        else:
            count = export_telemetry_csv(target_date, path)
            _log(
                logging.INFO,
                f"exported {count} rows to {path}",
                status="processing",
            )

        trigger_pipeline(target_date)
        mark_completed(run_id)
        succeeded = True
        _log(logging.INFO, f"finished target_date={target_date}", status="completed")
        return 0
    except Exception as exc:
        error_message = str(exc)
        _log(logging.ERROR, f"exception: {exc}", status="failed")
        raise
    finally:
        # Guarantee no row remains in processing after a failed execution.
        if run_id is not None and not succeeded:
            try:
                mark_failed(run_id, error_message or "unknown error")
            except Exception as mark_exc:
                _log(
                    logging.ERROR,
                    f"failed to mark job failed: {mark_exc}",
                    status="failed",
                )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(1)
