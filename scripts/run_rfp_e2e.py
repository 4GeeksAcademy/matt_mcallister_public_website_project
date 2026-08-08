#!/usr/bin/env python3
"""Run the RFP E2E fixture path with simulated approvals."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("RFP_STORE_BACKEND", "memory")
os.environ.setdefault("RFP_RUN_SYNC", "true")

from data.pipelines.rfp_intake.approval.workflow import resume_department  # noqa: E402
from data.pipelines.rfp_intake.constants import HUMAN_APPROVE, STATUS_DONE  # noqa: E402
from data.pipelines.rfp_intake.pipeline import run_rfp_intake_pipeline, save_uploaded_document  # noqa: E402
from data.pipelines.rfp_intake.store import get_rfp_store  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "rfp" / "luna_cosmetics_rfp.txt"


def main() -> int:
    ticket_id = save_uploaded_document(
        filename="luna_cosmetics_rfp.txt",
        content=FIXTURE.read_bytes(),
    )
    run_rfp_intake_pipeline(ticket_id)
    ticket = get_rfp_store().get_ticket(ticket_id)
    if ticket is None:
        print("Ticket missing", file=sys.stderr)
        return 1
    for summary in ticket.department_summaries:
        resume_department(ticket_id, summary.department_id, HUMAN_APPROVE)
    ticket = get_rfp_store().get_ticket(ticket_id)
    if ticket is None or ticket.status != STATUS_DONE:
        print(f"Expected done, got {ticket.status if ticket else None}", file=sys.stderr)
        return 1
    print(f"RFP E2E complete: ticket_id={ticket_id} status={ticket.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
