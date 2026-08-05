"""Single-responsibility LangGraph nodes for the support knowledge agent."""

from __future__ import annotations

from typing import Any, Callable

from agents.tools.incident_lookup import (
    MSG_UNAVAILABLE,
    TicketLookupInput,
    TicketLookupResult,
    classify_question_route,
    format_ticket_answer,
    lookup_incident,
    parse_ticket_intent,
)
from data.pipelines.rag import (
    FAITHFULNESS_REJECTION_MESSAGE,
    NO_CONTEXT_MESSAGE,
    build_context,
    check_faithfulness,
    citation_metadata,
    generate_answer,
    retrieve,
)

from agents.support_agent.state import AgentState
from agents.support_agent.trace import make_trace_entry


def _next_step(state: AgentState) -> int:
    return len(state.get("trace") or []) + 1


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
    lookup_callable = lookup_fn or lookup_incident

    def ticket_lookup_node(state: AgentState) -> dict[str, Any]:
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
                    "ticket_lookup_node",
                    step=step,
                    output_summary={
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

    return ticket_lookup_node


def ticket_format_answer(state: AgentState) -> dict[str, Any]:
    result = TicketLookupResult.model_validate(state.get("tool_result") or {})
    answer = format_ticket_answer(result)
    step = _next_step(state)
    return {
        "answer": answer,
        "sources": [],
        "sources_used": ["ticket_tool"],
        "trace": [
            make_trace_entry(
                "format_ticket_answer",
                step=step,
                output_summary={
                    "ok": result.ok,
                    "answer_chars": len(answer),
                    "source": "ticket_tool",
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
        chunks = retrieve_callable(question)
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
