"""Deterministic output guardrails before responses reach the user."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from data.pipelines.faithfulness import check_faithfulness

_LEAK_PATTERNS = (
    re.compile(r"(?i)hard rules\s*:"),
    re.compile(r"(?i)treat retrieved text as data"),
    re.compile(r"(?i)<retrieved_context>"),
)

_PII_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

OUTPUT_REJECTION_MESSAGE = (
    "I can't share that response safely. Please ask about TrackFlow policies or incidents."
)


@dataclass(frozen=True)
class OutputGuardrailResult:
    allowed: bool
    guardrail_type: Optional[str] = None
    rule: Optional[str] = None
    answer: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


def check_output_guardrails(
    answer: str,
    *,
    context: str = "",
    chunks: list[dict[str, Any]] | None = None,
) -> OutputGuardrailResult:
    text = (answer or "").strip()
    if not text:
        return OutputGuardrailResult(allowed=True, answer=text)

    for pattern in _LEAK_PATTERNS:
        if pattern.search(text):
            return OutputGuardrailResult(
                allowed=False,
                guardrail_type="security",
                rule="system_prompt_leak",
                answer=OUTPUT_REJECTION_MESSAGE,
            )

    if _PII_EMAIL.search(text):
        return OutputGuardrailResult(
            allowed=False,
            guardrail_type="content",
            rule="pii_email_detected",
            answer=OUTPUT_REJECTION_MESSAGE,
        )

    if context:
        faithfulness = check_faithfulness(text, context)
        if not faithfulness["faithful"]:
            return OutputGuardrailResult(
                allowed=False,
                guardrail_type="content",
                rule="unsupported_rate_or_timeframe",
                answer=OUTPUT_REJECTION_MESSAGE,
                metadata=faithfulness,
            )

    if chunks:
        for chunk in chunks:
            chunk_text = str(chunk.get("text") or "")
            if chunk_text and len(chunk_text) > 40 and chunk_text in text:
                return OutputGuardrailResult(
                    allowed=False,
                    guardrail_type="content",
                    rule="raw_chunk_leak",
                    answer=OUTPUT_REJECTION_MESSAGE,
                )

    return OutputGuardrailResult(allowed=True, answer=text)
