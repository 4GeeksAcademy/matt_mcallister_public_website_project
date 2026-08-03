"""Pipeline trigger and status endpoints for TrackFlow warehouse telemetry ETL."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User

# Import flows from monorepo data/pipelines (do not duplicate ETL logic here).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_PIPELINES_DIR = _REPO_ROOT / "data" / "pipelines"
if str(_PIPELINES_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINES_DIR))

from pipeline import (  # noqa: E402
    get_latest_pipeline_run,
    weekly_warehouse_client_performance_etl,
)


router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineRunResponse(BaseModel):
    status: str
    flow_run_id: Optional[str] = None
    records_processed: Optional[int] = None
    notify_status: Optional[str] = None
    error: Optional[str] = None


class PipelineLatestRunResponse(BaseModel):
    id: Optional[str] = None
    flow_run_id: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    records_processed: Optional[int] = None
    status: str
    error_message: Optional[str] = None


class TriggerPipelineRequest(BaseModel):
    force_notify_failure: bool = Field(
        default=False,
        description="Force optional notify step to fail without failing the ETL.",
    )


@router.get("/runs/latest", response_model=PipelineLatestRunResponse)
def get_latest_run(
    current_user: User = Depends(get_current_user),
) -> PipelineLatestRunResponse:
    """Return status and metadata for the most recent warehouse ETL run."""
    _ = current_user
    latest = get_latest_pipeline_run()
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pipeline runs recorded yet",
        )
    return PipelineLatestRunResponse(**latest)


@router.post(
    "/runs",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_pipeline_run(
    payload: Optional[TriggerPipelineRequest] = None,
    current_user: User = Depends(get_current_user),
) -> PipelineRunResponse:
    """Manually trigger the canonical weekly warehouse performance ETL."""
    _ = current_user
    options = payload or TriggerPipelineRequest()
    result: Dict[str, Any] = weekly_warehouse_client_performance_etl(
        force_notify_failure=options.force_notify_failure
    )
    return PipelineRunResponse(
        status=result.get("status", "Unknown"),
        flow_run_id=result.get("flow_run_id") or result.get("run_id"),
        records_processed=result.get("records_processed"),
        notify_status=result.get("notify_status"),
        error=result.get("error"),
    )
