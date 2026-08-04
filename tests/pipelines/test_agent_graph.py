"""Evaluations for the TrackFlow LangGraph support knowledge agent."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from agents.support_agent.graph import get_checkpoint_state, run_agent
from agents.support_agent.trace import clear_traces, get_trace


def _return_window_chunks() -> list[dict]:
    return [
        {
            "company": "trackflow",
            "source_document": "returns-policy",
            "section": "Standard return window",
            "language": "en",
            "chunk_index": 0,
            "text": (
                "The standard return window is 30 calendar days from the date of "
                "delivery to the end consumer."
            ),
            "_score": 0.91,
        }
    ]


def test_eval_trace_order_retrieve_before_generate() -> None:
    """Eval 1: retrieve_node must run before generate_node in the stored trace."""
    clear_traces()

    def fake_retrieve(_question: str, **_kwargs) -> list[dict]:
        return _return_window_chunks()

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        "The standard return window is 30 calendar days from delivery."
                    )
                )
            )
        ]
    )

    result = run_agent(
        "What is the standard return window?",
        retrieve_fn=fake_retrieve,
        openai_client=mock_openai,
    )

    trace = get_trace(result["trace_id"])
    node_names = [entry["node"] for entry in trace]
    assert "retrieve_node" in node_names
    assert "generate_node" in node_names
    assert node_names.index("retrieve_node") < node_names.index("generate_node")


def test_eval_empty_question_skips_generate() -> None:
    """Eval 2: empty questions route to set_error without calling generate_node."""
    clear_traces()

    result = run_agent("   ")

    trace = get_trace(result["trace_id"])
    node_names = [entry["node"] for entry in trace]
    assert "set_error" in node_names
    assert "generate_node" not in node_names
    assert "retrieve_node" not in node_names
    assert result["answer"] == "A question is required."
    assert result["sources"] == []


def test_eval_grounding_return_window_from_context_company() -> None:
    """Eval 3: answer stays grounded in CONTEXT-company return-window policy."""
    clear_traces()

    def fake_retrieve(_question: str, **_kwargs) -> list[dict]:
        return _return_window_chunks()

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        "The standard return window is 30 calendar days from "
                        "delivery to the end consumer."
                    )
                )
            )
        ]
    )

    result = run_agent(
        "What is the standard return window for eligible products?",
        retrieve_fn=fake_retrieve,
        openai_client=mock_openai,
    )

    assert "30 calendar days" in result["answer"].casefold()
    assert any(
        source["source_document"] == "returns-policy"
        for source in result["sources"]
    )
    trace = get_trace(result["trace_id"])
    assert any(entry["node"] == "retrieve_node" for entry in trace)


def test_eval_no_context_path_skips_generate() -> None:
    """Eval 4: empty retrieval routes to honest fallback without generation."""
    clear_traces()

    def fake_retrieve(_question: str, **_kwargs) -> list[dict]:
        return []

    result = run_agent(
        "What is the standard return window?",
        retrieve_fn=fake_retrieve,
    )

    trace = get_trace(result["trace_id"])
    node_names = [entry["node"] for entry in trace]
    assert "no_context_response" in node_names
    assert "generate_node" not in node_names
    assert result["sources"] == []
    assert "knowledge base" in result["answer"].casefold()


def test_checkpoint_exists_after_retrieve_transition() -> None:
    """Checkpointing is verifiable on the post-retrieve transition."""
    clear_traces()

    def fake_retrieve(_question: str, **_kwargs) -> list[dict]:
        return _return_window_chunks()

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="The standard return window is 30 calendar days."
                )
            )
        ]
    )

    result = run_agent(
        "What is the standard return window?",
        thread_id="checkpoint-eval-thread",
        retrieve_fn=fake_retrieve,
        openai_client=mock_openai,
    )

    checkpoint = get_checkpoint_state("checkpoint-eval-thread")
    assert checkpoint is not None
    assert checkpoint.get("chunks")
    assert result["trace_id"] == "checkpoint-eval-thread"
