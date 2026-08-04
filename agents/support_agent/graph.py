"""Compiled LangGraph for the TrackFlow commercial knowledge support agent."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.support_agent.nodes import (
    make_generate_node,
    make_retrieve_node,
    no_context_response,
    receive_question,
    set_error,
)
from agents.support_agent.state import AgentState
from agents.support_agent.trace import get_trace, store_trace

_CHECKPOINTER = MemorySaver()
_COMPILED_GRAPH = None


def _route_after_receive(state: AgentState) -> str:
    if state.get("error"):
        return "set_error"
    return "retrieve_node"


def _route_after_retrieve(state: AgentState) -> str:
    if not state.get("chunks"):
        return "no_context_response"
    return "generate_node"


def build_graph(
    *,
    retrieve_fn: Optional[Callable[..., list[dict]]] = None,
    openai_client: Any | None = None,
):
    graph = StateGraph(AgentState)
    graph.add_node("receive_question", receive_question)
    graph.add_node("set_error", set_error)
    graph.add_node("retrieve_node", make_retrieve_node(retrieve_fn))
    graph.add_node("no_context_response", no_context_response)
    graph.add_node("generate_node", make_generate_node(openai_client=openai_client))

    graph.set_entry_point("receive_question")
    graph.add_conditional_edges(
        "receive_question",
        _route_after_receive,
        {"set_error": "set_error", "retrieve_node": "retrieve_node"},
    )
    graph.add_edge("set_error", END)
    graph.add_conditional_edges(
        "retrieve_node",
        _route_after_retrieve,
        {
            "no_context_response": "no_context_response",
            "generate_node": "generate_node",
        },
    )
    graph.add_edge("no_context_response", END)
    graph.add_edge("generate_node", END)
    return graph.compile(checkpointer=_CHECKPOINTER)


def get_compiled_graph(
    *,
    retrieve_fn: Optional[Callable[..., list[dict]]] = None,
    openai_client: Any | None = None,
):
    global _COMPILED_GRAPH
    if retrieve_fn is not None or openai_client is not None:
        return build_graph(retrieve_fn=retrieve_fn, openai_client=openai_client)
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph()
    return _COMPILED_GRAPH


def run_agent(
    question: str,
    *,
    thread_id: Optional[str] = None,
    retrieve_fn: Optional[Callable[..., list[dict]]] = None,
    openai_client: Any | None = None,
) -> dict[str, Any]:
    """Execute the compiled graph and return answer, sources, and trace_id."""
    run_id = thread_id or str(uuid.uuid4())
    compiled = get_compiled_graph(
        retrieve_fn=retrieve_fn,
        openai_client=openai_client,
    )
    config = {"configurable": {"thread_id": run_id}}
    initial_state: AgentState = {
        "question": question,
        "chunks": [],
        "context": "",
        "answer": "",
        "sources": [],
        "error": None,
        "trace": [],
    }
    result = compiled.invoke(initial_state, config=config)
    trace = list(result.get("trace") or [])
    store_trace(run_id, trace)
    return {
        "answer": result.get("answer") or "",
        "sources": result.get("sources") or [],
        "trace_id": run_id,
    }


def get_checkpoint_state(thread_id: str) -> Optional[dict[str, Any]]:
    """Return the latest checkpointed graph state for inspection."""
    compiled = get_compiled_graph()
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = compiled.get_state(config)
    if snapshot is None or snapshot.values is None:
        return None
    return dict(snapshot.values)
