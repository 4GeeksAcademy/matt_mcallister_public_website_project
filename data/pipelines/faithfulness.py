"""Faithfulness checks for RAG answers (rates/timeframes vs context)."""

from __future__ import annotations

import re
from typing import Any

_RATE_OR_TIMEFRAME = re.compile(
    r"(?:[$€£]\s?\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s?%|"
    r"\d+(?:[.,]\d+)?(?:\s*(?:to|-)\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:(?:calendar|business)\s+)?(?:hours?|days?|weeks?|months?|years?))",
    re.IGNORECASE,
)


def check_faithfulness(answer: str, context: str) -> dict[str, Any]:
    """Flag rates and timeframes in the answer that are absent from context."""
    context_claims = {
        re.sub(r"\s+", " ", match.group(0)).strip().casefold()
        for match in _RATE_OR_TIMEFRAME.finditer(context)
    }
    answer_claims = [
        re.sub(r"\s+", " ", match.group(0)).strip()
        for match in _RATE_OR_TIMEFRAME.finditer(answer)
    ]
    unsupported = [
        claim for claim in answer_claims if claim.casefold() not in context_claims
    ]
    return {"faithful": not unsupported, "unsupported_claims": unsupported}
