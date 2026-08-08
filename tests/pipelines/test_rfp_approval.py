"""RFP approval, arbitration, and resume tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from data.pipelines.rfp_intake.approval.workflow import (
    interrupt_for_department,
    resume_department,
    run_arbitration_if_needed,
    start_approval_phase,
)
from data.pipelines.rfp_intake.checkpoints import load_checkpoint, reset_checkpoints, thread_id_for_department
from data.pipelines.rfp_intake.constants import DEPT_APPROVED, HUMAN_APPROVE, STATUS_DONE
from data.pipelines.rfp_intake.models import SectionDraft
from data.pipelines.rfp_intake.pipeline import run_rfp_intake_pipeline, save_uploaded_document
from data.pipelines.rfp_intake.store import get_rfp_store, merge_draft, reset_rfp_store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "rfp"


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_STORE_BACKEND", "memory")
    reset_rfp_store()
    reset_checkpoints()


def _prepare_ticket() -> str:
    ticket_id = save_uploaded_document(
        filename="luna_cosmetics_rfp.txt",
        content=(FIXTURES / "luna_cosmetics_rfp.txt").read_bytes(),
    )
    run_rfp_intake_pipeline(ticket_id)
    return ticket_id


def test_interrupt_and_resume_approve() -> None:
    ticket_id = _prepare_ticket()
    start_approval_phase(ticket_id)
    checkpoint = load_checkpoint(thread_id_for_department(ticket_id, "warehouse"))
    assert checkpoint is not None
    assert checkpoint["awaiting_human"] is True
    result = resume_department(ticket_id, "warehouse", HUMAN_APPROVE)
    assert result["status"] == DEPT_APPROVED


def test_parallel_approve_b_while_a_interrupted() -> None:
    ticket_id = _prepare_ticket()
    start_approval_phase(ticket_id)
    checkpoint_a = load_checkpoint(thread_id_for_department(ticket_id, "warehouse"))
    assert checkpoint_a is not None
    assert checkpoint_a["awaiting_human"] is True
    resume_department(ticket_id, "lastmile", HUMAN_APPROVE)
    checkpoint_a_after = load_checkpoint(thread_id_for_department(ticket_id, "warehouse"))
    assert checkpoint_a_after is not None
    assert checkpoint_a_after["awaiting_human"] is True
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.department_progress["lastmile"].status == DEPT_APPROVED


def test_arbitration_resolves_volume_vs_capacity() -> None:
    ticket_id = _prepare_ticket()
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    assert ticket is not None
    ticket = merge_draft(
        ticket,
        SectionDraft(
            department_id="warehouse",
            content="Warehouse section",
            structured_claims={"warehouse_capacity_units": 4000, "monthly_volume_assumed": 4000},
        ),
    )
    ticket = merge_draft(
        ticket,
        SectionDraft(
            department_id="lastmile",
            content="Last mile section",
            structured_claims={"monthly_volume": 5000, "quoted_currency": "USD"},
        ),
    )
    store.save_ticket(ticket)
    decisions = run_arbitration_if_needed(ticket_id)
    assert decisions
    assert decisions[0]["conflict_type"] == "volume-vs-capacity"


def test_all_departments_approved_finalizes_document() -> None:
    ticket_id = _prepare_ticket()
    start_approval_phase(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    for summary in ticket.department_summaries:
        resume_department(ticket_id, summary.department_id, HUMAN_APPROVE)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.status == STATUS_DONE
    assert ticket.final_document
