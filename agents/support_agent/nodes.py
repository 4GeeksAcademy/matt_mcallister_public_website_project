"""Single-responsibility LangGraph nodes for the support knowledge agent."""

from __future__ import annotations

from typing import Any, Callable

from agents.guardrails.input import CASUAL_STEER_TEMPLATE, check_input_guardrails
from agents.guardrails.isolation import sanitize_chunks, sanitize_untrusted_content
from agents.guardrails.observability import record_guardrail_trigger
from agents.guardrails.output import check_output_guardrails
from agents.memory.audit import log_memory_event
from agents.memory.evaluator import MemoryEvaluation, evaluate_memory_candidate
from agents.memory.intent import classify_memory_intent
from agents.memory.policy import format_memory_context, validate_memory_candidate
from agents.memory.redis_store import get_memory_store
from agents.memory.store import MemoryProposal
from agents.mcp.ticket_lookup import lookup_incident_via_mcp
from agents.support_agent.prompts import build_generation_messages
from agents.tools.incident_lookup import (
    MSG_UNAVAILABLE,
    TicketLookupInput,
    TicketLookupResult,
    classify_question_route,
    format_ticket_answer,
    parse_ticket_intent,
)
from data.pipelines.faithfulness import check_faithfulness
from data.pipelines.rag import (
    FAITHFULNESS_REJECTION_MESSAGE,
    NO_CONTEXT_MESSAGE,
    build_context,
    citation_metadata,
    generate_answer,
    retrieve,
)

from agents.support_agent.state import AgentState
from agents.support_agent.trace import make_trace_entry


def _next_step(state: AgentState) -> int:
    return len(state.get("trace") or []) + 1


def _user_id(state: AgentState) -> str:
    return state.get("user_id") or state.get("thread_id") or "anonymous"


def receive_question(state: AgentState) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    step = _next_step(state)
    if not question:
        return {
            "question": "",
            "error": "A question is required.",
            "trace": [
                make_trace_entry(
                    "receive_question",
                    step=step,
                    output_summary={"valid": False, "reason": "empty_question"},
                )
            ],
        }
    return {
        "question": question,
        "error": None,
        "trace": [
            make_trace_entry(
                "receive_question",
                step=step,
                output_summary={"valid": True, "question_len": len(question)},
            )
        ],
    }


def bootstrap_memory(state: AgentState) -> dict[str, Any]:
    store = get_memory_store()
    user_id = _user_id(state)
    entries = store.list_entries(user_id)
    pending = store.get_pending_proposal(user_id)
    step = _next_step(state)
    return {
        "user_id": user_id,
        "user_memory_context": format_memory_context([e.to_dict() for e in entries]),
        "pending_proposal": pending.to_dict() if pending else None,
        "trace": [
            make_trace_entry(
                "bootstrap_memory",
                step=step,
                output_summary={
                    "memory_entries": len(entries),
                    "has_pending_proposal": pending is not None,
                },
            )
        ],
    }


def memory_intent_classifier(state: AgentState) -> dict[str, Any]:
    pending = state.get("pending_proposal") or {}
    result = classify_memory_intent(
        state.get("question") or "",
        proposal_text=str(pending.get("text") or ""),
    )
    step = _next_step(state)
    return {
        "memory_intent": result.label,
        "memory_edit_text": result.edited_text,
        "trace": [
            make_trace_entry(
                "memory_intent_classifier",
                step=step,
                output_summary={"intent": result.label},
            )
        ],
    }


def memory_commit_or_discard(state: AgentState) -> dict[str, Any]:
    store = get_memory_store()
    user_id = _user_id(state)
    pending_raw = state.get("pending_proposal")
    intent = state.get("memory_intent") or "topic_change"
    thread_id = state.get("thread_id") or user_id
    step = _next_step(state)
    committed = None
    outcome = intent

    if pending_raw and intent == "approve":
        decision = validate_memory_candidate(
            category=str(pending_raw.get("category") or "preference"),
            text=str(pending_raw.get("text") or ""),
        )
        if decision.allowed:
            committed = store.commit_entry(
                user_id,
                category=str(pending_raw.get("category") or "preference"),
                text=str(pending_raw.get("text") or ""),
            ).to_dict()
            outcome = "approved"
        else:
            outcome = "rejected_policy"
    elif pending_raw and intent == "edit":
        edited = state.get("memory_edit_text") or pending_raw.get("text")
        decision = validate_memory_candidate(
            category=str(pending_raw.get("category") or "preference"),
            text=str(edited or ""),
        )
        if decision.allowed:
            committed = store.commit_entry(
                user_id,
                category=str(pending_raw.get("category") or "preference"),
                text=str(edited or ""),
            ).to_dict()
            outcome = "edited"
        else:
            outcome = "rejected_policy"
    elif pending_raw and intent == "reject":
        outcome = "rejected"

    store.set_pending_proposal(user_id, None)
    if pending_raw:
        log_memory_event(
            thread_id=thread_id,
            user_id=user_id,
            proposal=pending_raw,
            user_message=state.get("question") or "",
            outcome=outcome,
            committed_entry=committed,
        )

    entries = store.list_entries(user_id)
    update: dict[str, Any] = {
        "pending_proposal": None,
        "memory_proposal": None,
        "user_memory_context": format_memory_context([e.to_dict() for e in entries]),
        "trace": [
            make_trace_entry(
                "memory_commit_or_discard",
                step=step,
                output_summary={"outcome": outcome, "committed": committed is not None},
            )
        ],
    }
    return update


