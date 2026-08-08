"""FastAPI bridge for the Agentic RFP workflow."""

from __future__ import annotations

import os
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from data.pipelines.rfp_intake.approval.workflow import resume_department, start_approval_phase
from data.pipelines.rfp_intake.constants import (
    HUMAN_APPROVE,
    HUMAN_REJECT,
    HUMAN_REQUEST_CHANGES,
)
from data.pipelines.rfp_intake.pipeline import run_rfp_intake_pipeline, save_uploaded_document
from data.pipelines.rfp_intake.store import get_rfp_store, ticket_to_progress


class RfpUploadResponse(BaseModel):
    ticket_id: str
    status: str


class RfpResumeRequest(BaseModel):
    department_id: str
    decision: Literal["approve", "reject", "request_changes"]
    notes: str = ""


class RfpTicketResponse(BaseModel):
    ticket_id: str
    status: str
    filename: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    readability_metrics: dict[str, Any] = Field(default_factory=dict)
    departments: dict[str, Any] = Field(default_factory=dict)
    evaluations: dict[str, Any] = Field(default_factory=dict)
    has_final_document: bool = False
    error_message: Optional[str] = None


class RfpDocumentResponse(BaseModel):
    ticket_id: str
    document: str


def create_rfp_ticket(*, filename: str, content: bytes) -> RfpUploadResponse:
    ticket_id = save_uploaded_document(filename=filename, content=content)
    if os.environ.get("RFP_RUN_SYNC", "false").lower() == "true":
        run_rfp_intake_pipeline(ticket_id)
    else:
        try:
            from services.celery_app.tasks import run_rfp_intake

            run_rfp_intake.delay(ticket_id)
        except Exception:
            run_rfp_intake_pipeline(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    return RfpUploadResponse(ticket_id=ticket_id, status=ticket.status if ticket else "analyzing")


def get_rfp_ticket(ticket_id: str) -> RfpTicketResponse:
    ticket = get_rfp_store().get_ticket(ticket_id)
    if ticket is None:
        raise KeyError(ticket_id)
    payload = ticket_to_progress(ticket)
    return RfpTicketResponse(**payload)


def resume_rfp_ticket(ticket_id: str, body: RfpResumeRequest) -> dict[str, Any]:
    decision_map = {
        "approve": HUMAN_APPROVE,
        "reject": HUMAN_REJECT,
        "request_changes": HUMAN_REQUEST_CHANGES,
    }
    return resume_department(
        ticket_id,
        body.department_id,
        decision_map[body.decision],
        notes=body.notes,
    )


def get_rfp_document(ticket_id: str) -> RfpDocumentResponse:
    ticket = get_rfp_store().get_ticket(ticket_id)
    if ticket is None:
        raise KeyError(ticket_id)
    if not ticket.final_document:
        raise ValueError("Final document not ready")
    return RfpDocumentResponse(ticket_id=ticket_id, document=ticket.final_document)


def trigger_approval_phase(ticket_id: str) -> dict[str, Any]:
    return start_approval_phase(ticket_id)
