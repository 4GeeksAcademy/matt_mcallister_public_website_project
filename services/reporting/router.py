"""Reporting endpoints — query KPIs and trigger/inspect pipeline runs.

ETL logic lives in data/pipelines/; this module only imports helpers and
invokes `data/pipelines/pipeline.py` (no duplicated ETL in services/).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PIPELINES_DIR = _REPO_ROOT / "data" / "pipelines"
if str(_PIPELINES_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINES_DIR))

from reporting_store import (  # noqa: E402
    get_latest_pipeline_run,
    query_weekly_performance,
)

router = APIRouter(prefix="/reporting", tags=["reporting"])


class WeeklyPerformanceEntry(BaseModel):
    warehouse: str
    client_id: str
    inbound_units_count: int
    outbound_orders_count: int
    stockout_events_count: int
    discrepancy_events_count: int
    discrepancy_rate: float


class WeeklyPerformanceResponse(BaseModel):
    week_start: Optional[str] = None
    entries: List[WeeklyPerformanceEntry] = Field(default_factory=list)


class PipelineLatestRunResponse(BaseModel):
    id: Optional[str] = None
    flow_run_id: Optional[str] = None
    week_start: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    records_processed: Optional[int] = None
    status: str
    error_message: Optional[str] = None


class TriggerPipelineRequest(BaseModel):
    week_start: Optional[str] = Field(
        default=None,
        description="ISO week Monday (YYYY-MM-DD). Defaults to prior completed week.",
    )
    force_notify_failure: bool = Field(
        default=False,
        description="Force optional notify step to fail without failing the ETL.",
    )


class PipelineRunResponse(BaseModel):
    status: str
    week_start: Optional[str] = None
    flow_run_id: Optional[str] = None
    run_id: Optional[str] = None
    records_processed: Optional[int] = None
    notify_status: Optional[str] = None
    error: Optional[str] = None


def _pipeline_python() -> str:
    """Prefer the pipelines venv (has Prefect); fall back to current interpreter."""
    for path in (
        _PIPELINES_DIR / ".venv" / "bin" / "python",
        _PIPELINES_DIR / ".venv" / "bin" / "python3",
    ):
        if path.exists():
            return str(path)
    return sys.executable


@router.get(
    "/weekly-warehouse-client-performance",
    response_model=WeeklyPerformanceResponse,
)
def get_weekly_warehouse_client_performance(
    week_start: Optional[str] = Query(
        default=None,
        description="ISO week Monday (YYYY-MM-DD). Defaults to most recent computed week.",
    ),
) -> WeeklyPerformanceResponse:
    """Return per-warehouse / per-client KPIs for a week."""
    payload = query_weekly_performance(week_start=week_start)
    entries: List[Dict[str, Any]] = payload.get("entries") or []
    slim = [
        {
            "warehouse": e["warehouse"],
            "client_id": e["client_id"],
            "inbound_units_count": int(e["inbound_units_count"]),
            "outbound_orders_count": int(e["outbound_orders_count"]),
            "stockout_events_count": int(e["stockout_events_count"]),
            "discrepancy_events_count": int(e["discrepancy_events_count"]),
            "discrepancy_rate": float(e["discrepancy_rate"]),
        }
        for e in entries
    ]
    return WeeklyPerformanceResponse(week_start=payload.get("week_start"), entries=slim)


@router.get("/pipeline-runs/latest", response_model=PipelineLatestRunResponse)
def get_latest_run() -> PipelineLatestRunResponse:
    """Return status and metadata for the most recent pipeline run."""
    latest = get_latest_pipeline_run()
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pipeline runs recorded yet",
        )
    return PipelineLatestRunResponse(
        id=latest.get("id"),
        flow_run_id=latest.get("flow_run_id"),
        week_start=str(latest["week_start"]) if latest.get("week_start") is not None else None,
        started_at=latest.get("started_at"),
        finished_at=latest.get("finished_at"),
        records_processed=latest.get("records_processed"),
        status=latest.get("status") or "Unknown",
        error_message=latest.get("error_message"),
    )


@router.post(
    "/pipeline-runs",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_pipeline_run(
    payload: Optional[TriggerPipelineRequest] = None,
) -> PipelineRunResponse:
    """Trigger weekly_warehouse_client_performance_etl via data/pipelines/pipeline.py."""
    body = payload or TriggerPipelineRequest()
    env = os.environ.copy()
    if body.week_start:
        env["WEEK_START"] = body.week_start
    if body.force_notify_failure:
        env["FORCE_NOTIFY_FAILURE"] = "1"

    # Call the Prefect CLI entrypoint — ETL stays in data/pipelines/, not services/.
    try:
        completed = subprocess.run(
            [_pipeline_python(), str(_PIPELINES_DIR / "pipeline.py")],
            cwd=str(_REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed to start: {exc}",
        ) from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown error")[-2000:]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {detail}",
        )

    result: Dict[str, Any] = {}
    match = re.search(r"\{[\s\S]*\}\s*$", completed.stdout or "")
    if match:
        try:
            result = json.loads(match.group(0))
        except json.JSONDecodeError:
            result = {}

    latest = get_latest_pipeline_run() or {}
    return PipelineRunResponse(
        status=result.get("status") or latest.get("status") or "Completed",
        week_start=result.get("week_start") or (
            str(latest["week_start"]) if latest.get("week_start") is not None else None
        ),
        run_id=result.get("run_id") or latest.get("id"),
        records_processed=(
            result.get("records_processed")
            if result.get("records_processed") is not None
            else latest.get("records_processed")
        ),
        notify_status=result.get("notify_status"),
        error=result.get("error") or latest.get("error_message"),
    )