def input_guardrails(state: AgentState) -> dict[str, Any]:
    result = check_input_guardrails(state.get("question") or "")
    step = _next_step(state)
    update: dict[str, Any] = {
        "guardrail_blocked": not result.allowed,
        "guardrail_type": result.guardrail_type,
        "guardrail_rule": result.rule,
        "casual_steer": bool(result.casual_brief),
        "trace": [
            make_trace_entry(
                "input_guardrails",
                step=step,
                output_summary={
                    "allowed": result.allowed,
                    "rule": result.rule,
                    "type": result.guardrail_type,
                },
            )
        ],
    }
    if not result.allowed:
        record_guardrail_trigger(
            rule=result.rule or "unknown",
            guardrail_type=result.guardrail_type or "security",
            thread_id=state.get("thread_id"),
            question=state.get("question"),
        )
        update["answer"] = result.response or ""
        update["sources"] = []
    elif result.casual_brief:
        record_guardrail_trigger(
            rule=result.rule or "casual_steer_back",
            guardrail_type=result.guardrail_type or "content",
            thread_id=state.get("thread_id"),
            question=state.get("question"),
        )
        update["answer"] = CASUAL_STEER_TEMPLATE.format(brief_answer=result.casual_brief)
        update["sources"] = []
        update["sources_used"] = ["guardrail"]
    return update


def guardrail_response(state: AgentState) -> dict[str, Any]:
    step = _next_step(state)
    return {
        "trace": [
            make_trace_entry(
                "guardrail_response",
                step=step,
                output_summary={
                    "rule": state.get("guardrail_rule"),
                    "type": state.get("guardrail_type"),
                },
            )
        ],
    }


def casual_steer_response(state: AgentState) -> dict[str, Any]:
    step = _next_step(state)
    return {
        "trace": [
            make_trace_entry(
                "casual_steer_response",
                step=step,
                output_summary={"source": "guardrail_casual_steer"},
            )
        ],
    }


def classify_route(state: AgentState) -> dict[str, Any]:
    route, signals = classify_question_route(state["question"])
    tool_input = (
        parse_ticket_intent(state["question"]).model_dump()
        if route == "ticket"
        else {}
    )
    step = _next_step(state)
    return {
        "route": route,
        "tool_input": tool_input,
        "trace": [
            make_trace_entry(
                "classify_route",
                step=step,
                output_summary={"route": route, **signals},
            )
        ],
    }


def set_error(state: AgentState) -> dict[str, Any]:
    message = state.get("error") or "Invalid request."
    step = _next_step(state)
    return {
        "answer": message,
        "sources": [],
        "trace": [
            make_trace_entry(
                "set_error",
                step=step,
                output_summary={"error": message},
            )
        ],
    }


def make_ticket_lookup_node(
    lookup_fn: Callable[[TicketLookupInput], TicketLookupResult] | None = None,
) -> Callable[[AgentState], dict[str, Any]]:
    lookup_callable = lookup_fn or lookup_incident_via_mcp

    def mcp_ticket_lookup_node(state: AgentState) -> dict[str, Any]:
        tool_input = TicketLookupInput.model_validate(state.get("tool_input") or {})
        try:
            result = lookup_callable(tool_input)
        except Exception:
            result = TicketLookupResult(
                ok=False,
                error_code="unavailable",
                error_message=MSG_UNAVAILABLE,
            )
        step = _next_step(state)
        return {
            "tool_result": result.model_dump(),
            "trace": [
                make_trace_entry(
                    "mcp_ticket_lookup_node",
                    step=step,
                    output_summary={
                        "transport": "mcp",
                        "http_method": result.http_method,
                        "http_path": result.http_path,
                        "ok": result.ok,
                        "error_code": result.error_code,
                        "incident_count": len(result.incidents),
                        "duration_ms": result.duration_ms,
                    },
                )
            ],
        }

    return mcp_ticket_lookup_node


def ticket_format_answer(state: AgentState) -> dict[str, Any]:
    result = TicketLookupResult.model_validate(state.get("tool_result") or {})
    raw = format_ticket_answer(result)
    answer = sanitize_untrusted_content(raw)
    step = _next_step(state)
    return {
        "answer": answer,
        "sources": [],
        "sources_used": ["mcp_ticket_tool"],
        "trace": [
            make_trace_entry(
                "format_ticket_answer",
                step=step,
                output_summary={
                    "ok": result.ok,
                    "answer_chars": len(answer),
                    "source": "mcp_ticket_tool",
                },
            )
        ],
    }


