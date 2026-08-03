"""Unit tests for TrackFlow RAG retrieve() and query() with mocks (no live Qdrant/LLM)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from data.pipelines import rag as rag_pipeline


def _hit(score: float, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(score=score, payload=payload, id="1")


@patch("data.pipelines.rag.embed", return_value=[0.1, 0.2, 0.3])
def test_retrieve_excludes_results_below_min_score(mock_embed: MagicMock) -> None:
    client = MagicMock()
    client.search.return_value = [
        _hit(0.91, {"text": "high", "source_document": "sla-delivery"}),
        _hit(0.40, {"text": "low", "source_document": "sla-delivery"}),
        _hit(0.72, {"text": "mid", "source_document": "returns-policy"}),
    ]

    results = rag_pipeline.retrieve(
        "delivery SLA",
        k=5,
        min_score=0.7,
        client=client,
    )

    mock_embed.assert_called_once()
    assert len(results) == 2
    assert all(r["_score"] >= 0.7 for r in results)
    assert {r["text"] for r in results} == {"high", "mid"}


@patch("data.pipelines.rag.embed", return_value=[0.1, 0.2, 0.3])
def test_retrieve_can_return_fewer_than_k(mock_embed: MagicMock) -> None:
    client = MagicMock()
    client.search.return_value = [
        _hit(0.95, {"text": "only-one", "source_document": "carrier-coverage"}),
        _hit(0.20, {"text": "noise", "source_document": "carrier-coverage"}),
        _hit(0.10, {"text": "more-noise", "source_document": "carrier-coverage"}),
    ]

    results = rag_pipeline.retrieve(
        "rural Aragón",
        k=5,
        min_score=0.55,
        client=client,
    )

    assert len(results) == 1
    assert len(results) < 5
    assert results[0]["text"] == "only-one"


def test_query_returns_model_output_not_raw_chunks() -> None:
    retrieved = [
        {
            "company": "trackflow",
            "source_document": "returns-policy",
            "section": "Standard return window",
            "language": "en",
            "chunk_index": 0,
            "text": "The standard return window is 30 calendar days.",
            "_score": 0.88,
        }
    ]
    generated = (
        "The standard return window is 30 calendar days from delivery."
    )

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=generated))]
    )

    answer = rag_pipeline.query(
        "What's the standard return window?",
        retrieve_fn=lambda *args, **kwargs: retrieved,
        openai_client=mock_openai,
    )

    assert answer == generated
    assert answer != retrieved[0]["text"]
    assert "chunk_index" not in answer
    mock_openai.chat.completions.create.assert_called_once()


def test_query_honest_fallback_when_no_chunks() -> None:
    answer = rag_pipeline.query(
        "unrelated question with no hits",
        retrieve_fn=lambda *args, **kwargs: [],
        openai_client=MagicMock(),
    )

    assert "knowledge base" in answer.lower()
    assert "30 calendar days" not in answer
