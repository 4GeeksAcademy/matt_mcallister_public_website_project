"""Thin FastAPI bridge to the TrackFlow RAG query pipeline."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from data.pipelines.rag import query as rag_query

logger = logging.getLogger(__name__)


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class KnowledgeSource(BaseModel):
    source_document: str
    section: str
    language: str


class KnowledgeQueryResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSource]


def run_knowledge_query(question: str) -> dict[str, Any]:
    """Call pipeline query(); never expose raw Qdrant hits to the client."""
    result = rag_query(question)
    logger.info(
        "knowledge/query answered question=%r chars=%s sources=%s faithful=%s",
        question[:80],
        len(result["answer"]),
        len(result["sources"]),
        result["faithful"],
    )
    return {"answer": result["answer"], "sources": result["sources"]}
