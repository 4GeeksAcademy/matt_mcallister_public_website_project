"""Thin FastAPI bridge to the TrackFlow LangGraph support agent."""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from agents.support_agent.graph import run_agent

logger = logging.getLogger(__name__)


class AgentQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    thread_id: Optional[str] = None


class AgentSource(BaseModel):
    source_document: str
    section: str
    language: str


class AgentQueryResponse(BaseModel):
    answer: str
    sources: list[AgentSource]
    trace_id: str


def run_agent_query(question: str, *, thread_id: Optional[str] = None) -> dict[str, Any]:
    """Invoke the compiled support agent graph."""
    result = run_agent(question.strip(), thread_id=thread_id)
    logger.info(
        "agent/query answered question=%r chars=%s sources=%s trace_id=%s",
        question[:80],
        len(result["answer"]),
        len(result.get("sources", [])),
        result["trace_id"],
    )
    return result
