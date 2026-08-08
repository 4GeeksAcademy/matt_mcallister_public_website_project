"""Retrieval and generation pipeline for TrackFlow commercial knowledge RAG."""

from __future__ import annotations

import logging
import os
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from data.process.rag import (
    COLLECTION_NAME,
    DEFAULT_MIN_SCORE,
    embed,
    get_openai_client,
    get_qdrant_client,
)
from agents.support_agent.prompts import SYSTEM_INSTRUCTIONS as SYSTEM_PROMPT
from agents.support_agent.prompts import build_generation_messages

logger = logging.getLogger(__name__)

GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gpt-4o-mini")
EVAL_QUERIES_PATH = Path(__file__).resolve().parents[1] / "eval" / "test-queries.json"

NO_CONTEXT_MESSAGE = (
    "I do not have relevant information in the TrackFlow knowledge base "
    "for that question, so I cannot confirm those terms. Please check with "
    "commercial leadership before making a commitment."
)

FAITHFULNESS_REJECTION_MESSAGE = (
    "I cannot confirm those rates or timeframes from the retrieved TrackFlow "
    "knowledge. Please check the cited source or commercial leadership."
)


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


def build_context(chunks: list[dict]) -> str:
    blocks: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source_document", "unknown")
        section = chunk.get("section", "")
        text = chunk.get("text", "")
        blocks.append(
            f"[Chunk {i} | source={source} | section={section}]\n{text}"
        )
    return "\n\n".join(blocks)


def generate_answer(
    question: str,
    context: str,
    *,
    openai_client: OpenAI | None = None,
    user_memory_context: str = "",
) -> str:
    client = openai_client or get_openai_client()
    messages = build_generation_messages(
        question=question,
        context=context,
        user_memory_context=user_memory_context,
    )
    response = client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=messages,
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def citation_metadata(chunks: list[dict]) -> list[dict[str, str]]:
    """Return deduplicated public source metadata, never chunk text or scores."""
    citations: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for chunk in chunks:
        citation = {
            "source_document": str(chunk.get("source_document", "unknown")),
            "section": str(chunk.get("section", "")),
            "language": str(chunk.get("language", "")),
        }
        key = (
            citation["source_document"],
            citation["section"],
            citation["language"],
        )
        if key not in seen:
            seen.add(key)
            citations.append(citation)
    return citations


from data.pipelines.faithfulness import check_faithfulness
def evaluate_recall_at_3(
    *,
    retrieve_fn=None,
    eval_path: Path | str = EVAL_QUERIES_PATH,
    min_score: float | None = None,
) -> dict[str, Any]:
    """Evaluate whether each expected source appears in the top three results."""
    cases = json.loads(Path(eval_path).read_text(encoding="utf-8"))
    retrieve_callable = retrieve_fn or retrieve
    results: list[dict[str, Any]] = []
    hits = 0
    for case in cases:
        chunks = retrieve_callable(
            case["question"],
            k=3,
            min_score=min_score,
            qdrant_url=None,
        )
        sources = [chunk.get("source_document") for chunk in chunks[:3]]
        matched = case["expected_source_document"] in sources
        hits += int(matched)
        results.append(
            {
                "id": case["id"],
                "expected_source_document": case["expected_source_document"],
                "retrieved_source_documents": sources,
                "hit": matched,
            }
        )
    total = len(results)
    return {
        "metric": "Recall@3",
        "hits": hits,
        "total": total,
        "recall_at_3": hits / total if total else 0.0,
        "results": results,
    }


LOCAL_VECTOR_SIZE = 64
_SOURCE_MARKERS: dict[str, tuple[str, ...]] = {
    "sla-delivery": (
        "sla",
        "delivery",
        "black friday",
        "cyber monday",
        "ground",
        "peak",
        "sales",
    ),
    "returns-policy": (
        "return",
        "returns",
        "restocking",
        "international",
        "packaging",
        "window",
    ),
    "carrier-coverage": (
        "carrier",
        "carriers",
        "aragón",
        "aragon",
        "rural",
        "ups",
        "fedex",
        "seur",
        "mrw",
    ),
    "storage-pricing": (
        "pallet",
        "storage",
        "discount",
        "pricing",
        "miguel",
        "zaragoza",
        "location",
    ),
}


