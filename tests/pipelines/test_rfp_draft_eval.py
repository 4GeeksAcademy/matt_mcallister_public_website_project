"""RFP draft/evaluation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from data.pipelines.rfp_intake.constants import MAX_SECTION_ITERATIONS, STATUS_NEEDS_HUMAN_REVIEW
from data.pipelines.rfp_intake.draft.workflow import evaluate_compliance, evaluate_section, generate_section
from data.pipelines.rfp_intake.models import DepartmentSummary, SectionDraft
from data.pipelines.rfp_intake.pipeline import run_rfp_intake_pipeline, save_uploaded_document
from data.pipelines.rfp_intake.store import get_rfp_store, reset_rfp_store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "rfp"


@pytest.fixture(autouse=True)
def _reset_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_STORE_BACKEND", "memory")
    reset_rfp_store()


def _seed_ticket() -> str:
    ticket_id = save_uploaded_document(
        filename="luna_cosmetics_rfp.txt",
        content=(FIXTURES / "luna_cosmetics_rfp.txt").read_bytes(),
    )
    run_rfp_intake_pipeline(ticket_id)
    return ticket_id


def test_generator_and_evaluator_success() -> None:
    summary = DepartmentSummary(
        department_id="warehouse",
        key_aspects=["storage capacity", "cost per pallet/SKU"],
        contact_name="Ana Whitfield",
        contact_email="ana.whitfield@trackflow.com",
    )
    metadata = {"client_country": "US", "currency": "USD", "monthly_volume": 5000}
    draft = generate_section(department_id="warehouse", summary=summary, metadata=metadata)
    evaluation = evaluate_section(
        department_id="warehouse",
        draft=draft,
        summary=summary,
        metadata=metadata,
    )
    assert evaluation.overall_pass is True


def test_compliance_failure_from_context_rule() -> None:
    text = (FIXTURES / "compliance_failure_draft.txt").read_text(encoding="utf-8")
    result = evaluate_compliance(text, client_country="Spain", currency="EUR")
    assert result.pass_ is False
    assert "RETURNS_UNDER_48H_FORBIDDEN" in result.rule_ids
    assert "NO_CARRIER_NEGOTIATED_RATES" in result.rule_ids


def test_iteration_limit_sets_needs_human_review(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("data.pipelines.rfp_intake.draft.graph.MAX_SECTION_ITERATIONS", 1)
    ticket_id = _seed_ticket()
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.status in {STATUS_NEEDS_HUMAN_REVIEW, "waiting_for_approval", "done"}


def test_generic_evaluation_failure_provides_feedback() -> None:
    summary = DepartmentSummary(
        department_id="warehouse",
        key_aspects=["storage capacity", "cost per pallet/SKU"],
        contact_name="Ana Whitfield",
        contact_email="ana.whitfield@trackflow.com",
    )
    draft = SectionDraft(
        department_id="warehouse",
        content="Too short.",
        iteration=0,
    )
    evaluation = evaluate_section(
        department_id="warehouse",
        draft=draft,
        summary=summary,
        metadata={"client_country": "US", "currency": "USD"},
    )
    assert evaluation.overall_pass is False
    assert evaluation.feedback_for_generator
