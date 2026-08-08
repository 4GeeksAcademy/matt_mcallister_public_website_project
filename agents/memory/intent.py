"""Classify user responses to pending memory proposals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

MemoryIntentLabel = Literal["approve", "reject", "edit", "topic_change"]

_APPROVE = re.compile(r"(?i)\b(yes|approve|approved|remember that|go ahead|sounds good)\b")
_REJECT = re.compile(r"(?i)\b(no|reject|don't remember|do not remember|never mind)\b")
_EDIT = re.compile(r"(?i)\b(change it to|instead remember|update it to|edit to)\b")
_TRACKFLOW = re.compile(
    r"(?i)\b(trackflow|sla|return|carrier|warehouse|inventory|incident|inc_|delivery|storage)\b"
)


@dataclass(frozen=True)
class MemoryIntentResult:
    label: MemoryIntentLabel
    edited_text: str | None = None


def classify_memory_intent(message: str, *, proposal_text: str = "") -> MemoryIntentResult:
    text = (message or "").strip()
    if not text:
        return MemoryIntentResult("topic_change")

    if _EDIT.search(text):
        edited = text
        for prefix in ("change it to", "instead remember", "update it to", "edit to"):
            if text.lower().startswith(prefix):
                edited = text[len(prefix) :].strip(" :.")
                break
        return MemoryIntentResult("edit", edited_text=edited or proposal_text)

    if _APPROVE.search(text):
        return MemoryIntentResult("approve")

    if _REJECT.search(text):
        return MemoryIntentResult("reject")

    # Approval is never inferred from silence or unrelated business questions.
    if _TRACKFLOW.search(text):
        return MemoryIntentResult("topic_change")

    return MemoryIntentResult("topic_change")
