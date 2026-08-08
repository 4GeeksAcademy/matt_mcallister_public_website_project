"""End-to-end RFP workflow test with simulated approvals."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from data.pipelines.rfp_intake.approval.workflow import resume_department, start_approval_phase
from data.pipelines.rfp_intake.constants import HUMAN_APPROVE, STATUS_DONE, STATUS_INTAKE_COMPLETE
from data.pipelines.rfp_intake.pipeline import (
    run_rfp_draft_pipeline,
    run_rfp_intake_only,
    run_rfp_intake_pipeline,
    save_uploaded_document,
)
from data.pipelines.rfp_intake.store import get_rfp_store, reset_rfp_store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "rfp"


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_STORE_BACKEND", "memory")
    reset_rfp_store()


def test_rfp_lifecycle_part1_through_part3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_RUN_SYNC", "true")
    ticket_id = save_uploaded_document(
        filename="luna_cosmetics_rfp.txt",
        content=(FIXTURES / "luna_cosmetics_rfp.txt").read_bytes(),
    )
    run_rfp_intake_only(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.status == STATUS_INTAKE_COMPLETE
    run_rfp_draft_pipeline(ticket_id)
    start_approval_phase(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.department_summaries
    for summary in ticket.department_summaries:
        resume_department(ticket_id, summary.department_id, HUMAN_APPROVE)
    ticket = get_rfp_store().get_ticket(ticket_id)
    assert ticket is not None
    assert ticket.status == STATUS_DONE
    assert "Warehouse Operations" in (ticket.final_document or "")


def test_api_upload_and_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RFP_RUN_SYNC", "true")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    os.environ["RFP_STORE_BACKEND"] = "memory"
    import sys

    api_root = Path(__file__).resolve().parents[2] / "services" / "incident-api"
    sys.path.insert(0, str(api_root))
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    with (FIXTURES / "luna_cosmetics_rfp.txt").open("rb") as handle:
        upload = client.post(
            "/api/rfp/upload",
            files={"file": ("luna_cosmetics_rfp.txt", handle, "text/plain")},
        )
    assert upload.status_code == 200
    ticket_id = upload.json()["ticket_id"]
    run_rfp_intake_pipeline(ticket_id)
    detail = client.get(f"/api/rfp/{ticket_id}")
    assert detail.status_code == 200
    assert detail.json()["departments"]
