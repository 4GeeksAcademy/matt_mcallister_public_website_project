"""Memory proposal, confirmation, and audit tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agents.memory.audit import get_audit_entries, reset_audit_log
from agents.memory.consolidation import MAX_ENTRIES, RETENTION_DAYS, consolidate_entries
from agents.memory.evaluator import (
    MemoryEvaluation,
    MemoryProposal,
    evaluate_memory_candidate,
)
from agents.memory.intent import classify_memory_intent
from agents.memory.policy import validate_memory_candidate
from agents.memory.redis_store import get_memory_store, reset_memory_store
from agents.support_agent.graph import get_checkpoint_state, run_agent
from agents.support_agent.trace import clear_traces


def _return_window_chunks() -> list[dict]:
    return [
        {
            "company": "trackflow",
            "source_document": "returns-policy",
            "section": "Standard return window",
            "language": "en",
            "chunk_index": 0,
            "text": "The standard return window is 30 calendar days from delivery.",
            "_score": 0.91,
        }
    ]


def _mock_openai() -> MagicMock:
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="The standard return window is 30 calendar days from delivery."
                )
            )
        ]
    )
    return mock_openai


@pytest.fixture(autouse=True)
def _reset_memory() -> None:
    reset_memory_store()
    reset_audit_log()
    clear_traces()


def test_policy_rejects_forbidden_discount_memory() -> None:
    decision = validate_memory_candidate(
        category="preference",
        text="Miguel approved a 50% storage discount for all clients.",
    )
    assert decision.allowed is False


def test_intent_classifier_uses_explicit_labels() -> None:
    assert classify_memory_intent("approve").label == "approve"
    assert classify_memory_intent("no thanks, reject").label == "reject"
    assert classify_memory_intent("What is the TrackFlow SLA?").label == "topic_change"


def test_evaluator_dismisses_one_off_ticket_lookup() -> None:
    result = evaluate_memory_candidate(
        user_id="user-1",
        question="What is the status of inc_12345?",
        answer="Ticket inc_12345 is open.",
        route="ticket",
        sources_used=["mcp_ticket_tool"],
    )
    assert result.remember is False
    assert result.dismissal_reason == "one_off_ticket_lookup"


def test_evaluator_dismisses_off_domain_interaction() -> None:
    result = evaluate_memory_candidate(
        user_id="user-1",
        question="Write me a poem about logistics.",
        answer="I can't help with that.",
        route="knowledge",
        sources_used=[],
    )
    assert result.remember is False
    assert result.dismissal_reason == "off_domain_interaction"


def test_evaluator_dismisses_no_durable_preference() -> None:
    result = evaluate_memory_candidate(
        user_id="user-1",
        question="What is the standard return window?",
        answer="The standard return window is 30 calendar days.",
        route="knowledge",
        sources_used=["rag"],
    )
    assert result.remember is False
    assert result.dismissal_reason == "no_durable_preference_detected"


def test_consolidate_entries_expires_dedupes_and_caps() -> None:
    now = datetime.now(timezone.utc)
    stale = (now - timedelta(days=RETENTION_DAYS + 1)).isoformat()
    recent = now.isoformat()
    entries = [
        {
            "id": "mem_old",
            "user_id": "user-1",
            "category": "preference",
            "text": "Expired preference.",
            "created_at": stale,
            "updated_at": stale,
        },
        {
            "id": "mem_dup_a",
            "user_id": "user-1",
            "category": "preference",
            "text": "Prefers LA office",
            "created_at": recent,
            "updated_at": recent,
        },
        {
            "id": "mem_dup_b",
            "user_id": "user-1",
            "category": "preference",
            "text": "prefers la office",
            "created_at": recent,
            "updated_at": recent,
        },
    ]
    entries.extend(
        {
            "id": f"mem_{index}",
            "user_id": "user-1",
            "category": "preference",
            "text": f"Preference number {index}.",
            "created_at": recent,
            "updated_at": recent,
        }
        for index in range(MAX_ENTRIES + 5)
    )

    consolidated = consolidate_entries(entries)

    assert all("Expired preference." not in item["text"] for item in consolidated)
    la_entries = [item for item in consolidated if "la office" in item["text"].casefold()]
    assert len(la_entries) == 1
    assert len(consolidated) == MAX_ENTRIES


def test_approved_memory_cycle_is_reflected_later() -> None:
    thread_id = "memory-approved-thread"
    user_id = "user-approved"
    mock_openai = _mock_openai()

    def always_propose(**kwargs) -> MemoryEvaluation:
        return MemoryEvaluation(
            remember=True,
            memory_proposal=MemoryProposal.create(
                user_id=user_id,
                category="preference",
                text="Prefers Zaragoza warehouse for inventory questions.",
                reason="Explicit preference stated.",
            ),
        )

    first = run_agent(
        "For future inventory questions, prefer Zaragoza warehouse.",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=mock_openai,
        memory_evaluator=always_propose,
    )
    assert first["pending_proposal"] is not None
    assert "Should I remember this" in first["answer"]

    run_agent(
        "approve",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=mock_openai,
    )
    store = get_memory_store()
    entries = store.list_entries(user_id)
    assert len(entries) == 1
    assert "Zaragoza" in entries[0].text

    run_agent(
        "What is the standard return window?",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=mock_openai,
    )
    checkpoint = get_checkpoint_state(thread_id)
    assert checkpoint is not None
    assert "Zaragoza" in checkpoint.get("user_memory_context", "")

    generate_calls = [
        call
        for call in mock_openai.chat.completions.create.call_args_list
        if call.kwargs.get("messages")
    ]
    assert generate_calls
    last_messages = generate_calls[-1].kwargs["messages"]
    prompt_blob = " ".join(message["content"] for message in last_messages)
    assert "Zaragoza" in prompt_blob
    assert "<user_memory>" in prompt_blob


def test_rejected_memory_cycle_leaves_store_empty() -> None:
    thread_id = "memory-rejected-thread"
    user_id = "user-rejected"

    def always_propose(**kwargs) -> MemoryEvaluation:
        return MemoryEvaluation(
            remember=True,
            memory_proposal=MemoryProposal.create(
                user_id=user_id,
                category="preference",
                text="Prefers LA office for all calls.",
                reason="Explicit preference stated.",
            ),
        )

    run_agent(
        "For future calls, prefer LA office.",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=_mock_openai(),
        memory_evaluator=always_propose,
    )
    run_agent(
        "reject",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=_mock_openai(),
    )
    assert get_memory_store().list_entries(user_id) == []
    outcomes = [event["outcome"] for event in get_audit_entries()]
    assert "rejected" in outcomes


def test_topic_change_discards_pending_proposal_by_default() -> None:
    thread_id = "memory-discard-thread"
    user_id = "user-discard"

    def always_propose(**kwargs) -> MemoryEvaluation:
        return MemoryEvaluation(
            remember=True,
            memory_proposal=MemoryProposal.create(
                user_id=user_id,
                category="preference",
                text="Prefers LA office for all calls.",
                reason="Explicit preference stated.",
            ),
        )

    run_agent(
        "For future calls, prefer LA office.",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=_mock_openai(),
        memory_evaluator=always_propose,
    )
    run_agent(
        "What is the TrackFlow return policy?",
        thread_id=thread_id,
        user_id=user_id,
        retrieve_fn=lambda *_a, **_k: _return_window_chunks(),
        openai_client=_mock_openai(),
    )
    assert get_memory_store().get_pending_proposal(user_id) is None
    assert get_memory_store().list_entries(user_id) == []
