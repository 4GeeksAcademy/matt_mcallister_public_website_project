"""Thin FastAPI bridge to the TrackFlow RAG query pipeline."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from data.pipelines.rag import query as rag_query

logger = logging.getLogger(__name__)


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class KnowledgeQueryResponse(BaseModel):
    answer: str


def run_knowledge_query(question: str) -> dict[str, Any]:
    """Call pipeline query(); never expose raw Qdrant hits to the client."""
    answer = rag_query(question)
    logger.info("knowledge/query answered question=%r chars=%s", question[:80], len(answer))
    return {"answer": answer}
