"""Async Celery tasks for TrackFlow background processing."""

from __future__ import annotations

import logging
import os
import sys
import time
import traceback
from pathlib import Path

from services.celery_app.celery import app
from services.celery_app.dlq import record_failure

logger = logging.getLogger(__name__)

# Ensure analysis_bridge imports resolve (services/api on path, scripts via bridge).
_API_DIR = Path(__file__).resolve().parents[1] / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from app.analysis_bridge import result_to_dict, run_analysis  # noqa: E402


def _upload_dir() -> Path:
    return Path(os.environ.get("UPLOAD_DIR", "/data/uploads"))


@app.task(bind=True, max_retries=3, name="services.celery_app.tasks.analyze_incident")
def analyze_incident(self, upload_id: str, source_file: str) -> dict:
    """Load a previously uploaded CSV by id and run incident analysis."""
    started = time.monotonic()
    attempt = self.request.retries + 1
    task_id = self.request.id or "unknown"

    try:
        csv_path = _upload_dir() / f"{upload_id}.csv"
        if not csv_path.is_file():
            raise FileNotFoundError(f"Upload not found: {upload_id}")

        content = csv_path.read_text(encoding="utf-8")
        result = run_analysis(content, source_file)
        payload = result_to_dict(result)

        duration_ms = round((time.monotonic() - started) * 1000, 2)
        logger.info(
            "task_id=%s attempt=%s status=success duration_ms=%s source_file=%s",
            task_id,
            attempt,
            duration_ms,
            source_file,
        )
        return payload
    except Exception as exc:
        duration_ms = round((time.monotonic() - started) * 1000, 2)
        logger.error(
            "task_id=%s attempt=%s status=failure duration_ms=%s error=%s\n%s",
            task_id,
            attempt,
            duration_ms,
            exc,
            traceback.format_exc(),
        )

        if self.request.retries >= self.max_retries:
            try:
                record_failure(
                    task_id=task_id,
                    attempt=attempt,
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            except Exception:
                logger.exception(
                    "Failed to record DLQ entry for task_id=%s attempt=%s",
                    task_id,
                    attempt,
                )
            raise

        # Exponential backoff: 2, 4, 8 seconds (no immediate retry).
        countdown = 2 ** (self.request.retries + 1)
        raise self.retry(exc=exc, countdown=countdown) from exc
