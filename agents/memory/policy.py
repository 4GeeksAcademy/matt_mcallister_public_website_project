"""Memory policy aligned with TrackFlow CONTEXT constraints."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_FORBIDDEN_DISCOUNT = re.compile(
    r"(?i)(\d+\s?%|free storage|waive(?:d)? fee|approved discount|storage discount|miguel approved)"
)
_FORBIDDEN_PROMPT = re.compile(r"(?i)\b(system prompt|ignore instructions|api key|secret)\b")
_FORBIDDEN_PII = re.compile(r"(?i)\bcustomer_email\b")


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def validate_memory_candidate(*, category: str, text: str) -> PolicyDecision:
    candidate = (text or "").strip()
    if not candidate:
        return PolicyDecision(False, "empty_memory_text")
    if _EMAIL.search(candidate) or _FORBIDDEN_PII.search(candidate):
        return PolicyDecision(False, "pii_not_allowed")
    if _FORBIDDEN_DISCOUNT.search(candidate):
        return PolicyDecision(False, "invented_commercial_terms")
    if _FORBIDDEN_PROMPT.search(candidate):
        return PolicyDecision(False, "instruction_or_secret_content")
    if category not in {"preference", "client_context", "workflow"}:
        return PolicyDecision(False, "invalid_category")
    return PolicyDecision(True, "allowed")


def format_memory_context(entries: list[dict], *, max_entries: int = 5) -> str:
    lines = []
    for entry in entries[:max_entries]:
        lines.append(f"- [{entry.get('category', 'preference')}] {entry.get('text', '')}")
    return "\n".join(lines)


DISMISS_EXAMPLES = [
    "One-off ticket lookup with no reusable preference.",
    "User asked for a poem (off-domain request).",
    "User attempted to store Miguel-approved 50% discount (forbidden commercial term).",
]

REMEMBER_EXAMPLES = [
    "User prefers Zaragoza warehouse for inventory questions.",
    "User always wants SLA doc cited for delivery questions.",
    "User handles client brand Aurora for return-policy calls.",
]
