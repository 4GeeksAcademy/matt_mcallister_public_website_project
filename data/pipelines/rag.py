"""Retrieval and generation pipeline for TrackFlow commercial knowledge RAG."""

from __future__ import annotations

import logging
import os
from typing import Any

from openai import OpenAI

from data.process.rag import (
    COLLECTION_NAME,
    DEFAULT_MIN_SCORE,
    embed,
    get_openai_client,
    get_qdrant_client,
)

logger = logging.getLogger(__name__)

GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are a TrackFlow salesperson / account manager assisting colleagues \
on client and prospect calls. Answer ONLY using the retrieved knowledge base context below.

Hard rules:
- Never invent rates, SLAs, timeframes, discounts, carrier exceptions, or policy terms.
- During declared high-demand dates (Black Friday, Cyber Monday, major Sales), do not \
promise standard delivery SLAs; follow the peak-demand warning in the context.
- International returns are never automatic — always describe them as manual handling.
- Any storage discount or off-rate-card pricing requires Miguel Torres's written approval; \
say so explicitly when discounts are discussed.
- If the context does not contain enough information, say honestly that the knowledge base \
does not have relevant information and do not invent company facts.
- Keep answers concise, commercial, and faithful to percentages, rates, and timeframes \
exactly as stated in the context.
"""


def retrieve(
    query: str,
    *,
    k: int = 5,
    min_score: float | None = None,
    qdrant_url: str | None = None,
    client: Any | None = None,
) -> list[dict]:
    """
    Embed the query, search Qdrant, and return payloads above min_score.

    May return fewer than k results when scores fall below the threshold.
    """
    threshold = DEFAULT_MIN_SCORE if min_score is None else min_score
    qdrant = client or get_qdrant_client(qdrant_url)
    vector = embed(query)

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=k,
        with_payload=True,
    )

    payloads: list[dict] = []
    for hit in results:
        score = float(getattr(hit, "score", 0.0) or 0.0)
        if score < threshold:
            logger.debug(
                "Dropping hit below min_score=%.3f (score=%.3f, id=%s)",
                threshold,
                score,
                getattr(hit, "id", None),
            )
            continue
        payload = dict(getattr(hit, "payload", None) or {})
        payload["_score"] = score
        payloads.append(payload)

    logger.info(
        "retrieve query=%r k=%s min_score=%s kept=%s",
        query[:80],
        k,
        threshold,
        len(payloads),
    )
    return payloads


def _build_context(chunks: list[dict]) -> str:
    blocks: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source_document", "unknown")
        section = chunk.get("section", "")
        text = chunk.get("text", "")
        blocks.append(
            f"[Chunk {i} | source={source} | section={section}]\n{text}"
        )
    return "\n\n".join(blocks)


def _generate(question: str, context: str, *, openai_client: OpenAI | None = None) -> str:
    client = openai_client or get_openai_client()
    user_prompt = (
        f"Retrieved context:\n{context}\n\n"
        f"Client / prospect question:\n{question}\n\n"
        "Respond as a TrackFlow salesperson using only the context."
    )
    response = client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def query(
    question: str,
    *,
    k: int = 5,
    min_score: float | None = None,
    qdrant_url: str | None = None,
    openai_client: OpenAI | None = None,
    retrieve_fn=None,
) -> str:
    """
    Primary RAG entry point: retrieve → prompt assembly → generation → answer string.
    """
    retrieve_callable = retrieve_fn or retrieve
    chunks = retrieve_callable(
        question, k=k, min_score=min_score, qdrant_url=qdrant_url
    )

    if not chunks:
        logger.info("No chunks above min_score for question=%r", question[:80])
        return (
            "I do not have relevant information in the TrackFlow knowledge base "
            "for that question, so I cannot confirm those terms. Please check with "
            "commercial leadership before making a commitment."
        )

    # Strip internal score before prompt assembly / never return raw search dumps
    context_chunks = [{k: v for k, v in c.items() if k != "_score"} for c in chunks]
    for chunk in chunks:
        logger.debug(
            "Using chunk source=%s section=%s score=%s",
            chunk.get("source_document"),
            chunk.get("section"),
            chunk.get("_score"),
        )

    context = _build_context(context_chunks)
    return _generate(question, context, openai_client=openai_client)
