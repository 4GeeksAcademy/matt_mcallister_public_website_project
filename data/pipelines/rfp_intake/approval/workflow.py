"""Part 3 approval, arbitration, and final document synthesis."""

from __future__ import annotations

from typing import Any

from data.pipelines.rfp_intake.arbitration import detect_structured_conflicts, resolve_conflict
from data.pipelines.rfp_intake.checkpoints import (
    load_checkpoint,
    save_checkpoint,
    thread_id_for_department,
)
from data.pipelines.rfp_intake.constants import (
    DEPT_APPROVED,
    DEPT_REJECTED,
    HUMAN_APPROVE,
    HUMAN_REJECT,
    HUMAN_REQUEST_CHANGES,
    STATUS_DONE,
    STATUS_DRAFTING,
    STATUS_WAITING_APPROVAL,
)
from data.pipelines.rfp_intake.draft.graph import run_draft_eval_for_department
from data.pipelines.rfp_intake.models import DepartmentProgress, NodeLogEntry
from data.pipelines.rfp_intake.store import get_rfp_store


def approval_summary(ticket_id: str, department_id: str) -> dict[str, Any]:
    ticket = get_rfp_store().get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    draft = ticket.drafts.get(department_id)
    evaluation = ticket.evaluations.get(department_id)
    return {
        "department_id": department_id,
        "draft_excerpt": (draft.content[:400] if draft else ""),
        "overall_pass": evaluation.overall_pass if evaluation else False,
        "compliance_violations": evaluation.compliance.violations if evaluation else [],
        "iteration": draft.iteration if draft else 0,
    }


def interrupt_for_department(ticket_id: str, department_id: str) -> dict[str, Any]:
    thread_id = thread_id_for_department(ticket_id, department_id)
    payload = {
        "ticket_id": ticket_id,
        "department_id": department_id,
        "awaiting_human": True,
        "approval_summary": approval_summary(ticket_id, department_id),
    }
    save_checkpoint(thread_id, payload)
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    ticket.status = STATUS_WAITING_APPROVAL
    progress = ticket.department_progress.get(department_id) or DepartmentProgress(
        department_id=department_id
    )
    progress.status = "waiting_for_approval"
    ticket.department_progress[department_id] = progress
    store.save_ticket(ticket)
    store.append_node_log(
        NodeLogEntry(
            ticket_id=ticket_id,
            department_id=department_id,
            node="interrupt",
            agent="approval_gate",
            input_summary="awaiting_human",
            output_summary="checkpoint_saved",
        )
    )
    return payload


def resume_department(
    ticket_id: str,
    department_id: str,
    decision: str,
    *,
    notes: str = "",
) -> dict[str, Any]:
    if decision not in {HUMAN_APPROVE, HUMAN_REJECT, HUMAN_REQUEST_CHANGES}:
        raise ValueError(f"Invalid decision: {decision}")
    thread_id = thread_id_for_department(ticket_id, department_id)
    checkpoint = load_checkpoint(thread_id)
    if checkpoint is None:
        raise RuntimeError(f"No checkpoint for {thread_id}")

    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    progress = ticket.department_progress.get(department_id) or DepartmentProgress(
        department_id=department_id
    )

    if decision == HUMAN_APPROVE:
        progress.status = DEPT_APPROVED
        ticket.department_progress[department_id] = progress
        store.save_ticket(ticket)
        store.append_node_log(
            NodeLogEntry(
                ticket_id=ticket_id,
                department_id=department_id,
                node="resume",
                agent="human_approver",
                input_summary=decision,
                output_summary=DEPT_APPROVED,
            )
        )
        save_checkpoint(thread_id, {**checkpoint, "awaiting_human": False, "decision": decision})
        maybe_finalize_ticket(ticket_id)
        return {"department_id": department_id, "status": DEPT_APPROVED}

    progress.status = DEPT_REJECTED
    ticket.department_progress[department_id] = progress
    ticket.status = STATUS_DRAFTING
    store.save_ticket(ticket)
    store.append_node_log(
        NodeLogEntry(
            ticket_id=ticket_id,
            department_id=department_id,
            node="resume",
            agent="human_approver",
            input_summary=f"{decision}:{notes}",
            output_summary="return_to_generator",
        )
    )
    save_checkpoint(thread_id, {**checkpoint, "awaiting_human": False, "decision": decision})
    run_draft_eval_for_department(ticket_id, department_id)
    return {"department_id": department_id, "status": DEPT_REJECTED}


def run_arbitration_if_needed(ticket_id: str) -> list[dict[str, Any]]:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    claims = {
        dept_id: draft.structured_claims
        for dept_id, draft in ticket.drafts.items()
    }
    draft_contents = {dept_id: draft.content for dept_id, draft in ticket.drafts.items()}
    conflicts = detect_structured_conflicts(
        claims,
        draft_contents=draft_contents,
        client_country=ticket.metadata.get("client_country", ""),
    )
    decisions = []
    for conflict in conflicts:
        decision = resolve_conflict(conflict)
        decisions.append(decision.__dict__)
        store.append_node_log(
            NodeLogEntry(
                ticket_id=ticket_id,
                department_id=decision.winning_department_id,
                node="arbitration",
                agent="context_arbiter",
                input_summary=conflict,
                output_summary=decision.details,
            )
        )
    return decisions


def maybe_finalize_ticket(ticket_id: str) -> bool:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    summaries = {item.department_id for item in ticket.department_summaries}
    approved = {
        dept_id
        for dept_id, progress in ticket.department_progress.items()
        if progress.status == DEPT_APPROVED
    }
    if summaries and summaries.issubset(approved):
        run_arbitration_if_needed(ticket_id)
        sections = []
        for dept_id in sorted(summaries):
            draft = ticket.drafts.get(dept_id)
            if draft:
                sections.append(draft.content)
        ticket.final_document = "\n\n".join(sections)
        ticket.status = STATUS_DONE
        store.save_ticket(ticket)
        store.append_node_log(
            NodeLogEntry(
                ticket_id=ticket_id,
                node="synthesize_final_document",
                agent="rfp_synthesizer",
                input_summary=f"departments={len(summaries)}",
                output_summary=STATUS_DONE,
            )
        )
        return True
    return False


def start_approval_phase(ticket_id: str) -> dict[str, Any]:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    interrupted = []
    for summary in ticket.department_summaries:
        interrupted.append(interrupt_for_department(ticket_id, summary.department_id))
    return {"ticket_id": ticket_id, "interrupted_departments": interrupted}
