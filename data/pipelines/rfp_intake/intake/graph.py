"""Part 1 intake LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from data.pipelines.rfp_intake.constants import STATUS_DISCARDED, STATUS_INTAKE_COMPLETE
from data.pipelines.rfp_intake.intake.workflow import (
    classify_document,
    orchestrate_departments,
    synthesize_intake,
)
from data.pipelines.rfp_intake.models import NodeLogEntry
from data.pipelines.rfp_intake.store import get_rfp_store, merge_department_summary


class IntakeState(TypedDict, total=False):
    ticket_id: str
    document_text: str
    is_rfp: bool
    discard_reason: str
    department_ids: list[str]
    node_logs: list[dict[str, Any]]


def _log(state: IntakeState, *, node: str, agent: str, input_summary: str, output_summary: str) -> dict[str, Any]:
    entry = NodeLogEntry(
        ticket_id=state["ticket_id"],
        node=node,
        agent=agent,
        input_summary=input_summary,
        output_summary=output_summary,
    )
    get_rfp_store().append_node_log(entry)
    logs = list(state.get("node_logs") or [])
    logs.append(entry.model_dump())
    return {"node_logs": logs}


def classify_node(state: IntakeState) -> dict[str, Any]:
    result = classify_document(state["document_text"])
    update = {
        "is_rfp": result["is_rfp"],
        "discard_reason": "" if result["is_rfp"] else result["reason"],
    }
    update.update(
        _log(
            state,
            node="classify_document",
            agent="rfp_classifier",
            input_summary=f"chars={len(state['document_text'])}",
            output_summary=str(result),
        )
    )
    return update


def orchestrator_node(state: IntakeState) -> dict[str, Any]:
    department_ids = orchestrate_departments(state["document_text"])
    update = {"department_ids": department_ids}
    update.update(
        _log(
            state,
            node="orchestrator",
            agent="rfp_orchestrator",
            input_summary="document_text",
            output_summary=f"departments={department_ids}",
        )
    )
    return update


def synthesizer_node(state: IntakeState) -> dict[str, Any]:
    store = get_rfp_store()
    ticket = store.get_ticket(state["ticket_id"])
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {state['ticket_id']}")
    department_ids = state.get("department_ids") or []
    summaries, payload = synthesize_intake(
        text=state["document_text"],
        department_ids=department_ids,
    )
    ticket.metadata = payload["metadata"]
    ticket.readability_metrics = payload["readability_metrics"]
    ticket.status = STATUS_INTAKE_COMPLETE
    for summary in summaries:
        ticket = merge_department_summary(ticket, summary)
    store.save_ticket(ticket)
    update = _log(
        state,
        node="synthesizer",
        agent="rfp_synthesizer",
        input_summary=f"departments={len(summaries)}",
        output_summary=STATUS_INTAKE_COMPLETE,
    )
    return update


def discard_node(state: IntakeState) -> dict[str, Any]:
    store = get_rfp_store()
    ticket = store.get_ticket(state["ticket_id"])
    if ticket is None:
        raise RuntimeError(f"Ticket not found: {state['ticket_id']}")
    ticket.status = STATUS_DISCARDED
    ticket.error_message = state.get("discard_reason")
    store.save_ticket(ticket)
    return _log(
        state,
        node="discard",
        agent="rfp_classifier",
        input_summary="non_rfp",
        output_summary=STATUS_DISCARDED,
    )


def _route_after_classify(state: IntakeState) -> str:
    return "orchestrator" if state.get("is_rfp") else "discard"


def build_intake_graph():
    graph = StateGraph(IntakeState)
    graph.add_node("classify_document", classify_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("discard", discard_node)
    graph.set_entry_point("classify_document")
    graph.add_conditional_edges("classify_document", _route_after_classify)
    graph.add_edge("orchestrator", "synthesizer")
    graph.add_edge("synthesizer", END)
    graph.add_edge("discard", END)
    return graph.compile()


def run_intake(*, ticket_id: str, document_text: str) -> dict[str, Any]:
    compiled = build_intake_graph()
    return compiled.invoke({"ticket_id": ticket_id, "document_text": document_text, "node_logs": []})