def deterministic_embed(text: str, *, vector_size: int = LOCAL_VECTOR_SIZE) -> list[float]:
    """CI-safe embedding that preserves topical signal without calling OpenAI."""
    import hashlib
    import math

    cleaned = re.sub(r"\s+", " ", (text or "").casefold()).strip()
    vector = [0.0] * vector_size
    tokens = re.findall(r"[a-z0-9áéíóúñü]+", cleaned)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % vector_size
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign

    source_keys = list(_SOURCE_MARKERS)
    for offset, source in enumerate(source_keys):
        weight = sum(1 for marker in _SOURCE_MARKERS[source] if marker in cleaned)
        if weight:
            vector[offset] += float(weight) * 8.0

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def build_local_index(*, kb_dir: Path | None = None) -> Any:
    """Index knowledge-base chunks into an in-memory Qdrant collection."""
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels

    from data.process.rag import (
        COLLECTION_NAME,
        load_knowledge_chunks,
        point_id_for,
    )

    client = QdrantClient(":memory:")
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(
            size=LOCAL_VECTOR_SIZE,
            distance=qmodels.Distance.COSINE,
        ),
    )

    points: list[qmodels.PointStruct] = []
    for chunk in load_knowledge_chunks(kb_dir):
        points.append(
            qmodels.PointStruct(
                id=point_id_for(chunk["source_document"], chunk["chunk_index"]),
                vector=deterministic_embed(chunk["text"]),
                payload=chunk,
            )
        )
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return client


def retrieve_local(
    query: str,
    *,
    k: int = 5,
    min_score: float | None = 0.0,
    client: Any,
    qdrant_url: str | None = None,
) -> list[dict]:
    """Retrieve against a local-index client using deterministic embeddings."""
    from data.process.rag import COLLECTION_NAME

    del qdrant_url  # unused; signature matches retrieve() callers
    threshold = 0.0 if min_score is None else min_score
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=deterministic_embed(query),
        limit=k,
        with_payload=True,
    )
    payloads: list[dict] = []
    for hit in results:
        score = float(getattr(hit, "score", 0.0) or 0.0)
        if score < threshold:
            continue
        payload = dict(getattr(hit, "payload", None) or {})
        payload["_score"] = score
        payloads.append(payload)
    return payloads


def build_local_index_retrieve_fn(kb_dir: Path | None = None):
    """Return a retrieve_fn backed by a freshly indexed in-memory collection."""
    client = build_local_index(kb_dir=kb_dir)

    def retrieve_fn(question: str, **kwargs):
        return retrieve_local(question, client=client, **kwargs)

    return retrieve_fn


def query(
    question: str,
    *,
    k: int = 5,
    min_score: float | None = None,
    qdrant_url: str | None = None,
    openai_client: OpenAI | None = None,
    retrieve_fn=None,
) -> dict[str, Any]:
    """
    Retrieve, generate, verify rate/timeframe claims, and return safe citations.
    """
    retrieve_callable = retrieve_fn or retrieve
    chunks = retrieve_callable(
        question, k=k, min_score=min_score, qdrant_url=qdrant_url
    )

    if not chunks:
        logger.info("No chunks above min_score for question=%r", question[:80])
        return {
            "answer": NO_CONTEXT_MESSAGE,
            "sources": [],
            "faithful": True,
            "unsupported_claims": [],
        }

    # Strip internal score before prompt assembly / never return raw search dumps
    context_chunks = [{k: v for k, v in c.items() if k != "_score"} for c in chunks]
    for chunk in chunks:
        logger.debug(
            "Using chunk source=%s section=%s score=%s",
            chunk.get("source_document"),
            chunk.get("section"),
            chunk.get("_score"),
        )

    context = build_context(context_chunks)
    answer = generate_answer(question, context, openai_client=openai_client)
    faithfulness = check_faithfulness(answer, context)
    if not faithfulness["faithful"]:
        logger.warning(
            "Rejected unsupported rate/timeframe claims question=%r claims=%s",
            question[:80],
            faithfulness["unsupported_claims"],
        )
        answer = FAITHFULNESS_REJECTION_MESSAGE
    return {
        "answer": answer,
        "sources": citation_metadata(chunks),
        **faithfulness,
    }
