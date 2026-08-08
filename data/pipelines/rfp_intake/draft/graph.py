"""Part 2 draft/evaluation workflow."""

from __future__ import annotations

from typing import Any

from data.pipelines.rfp_intake.constants import (
    DEPT_NEEDS_REVIEW,
    DEPT_PENDING,
    MAX_SECTION_ITERATIONS,
    STATUS_DRAFTING,
    STATUS_NEEDS_HUMAN_REVIEW,
    STATUS_UNDER_EVALUATION,
    STATUS_WAITING_APPROVAL,
)
from data.pipelines.rfp_intake.draft.workflow import (
    evaluate_section,
    evaluate_sections_parallel,
    generate_section,
)
from data.pipelines.rfp_intake.models import DepartmentProgress, NodeLogEntry, SectionDraft
from data.pipelines.rfp_intake.store import get_rfp_store, merge_draft, merge_evaluation


def _summary_map(ticket) -> dict[str, Any]:
    return {item.department_id: item for item in ticket.department_summaries}


def run_draft_eval_for_department(ticket_id: str, department_id: str) -> None:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    summaries = _summary_map(ticket)
    summary = summaries[department_id]
    metadata = ticket.metadata
    ticket.status = STATUS_DRAFTING
    store.save_ticket(ticket)

    previous = ticket.drafts.get(department_id)
    feedback = ""
    if previous and ticket.evaluations.get(department_id):
        feedback = ticket.evaluations[department_id].feedback_for_generator

    draft = generate_section(
        department_id=department_id,
        summary=summary,
        metadata=metadata,
        previous_draft=previous,
        feedback=feedback,
    )
    ticket = merge_draft(ticket, draft)
    ticket.status = STATUS_UNDER_EVALUATION
    store.save_ticket(ticket)
    store.append_node_log(
        NodeLogEntry(
            ticket_id=ticket_id,
            department_id=department_id,
            node="generate_section",
            agent=f"generator_{department_id}",
            input_summary=f"iteration={draft.iteration}",
            output_summary=f"chars={len(draft.content)}",
        )
    )

    evaluation = evaluate_section(
        department_id=department_id,
        draft=draft,
        summary=summary,
        metadata=metadata,
    )
    ticket = store.get_ticket(ticket_id)
    assert ticket is not None
    ticket = merge_evaluation(ticket, evaluation)
    progress = ticket.department_progress.get(department_id) or DepartmentProgress(
        department_id=department_id
    )
    if evaluation.overall_pass:
        progress.status = DEPT_PENDING
        ticket.status = STATUS_WAITING_APPROVAL
    elif draft.iteration + 1 >= MAX_SECTION_ITERATIONS:
        progress.status = DEPT_NEEDS_REVIEW
        ticket.status = STATUS_NEEDS_HUMAN_REVIEW
    else:
        progress.status = DEPT_PENDING
        ticket.status = STATUS_DRAFTING
    ticket.department_progress[department_id] = progress
    store.save_ticket(ticket)
    store.append_node_log(
        NodeLogEntry(
            ticket_id=ticket_id,
            department_id=department_id,
            node="evaluate_section",
            agent=f"evaluator_{department_id}",
            input_summary=f"iteration={draft.iteration}",
            output_summary=f"overall_pass={evaluation.overall_pass}",
        )
    )


def run_draft_eval_all_departments(ticket_id: str) -> None:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    summaries = _summary_map(ticket)

    for department_id in summaries:
        iteration = 0
        while iteration < MAX_SECTION_ITERATIONS:
            run_draft_eval_for_department(ticket_id, department_id)
            ticket = store.get_ticket(ticket_id)
            assert ticket is not None
            evaluation = ticket.evaluations.get(department_id)
            if evaluation and evaluation.overall_pass:
                break
            draft = ticket.drafts.get(department_id)
            iteration = draft.iteration + 1 if draft else iteration + 1
            if ticket.status == STATUS_NEEDS_HUMAN_REVIEW:
                break


def run_parallel_evaluation_batch(ticket_id: str, department_ids: list[str]) -> None:
    store = get_rfp_store()
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {ticket_id}")
    summaries = _summary_map(ticket)
    metadata = ticket.metadata
    items = []
    for department_id in department_ids:
        draft = ticket.drafts.get(department_id)
        if draft is None:
            draft = generate_section(
                department_id=department_id,
                summary=summaries[department_id],
                metadata=metadata,
            )
            ticket = merge_draft(ticket, draft)
        items.append((draft, summaries[department_id], metadata))
    results = evaluate_sections_parallel(items)
    ticket = store.get_ticket(ticket_id)
    assert ticket is not None
    for evaluation in results:
        ticket = merge_evaluation(ticket, evaluation)
    store.save_ticket(ticket)
