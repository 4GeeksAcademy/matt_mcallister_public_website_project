"""TrackFlow commercial knowledge support agent (LangGraph)."""

from __future__ import annotations

__all__ = ["get_checkpoint_state", "get_trace", "run_agent"]


def __getattr__(name: str):
    if name == "get_checkpoint_state":
        from agents.support_agent.graph import get_checkpoint_state

        return get_checkpoint_state
    if name == "run_agent":
        from agents.support_agent.graph import run_agent

        return run_agent
    if name == "get_trace":
        from agents.support_agent.trace import get_trace

        return get_trace
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
