"""Deterministic input guardrails for scope and injection attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_JAILBREAK_PATTERNS = (
    re.compile(r"(?i)ignore\s+(all\s+)?(your\s+)?instructions"),
    re.compile(r"(?i)you\s+are\s+now\s+(an?\s+)?(unrestricted|helpful)\s+assistant"),
    re.compile(r"(?i)(reveal|show|print|dump)\s+(the\s+)?(system\s+)?prompt"),
)

_OFF_TOPIC_PATTERNS = (
    re.compile(r"(?i)\b(write|compose|create)\s+(me\s+)?(a\s+)?poem\b"),
    re.compile(r"(?i)\b(homework|essay|math problem)\b"),
    re.compile(r"(?i)\b(personal relationship|dating advice)\b"),
)

_CASUAL_PATTERNS = (
    re.compile(r"(?i)\bwhat time is it in\b"),
    re.compile(r"(?i)\bwho won (the )?(world cup|super bowl)\b"),
)

_TRACKFLOW_SIGNALS = re.compile(
    r"(?i)\b(trackflow|sla|return|carrier|warehouse|inventory|incident|inc_|"
    r"delivery|storage|pallet|miguel|zaragoza|los angeles)\b"
)

REDIRECT_MESSAGE = (
    "I can help with TrackFlow delivery SLAs, returns, carrier coverage, "
    "storage pricing, and incident tickets. Please ask a TrackFlow business question."
)

JAILBREAK_MESSAGE = (
    "I can't change my operating instructions. "
    "Ask me about TrackFlow policies, pricing, carriers, or incident status."
)

CASUAL_STEER_TEMPLATE = (
    "{brief_answer} For TrackFlow account support, I can help with SLAs, returns, "
    "carrier coverage, storage pricing, or incident tickets."
)


@dataclass(frozen=True)
class InputGuardrailResult:
    allowed: bool
    guardrail_type: Optional[str] = None
    rule: Optional[str] = None
    response: Optional[str] = None
    casual_brief: Optional[str] = None


def check_input_guardrails(question: str) -> InputGuardrailResult:
    text = (question or "").strip()
    if not text:
        return InputGuardrailResult(allowed=False, guardrail_type="structural", rule="empty_question")

    for index, pattern in enumerate(_JAILBREAK_PATTERNS, start=1):
        if pattern.search(text):
            return InputGuardrailResult(
                allowed=False,
                guardrail_type="security",
                rule=f"jailbreak_variant_{index}",
                response=JAILBREAK_MESSAGE,
            )

    if not _TRACKFLOW_SIGNALS.search(text):
        for pattern in _OFF_TOPIC_PATTERNS:
            if pattern.search(text):
                return InputGuardrailResult(
                    allowed=False,
                    guardrail_type="content",
                    rule="off_topic_personal",
                    response=REDIRECT_MESSAGE,
                )

        for pattern in _CASUAL_PATTERNS:
            if pattern.search(text):
                return InputGuardrailResult(
                    allowed=True,
                    guardrail_type="content",
                    rule="casual_steer_back",
                    casual_brief="I don't have live world-clock data in this assistant.",
                )

    return InputGuardrailResult(allowed=True)