def make_retrieve_node(
    retrieve_fn: Callable[..., list[dict]] | None = None,
) -> Callable[[AgentState], dict[str, Any]]:
    retrieve_callable = retrieve_fn or retrieve

    def retrieve_node(state: AgentState) -> dict[str, Any]:
        question = state["question"]
        chunks = sanitize_chunks(retrieve_callable(question))
        source_documents = sorted(
            {str(chunk.get("source_document", "unknown")) for chunk in chunks}
        )
        step = _next_step(state)
        return {
            "chunks": chunks,
            "trace": [
                make_trace_entry(
                    "retrieve_node",
                    step=step,
                    output_summary={
                        "chunk_count": len(chunks),
                        "source_documents": source_documents,
                    },
                )
            ],
        }

    return retrieve_node


def no_context_response(state: AgentState) -> dict[str, Any]:
    step = _next_step(state)
    return {
        "answer": NO_CONTEXT_MESSAGE,
        "sources": [],
        "context": "",
        "sources_used": ["rag"],
        "trace": [
            make_trace_entry(
                "no_context_response",
                step=step,
                output_summary={"fallback": "no_chunks_above_threshold", "source": "rag"},
            )
        ],
    }


def make_generate_node(
    *,
    openai_client: Any | None = None,
) -> Callable[[AgentState], dict[str, Any]]:
    def generate_node(state: AgentState) -> dict[str, Any]:
        chunks = state.get("chunks") or []
        context_chunks = [{k: v for k, v in c.items() if k != "_score"} for c in chunks]
        context = build_context(context_chunks)
        answer = generate_answer(
            state["question"],
            context,
            openai_client=openai_client,
            user_memory_context=state.get("user_memory_context") or "",
        )
        faithfulness = check_faithfulness(answer, context)
        if not faithfulness["faithful"]:
            answer = FAITHFULNESS_REJECTION_MESSAGE
        step = _next_step(state)
        return {
            "context": context,
            "answer": answer,
            "sources": citation_metadata(chunks),
            "sources_used": ["rag"],
            "trace": [
                make_trace_entry(
                    "generate_node",
                    step=step,
                    output_summary={
                        "answer_chars": len(answer),
                        "source_count": len(chunks),
                        "faithful": faithfulness["faithful"],
                        "source": "rag",
                    },
                )
            ],
        }

    return generate_node


def output_guardrails(state: AgentState) -> dict[str, Any]:
    result = check_output_guardrails(
        state.get("answer") or "",
        context=state.get("context") or "",
        chunks=state.get("chunks") or [],
    )
    step = _next_step(state)
    update: dict[str, Any] = {
        "answer": result.answer or state.get("answer") or "",
        "trace": [
            make_trace_entry(
                "output_guardrails",
                step=step,
                output_summary={
                    "allowed": result.allowed,
                    "rule": result.rule,
                    "type": result.guardrail_type,
                },
            )
        ],
    }
    if not result.allowed:
        record_guardrail_trigger(
            rule=result.rule or "unknown",
            guardrail_type=result.guardrail_type or "content",
            thread_id=state.get("thread_id"),
            question=state.get("question"),
        )
        update["guardrail_blocked"] = True
        update["guardrail_type"] = result.guardrail_type
        update["guardrail_rule"] = result.rule
    return update


def make_memory_self_evaluate_node(
    evaluator: Callable[..., MemoryEvaluation] | None = None,
) -> Callable[[AgentState], dict[str, Any]]:
    evaluate = evaluator or evaluate_memory_candidate

    def memory_self_evaluate(state: AgentState) -> dict[str, Any]:
        store = get_memory_store()
        user_id = _user_id(state)
        if store.get_pending_proposal(user_id) is not None:
            step = _next_step(state)
            return {
                "trace": [
                    make_trace_entry(
                        "memory_self_evaluate",
                        step=step,
                        output_summary={"skipped": "pending_proposal_exists"},
                    )
                ]
            }

        evaluation = evaluate(
            user_id=user_id,
            question=state.get("question") or "",
            answer=state.get("answer") or "",
            route=state.get("route") or "knowledge",
            sources_used=list(state.get("sources_used") or []),
        )
        step = _next_step(state)
        update: dict[str, Any] = {
            "trace": [
                make_trace_entry(
                    "memory_self_evaluate",
                    step=step,
                    output_summary={
                        "remember": evaluation.remember,
                        "dismissal_reason": evaluation.dismissal_reason,
                    },
                )
            ]
        }
        if evaluation.remember and evaluation.memory_proposal:
            proposal = evaluation.memory_proposal
            store.set_pending_proposal(user_id, proposal)
            log_memory_event(
                thread_id=state.get("thread_id") or user_id,
                user_id=user_id,
                proposal=proposal.to_dict(),
                user_message=state.get("question") or "",
                outcome="proposed",
            )
            prompt = (
                f"\n\nShould I remember this for future conversations? "
                f"{proposal.text} (Reply approve, reject, or edit.)"
            )
            update["memory_proposal"] = proposal.to_dict()
            update["pending_proposal"] = proposal.to_dict()
            update["answer"] = (state.get("answer") or "") + prompt
        return update

    return memory_self_evaluate
