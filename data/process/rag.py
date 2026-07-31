"""Chunking, embedding, and Qdrant indexing for TrackFlow knowledge base."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION", "trackflow_knowledge")
COMPANY = "trackflow"
LANGUAGE = "en"
VECTOR_SIZE = int(os.environ.get("EMBEDDING_VECTOR_SIZE", "1536"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_MIN_SCORE = float(os.environ.get("RAG_MIN_SCORE", "0.55"))

# Maps filename stem fragment -> CONTEXT-company source_document value
SOURCE_DOCUMENT_BY_FILE = {
    "trackflow-sla-delivery.en.md": "sla-delivery",
    "trackflow-returns-policy.en.md": "returns-policy",
    "trackflow-carrier-coverage.en.md": "carrier-coverage",
    "trackflow-storage-pricing.en.md": "storage-pricing",
}

_POINT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def knowledge_base_dir() -> Path:
    return _repo_root() / "docs" / "company-knowledge-base"


def get_qdrant_client(url: str | None = None) -> QdrantClient:
    return QdrantClient(url=url or os.environ.get("QDRANT_URL", "http://localhost:6333"))


def get_openai_client() -> OpenAI:
    kwargs: dict[str, Any] = {"api_key": os.environ.get("OPENAI_API_KEY", "")}
    base_url = os.environ.get("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def normalize_text(text: str) -> str:
    """Light preprocessing before embedding."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def embed(text: str) -> list[float]:
    """Generate an embedding vector for a single string (index + query time)."""
    cleaned = normalize_text(text)
    client = get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=cleaned)
    return list(response.data[0].embedding)


def _split_markdown_sections(markdown: str) -> list[tuple[str, str]]:
    """Split markdown into (section_title, body) keeping heading boundaries intact."""
    lines = markdown.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_title = "Introduction"
    current_body: list[str] = []

    for line in lines:
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            if any(part.strip() for part in current_body):
                sections.append((current_title, current_body))
            current_title = heading.group(2).strip()
            current_body = []
            continue
        current_body.append(line)

    if any(part.strip() for part in current_body):
        sections.append((current_title, current_body))

    return [(title, "\n".join(body).strip()) for title, body in sections if "\n".join(body).strip()]


def chunk_document(markdown: str, *, source_document: str) -> list[dict[str, Any]]:
    """
    Heading-based semantic chunking.

    Each H1/H2/H3 section becomes one coherent chunk so rules and conditions
    are never split mid-sentence.
    """
    sections = _split_markdown_sections(markdown)
    chunks: list[dict[str, Any]] = []
    for index, (section, body) in enumerate(sections):
        text = normalize_text(f"{section}\n\n{body}")
        chunks.append(
            {
                "company": COMPANY,
                "source_document": source_document,
                "section": section,
                "language": LANGUAGE,
                "chunk_index": index,
                "text": text,
            }
        )
    return chunks


def load_knowledge_chunks(kb_dir: Path | None = None) -> list[dict[str, Any]]:
    root = kb_dir or knowledge_base_dir()
    all_chunks: list[dict[str, Any]] = []
    for filename, source_document in SOURCE_DOCUMENT_BY_FILE.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base file missing: {path}")
        markdown = path.read_text(encoding="utf-8")
        doc_chunks = chunk_document(markdown, source_document=source_document)
        if len(doc_chunks) < 3:
            raise ValueError(
                f"{filename} produced {len(doc_chunks)} chunks; need at least 3"
            )
        all_chunks.extend(doc_chunks)
    return all_chunks


def point_id_for(source_document: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_POINT_NAMESPACE, f"{source_document}:{chunk_index}"))


def ensure_collection(client: QdrantClient, *, recreate: bool = True) -> None:
    """
    Idempotency strategy: clear-and-reload.

    Recreate the collection on setup so re-running setup() never duplicates points.
    Deterministic UUIDv5 point IDs add a second safety net for upserts.
    """
    exists = client.collection_exists(COLLECTION_NAME)
    if recreate and exists:
        client.delete_collection(COLLECTION_NAME)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=VECTOR_SIZE,
                distance=qmodels.Distance.COSINE,
            ),
        )


def setup(
    *,
    qdrant_url: str | None = None,
    kb_dir: Path | None = None,
    recreate: bool = True,
) -> dict[str, Any]:
    """Read KB docs, chunk, embed, and upsert into Qdrant. Idempotent via recreate."""
    client = get_qdrant_client(qdrant_url)
    ensure_collection(client, recreate=recreate)
    chunks = load_knowledge_chunks(kb_dir)

    points: list[qmodels.PointStruct] = []
    for chunk in chunks:
        vector = embed(chunk["text"])
        points.append(
            qmodels.PointStruct(
                id=point_id_for(chunk["source_document"], chunk["chunk_index"]),
                vector=vector,
                payload=chunk,
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return {
        "collection": COLLECTION_NAME,
        "points_upserted": len(points),
        "documents": sorted({c["source_document"] for c in chunks}),
    }


if __name__ == "__main__":
    result = setup()
    print(result)
