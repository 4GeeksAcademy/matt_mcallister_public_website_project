"""Compiled LangGraph for the TrackFlow commercial knowledge support agent."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.memory.evaluator import MemoryEvaluation
from agents.support_agent.nodes import (
    bootstrap_memory,
    casual_steer_response,
    classify_route,
    guardrail_response,
    input_guardrails,
    make_generate_node,
    make_memory_self_evaluate_node,
    make_retrieve_node,
    make_ticket_lookup_node,
    memory_commit_or_discard,
    memory_intent_classifier,
    no_context_response,
    output_guardrails,
    receive_question,
    set_error,
    ticket_format_answer,
)
from agents.support_agent.state import AgentState
from agents.support_agent.trace import store_trace
from agents.tools.incident_lookup import TicketLookupInput, TicketLookupResult

_CHECKPOINTER = MemorySaver()
_COMPILED_GRAPH = None


def _route_after_receive(state: AgentState) -> str:
    if state.get("error"):
        return "set_error"
    return "bootstrap_memory"


def _route_after_bootstrap(state: AgentState) -> str:
    if state.get("pending_proposal"):
        return "memory_intent_classifier"
    return "input_guardrails"


def _route_after_input_guardrails(state: AgentState) -> str:
    if state.get("guardrail_blocked"):
        return "guardrail_response"
    if state.get("casual_steer"):
        return "casual_steer_response"
    return "classify_route"


def _route_after_classify(state: AgentState) -> str:
    if state.get("route") == "ticket":
        return "mcp_ticket_lookup_node"
    return "retrieve_node"


def _route_after_retrieve(state: AgentState) -> str:
    if not state.get("chunks"):
        return "no_context_response"
    return "generate_node"


def build_graph(
    *,
    retrieve_fn: Optional[Callable[..., list[dict]]] = None,
    lookup_fn: Optional[Callable[[TicketLookupInput], TicketLookupResult]] = None,
    openai_client: Any | None = None,
    memory_evaluator: Optional[Callable[..., MemoryEvaluation]] = None,
):
    graph = StateGraph(AgentState)
    graph.add_node("receive_question", receive_question)
    graph.add_node("bootstrap_memory", bootstrap_memory)
    graph.add_node("memory_intent_classifier", memory_intent_classifier)
    graph.add_node("memory_commit_or_discard", memory_commit_or_discard)
    graph.add_node("input_guardrails", input_guardrails)
    graph.add_node("guardrail_response", guardrail_response)
    graph.add_node("casual_steer_response", casual_steer_response)
    graph.add_node("classify_route", classify_route)
    graph.add_node("set_error", set_error)
    graph.add_node("mcp_ticket_lookup_node", make_ticket_lookup_node(lookup_fn))
    graph.add_node("format_ticket_answer", ticket_format_answer)
    graph.add_node("retrieve_node", make_retrieve_node(retrieve_fn))
    graph.add_node("no_context_response", no_context_response)
    graph.add_node("generate_node", make_generate_node(openai_client=openai_client))
    graph.add_node("output_guardrails", output_guardrails)
    graph.add_node(
        "memory_self_evaluate",
        make_memory_self_evaluate_node(memory_evaluator),
    )

    graph.set_entry_point("receive_question")
    graph.add_conditional_edges(
        "receive_question",
        _route_after_receive,
        {"set_error": "set_error", "bootstrap_memory": "bootstrap_memory"},
    )
    graph.add_edge("set_error", END)
    graph.add_conditional_edges(
        "bootstrap_memory",
        _route_after_bootstrap,
        {
            "memory_intent_classifier": "memory_intent_classifier",
            "input_guardrails": "input_guardrails",
        },
    )
    graph.add_edge("memory_intent_classifier", "memory_commit_or_discard")
    graph.add_edge("memory_commit_or_discard", "input_guardrails")
    graph.add_conditional_edges(
        "input_guardrails",
        _route_after_input_guardrails,
        {
            "guardrail_response": "guardrail_response",
            "casual_steer_response": "casual_steer_response",
            "classify_route": "classify_route",
        },
    )
    graph.add_edge("guardrail_response", END)
    graph.add_edge("casual_steer_response", "memory_self_evaluate")
    graph.add_conditional_edges(
        "classify_route",
        _route_after_classify,
        {"mcp_ticket_lookup_node": "mcp_ticket_lookup_node", "retrieve_node": "retrieve_node"},
    )
    graph.add_edge("mcp_ticket_lookup_node", "format_ticket_answer")
    graph.add_edge("format_ticket_answer", "memory_self_evaluate")
    graph.add_conditional_edges(
        "retrieve_node",
        _route_after_retrieve,
        {
            "no_context_response": "no_context_response",
            "generate_node": "generate_node",
        },
    )
    graph.add_edge("no_context_response", "memory_self_evaluate")
    graph.add_edge("generate_node", "output_guardrails")
    graph.add_edge("output_guardrails", "memory_self_evaluate")
    graph.add_edge("memory_self_evaluate", END)
    return graph.compile(checkpointer=_CHECKPOINTER)


def get_compiled_graph(
    *,
    retrieve_fn: Optional[Callable[..., list[dict]]] = None,
    lookup_fn: Optional[Callable[[TicketLookupInput], TicketLookupResult]] = None,
    openai_client: Any | None = None,
    memory_evaluator: Optional[Callable[..., MemoryEvaluation]] = None,
):
    global _COMPILED_GRAPH
    if (
        retrieve_fn is not None
        or lookup_fn is not None
        or openai_client is not None
        or memory_evaluator is not None
    ):
        return build_graph(
            retrieve_fn=retrieve_fn,
            lookup_fn=lookup_fn,
            openai_client=openai_client,
            memory_evaluator=memory_evaluator,
        )
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph()
    return _COMPILED_GRAPH


def run_agent(
    question: str,
    *,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    retrieve_fn: Optional[Callable[..., list[dict]]] = None,
    lookup_fn: Optional[Callable[[TicketLookupInput], TicketLookupResult]] = None,
    openai_client: Any | None = None,
    memory_evaluator: Optional[Callable[..., MemoryEvaluation]] = None,
) -> dict[str, Any]:
    """Execute the compiled graph and return answer, sources, and trace_id."""
    run_id = thread_id or str(uuid.uuid4())
    compiled = get_compiled_graph(
        retrieve_fn=retrieve_fn,
        lookup_fn=lookup_fn,
        openai_client=openai_client,
        memory_evaluator=memory_evaluator,
    )
    config = {"configurable": {"thread_id": run_id}}
    initial_state: AgentState = {
        "question": question,
        "thread_id": run_id,
        "user_id": user_id or run_id,
        "route": "",
        "chunks": [],
        "context": "",
        "answer": "",
        "sources": [],
        "tool_input": {},
        "tool_result": {},
        "sources_used": [],
        "error": None,
        "trace": [],
        "user_memory_context": "",
        "pending_proposal": None,
        "memory_proposal": None,
        "memory_intent": None,
        "memory_edit_text": None,
        "guardrail_blocked": False,
        "guardrail_type": None,
        "guardrail_rule": None,
        "casual_steer": False,
    }
    result = compiled.invoke(initial_state, config=config)
    trace = list(result.get("trace") or [])
    store_trace(run_id, trace)
    sources_used = list(result.get("sources_used") or [])
    return {
        "answer": result.get("answer") or "",
        "sources": result.get("sources") or [],
        "trace_id": run_id,
        "sources_used": sources_used,
        "memory_proposal": result.get("memory_proposal"),
        "pending_proposal": result.get("pending_proposal"),
        "guardrail_blocked": bool(result.get("guardrail_blocked")),
        "guardrail_type": result.get("guardrail_type"),
        "guardrail_rule": result.get("guardrail_rule"),
    }


def get_checkpoint_state(thread_id: str) -> Optional[dict[str, Any]]:
    """Return the latest checkpointed graph state for inspection."""
    compiled = get_compiled_graph()
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = compiled.get_state(config)
    if snapshot is None or snapshot.values is None:
        return None
    return dict(snapshot.values)
