"""Self-evaluation for whether an interaction should become memory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

from agents.memory.policy import validate_memory_candidate
from agents.memory.store import MemoryProposal

_PREFERENCE = re.compile(
    r"(?i)\b(prefer|always ask|default to|for future|remember that i)\b"
)
_BRANCH = re.compile(r"(?i)\b(la_office|zaragoza|los angeles|zaragoza_warehouse|la_warehouse)\b")
_CLIENT = re.compile(r"(?i)\bclient brand\b|\bbrand ([A-Za-z0-9_-]+)\b")


@dataclass
class MemoryEvaluation:
    remember: bool
    memory_proposal: Optional[MemoryProposal] = None
    dismissal_reason: Optional[str] = None


def evaluate_memory_candidate(
    *,
    user_id: str,
    question: str,
    answer: str,
    route: str,
    sources_used: list[str],
) -> MemoryEvaluation:
    text = f"{question}\n{answer}".strip()

    if route == "ticket" and "inc_" in question.lower():
        return MemoryEvaluation(
            remember=False,
            dismissal_reason="one_off_ticket_lookup",
        )

    if "poem" in question.casefold() or "homework" in question.casefold():
        return MemoryEvaluation(
            remember=False,
            dismissal_reason="off_domain_interaction",
        )

    proposal_text = None
    category = "preference"
    reason = ""

    if _PREFERENCE.search(question):
        proposal_text = question.strip()
        reason = "User stated an explicit reusable preference."
    elif match := _BRANCH.search(question):
        proposal_text = f"Prefers {match.group(0)} for operational questions."
        reason = "User referenced a default branch/warehouse context."
    elif match := _CLIENT.search(question):
        proposal_text = f"Handles client brand context: {match.group(0)}."
        category = "client_context"
        reason = "User mentioned a reusable client-brand context."
    elif "always cite" in question.casefold():
        proposal_text = question.strip()
        category = "workflow"
        reason = "User requested a repeatable workflow preference."

    if not proposal_text:
        return MemoryEvaluation(
            remember=False,
            dismissal_reason="no_durable_preference_detected",
        )

    decision = validate_memory_candidate(category=category, text=proposal_text)
    if not decision.allowed:
        return MemoryEvaluation(
            remember=False,
            dismissal_reason=decision.reason,
        )

    return MemoryEvaluation(
        remember=True,
        memory_proposal=MemoryProposal.create(
            user_id=user_id,
            category=category,
            text=proposal_text,
            reason=reason,
        ),
    )


MemoryEvaluator = Callable[..., MemoryEvaluation]
