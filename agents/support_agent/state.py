"""Minimal explicit state for the support knowledge agent graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    user_id: str
    thread_id: str
    route: str
    chunks: list[dict[str, Any]]
    context: str
    answer: str
    sources: list[dict[str, str]]
    tool_input: dict[str, Any]
    tool_result: dict[str, Any]
    sources_used: Annotated[list[str], operator.add]
    error: Optional[str]
    trace: Annotated[list[dict[str, Any]], operator.add]
    user_memory_context: str
    pending_proposal: Optional[dict[str, Any]]
    memory_proposal: Optional[dict[str, Any]]
    memory_intent: Optional[str]
    memory_edit_text: Optional[str]
    guardrail_blocked: bool
    guardrail_type: Optional[str]
    guardrail_rule: Optional[str]
    casual_steer: bool
