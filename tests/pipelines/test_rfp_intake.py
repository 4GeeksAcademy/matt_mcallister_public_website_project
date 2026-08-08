"""RFP intake tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from data.pipelines.rfp_intake.constants import STATUS_DISCARDED, STATUS_INTAKE_COMPLETE
from data.pipelines.rfp_intake.intake.workflow import (
    classify_document,
    extract_metadata,
    orchestrate_departments,
    run_department_worker,
)
from data.pipelines.rfp_intake.pipeline import run_rfp_intake_only, save_uploaded_document
from data.pipelines.rfp_intake.store import get_rfp_store, reset_rfp_store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "rfp"


@pytest.fixture(autouse=True)
def _reset_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_STORE_BACKEND", "memory")
    reset_rfp_store()


def test_classifier_accepts_modaviva_rfp() -> None:
    text = (FIXTURES / "modaviva_rfp.txt").read_text(encoding="utf-8")
    assert classify_document(text)["is_rfp"] is True


def test_classifier_accepts_luna_rfp() -> None:
    text = (FIXTURES / "luna_cosmetics_rfp.txt").read_text(encoding="utf-8")
    assert classify_document(text)["is_rfp"] is True


def test_classifier_rejects_carrier_pitch() -> None:
    text = (FIXTURES / "carrier_pitch.txt").read_text(encoding="utf-8")
    assert classify_document(text)["is_rfp"] is False


def test_orchestrator_scopes_modaviva_to_warehouse_and_reverse() -> None:
    text = (FIXTURES / "modaviva_rfp.txt").read_text(encoding="utf-8")
    metadata = extract_metadata(text)
    assert set(metadata["departments_needed"]) == {"warehouse", "reverse"}
    assert "lastmile" not in metadata["departments_needed"]


def test_orchestrator_scopes_luna_to_warehouse_and_lastmile() -> None:
    text = (FIXTURES / "luna_cosmetics_rfp.txt").read_text(encoding="utf-8")
    departments = orchestrate_departments(text)
    assert set(departments) == {"warehouse", "lastmile"}


def test_metadata_extracts_country_and_volume() -> None:
    text = (FIXTURES / "luna_cosmetics_rfp.txt").read_text(encoding="utf-8")
    metadata = extract_metadata(text)
    assert metadata["client_country"] == "US"
    assert metadata["currency"] == "USD"
    assert metadata["monthly_volume"] == 5000


def test_warehouse_worker_extracts_key_aspects() -> None:
    text = (FIXTURES / "modaviva_rfp.txt").read_text(encoding="utf-8")
    summary = run_department_worker("warehouse", text)
    assert summary.contact_name == "Ana Whitfield"
    assert summary.key_aspects


def test_intake_pipeline_stops_at_intake_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_RUN_SYNC", "true")
    ticket_id = save_uploaded_document(
        filename="luna_cosmetics_rfp.txt",
        content=(FIXTURES / "luna_cosmetics_rfp.txt").read_bytes(),
    )
    run_rfp_intake_only(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.status == STATUS_INTAKE_COMPLETE
    assert len(ticket.department_summaries) == 2
    assert ticket.metadata["client_country"] == "US"
    assert ticket.readability_metrics["word_count"] > 0


def test_carrier_pitch_is_discarded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_RUN_SYNC", "true")
    ticket_id = save_uploaded_document(
        filename="carrier_pitch.txt",
        content=(FIXTURES / "carrier_pitch.txt").read_bytes(),
    )
    run_rfp_intake_only(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.status == STATUS_DISCARDED
