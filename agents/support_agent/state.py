"""Minimal explicit state for the support knowledge agent graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    chunks: list[dict[str, Any]]
    context: str
    answer: str
    sources: list[dict[str, str]]
    error: Optional[str]
    trace: Annotated[list[dict[str, Any]], operator.add]
