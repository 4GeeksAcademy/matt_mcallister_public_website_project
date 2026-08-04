"""Append-only execution traces queryable after a graph run."""

from __future__ import annotations

from typing import Any

_TRACE_STORE: dict[str, list[dict[str, Any]]] = {}


def make_trace_entry(node: str, *, step: int, output_summary: dict[str, Any]) -> dict[str, Any]:
    return {"step": step, "node": node, "output_summary": output_summary}


def store_trace(trace_id: str, trace: list[dict[str, Any]]) -> None:
    _TRACE_STORE[trace_id] = list(trace)


def get_trace(trace_id: str) -> list[dict[str, Any]]:
    return list(_TRACE_STORE.get(trace_id, []))


def clear_traces() -> None:
    _TRACE_STORE.clear()
