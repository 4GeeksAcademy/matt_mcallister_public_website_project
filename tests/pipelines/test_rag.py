"""Unit tests for TrackFlow RAG retrieve() and query() with mocks (no live Qdrant/LLM)."""

from __future__ import annotations

import json
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

    result = rag_pipeline.query(
        "What's the standard return window?",
        retrieve_fn=lambda *args, **kwargs: retrieved,
        openai_client=mock_openai,
    )

    assert result["answer"] == generated
    assert result["answer"] != retrieved[0]["text"]
    assert result["sources"] == [
        {
            "source_document": "returns-policy",
            "section": "Standard return window",
            "language": "en",
        }
    ]
    assert "text" not in result["sources"][0]
    assert "chunk_index" not in result["sources"][0]
    assert "_score" not in result["sources"][0]
    assert result["faithful"] is True
    mock_openai.chat.completions.create.assert_called_once()


def test_query_honest_fallback_when_no_chunks() -> None:
    result = rag_pipeline.query(
        "unrelated question with no hits",
        retrieve_fn=lambda *args, **kwargs: [],
        openai_client=MagicMock(),
    )

    assert "knowledge base" in result["answer"].lower()
    assert "30 calendar days" not in result["answer"]
    assert result["sources"] == []


def test_query_rejects_unsupported_rate_or_timeframe() -> None:
    retrieved = [
        {
            "source_document": "returns-policy",
            "section": "Return eligibility",
            "language": "en",
            "text": "Eligible products may be returned after review.",
        }
    ]
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="Returns have a 14 day window and a 12% fee."
                )
            )
        ]
    )

    result = rag_pipeline.query(
        "What are the return terms?",
        retrieve_fn=lambda *args, **kwargs: retrieved,
        openai_client=mock_openai,
    )

    assert result["faithful"] is False
    assert result["unsupported_claims"] == ["14 day", "12%"]
    assert "cannot confirm" in result["answer"].lower()
    assert "14 day" not in result["answer"]


def test_recall_at_3_uses_all_canonical_eval_queries() -> None:
    expected_by_question = {
        case["question"]: case["expected_source_document"]
        for case in json.loads(
            rag_pipeline.EVAL_QUERIES_PATH.read_text(encoding="utf-8")
        )
    }

    def fake_retrieve(question: str, **kwargs):
        assert kwargs["k"] == 3
        return [
            {"source_document": "irrelevant"},
            {"source_document": expected_by_question[question]},
        ]

    report = rag_pipeline.evaluate_recall_at_3(retrieve_fn=fake_retrieve)

    assert report["metric"] == "Recall@3"
    assert report["total"] == 10
    assert report["hits"] == 10
    assert report["recall_at_3"] == 1.0


def test_local_index_recall_at_3_meets_threshold() -> None:
    retrieve_fn = rag_pipeline.build_local_index_retrieve_fn()
    report = rag_pipeline.evaluate_recall_at_3(
        retrieve_fn=retrieve_fn,
        min_score=0.0,
    )

    assert report["total"] == 10
    assert report["recall_at_3"] >= 0.8
    assert report["hits"] >= 8
