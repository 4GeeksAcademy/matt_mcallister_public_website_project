"""Top-level RFP pipeline orchestration (Parts 1-3)."""

from __future__ import annotations

import traceback
from pathlib import Path

from data.pipelines.rfp_intake.approval.workflow import start_approval_phase
from data.pipelines.rfp_intake.checkpoints import clear_checkpoints
from data.pipelines.rfp_intake.constants import STATUS_DISCARDED, STATUS_FAILED, STATUS_INTAKE_COMPLETE
from data.pipelines.rfp_intake.draft.graph import run_draft_eval_all_departments
from data.pipelines.rfp_intake.intake.graph import run_intake
from data.pipelines.rfp_intake.pdf_utils import extract_document_text
from data.pipelines.rfp_intake.store import get_rfp_store


def run_rfp_intake_only(ticket_id: str) -> None:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    text = extract_document_text(ticket.pdf_path)
    run_intake(ticket_id=ticket_id, document_text=text)


def run_rfp_draft_pipeline(ticket_id: str) -> None:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    if ticket.status != STATUS_INTAKE_COMPLETE:
        raise RuntimeError(f"Ticket {ticket_id} is not ready for drafting (status={ticket.status})")
    run_draft_eval_all_departments(ticket_id)


def run_rfp_intake_pipeline(ticket_id: str) -> None:
    """Run Parts 1-3 sequentially with observable status transitions."""
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    try:
        run_rfp_intake_only(ticket_id)
        ticket = store.get_ticket(ticket_id)
        if ticket and ticket.status == STATUS_INTAKE_COMPLETE:
            run_rfp_draft_pipeline(ticket_id)
            start_approval_phase(ticket_id)
    except Exception as exc:
        ticket = store.get_ticket(ticket_id)
        if ticket and ticket.status != STATUS_DISCARDED:
            ticket.status = STATUS_FAILED
            ticket.error_message = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            store.save_ticket(ticket)
        raise


def save_uploaded_document(*, filename: str, content: bytes, repo_root: Path | None = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[3]
    target_dir = root / "data" / "raw" / "rfp"
    target_dir.mkdir(parents=True, exist_ok=True)
    store = get_rfp_store()
    ticket = store.create_ticket(filename=filename, pdf_path="")
    suffix = Path(filename).suffix.lower() or ".pdf"
    pdf_path = target_dir / f"{ticket.id}{suffix}"
    pdf_path.write_bytes(content)
    ticket.pdf_path = str(pdf_path)
    store.save_ticket(ticket)
    clear_checkpoints(ticket.id)
    return ticket.id
