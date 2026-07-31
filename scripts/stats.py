"""Incident CSV analysis: validation and aggregate metrics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

VALID_COUNTRIES = {"US", "ES"}
VALID_CATEGORIES = {
    "LOST_PARCEL",
    "DELAYED_DELIVERY",
    "WRONG_ADDRESS",
    "RETURN_REQUEST",
    "DAMAGE",
}
CARRIERS_BY_COUNTRY = {
    "US": {"UPS", "FEDEX", "DHL_US"},
    "ES": {"MRW", "SEUR", "DHL_ES", "LOCAL_ES"},
}

INVALID_TRACKING = "Invalid tracking number"
INVALID_CARRIER = "Carrier/country mismatch"
INVALID_CATEGORY = "Invalid or missing category"
INVALID_EMAIL = "Invalid or missing email"
CLOSED_NO_SCORE = "Closed incident, no score"
INVALID_COUNTRY = "Missing or invalid country"
INVALID_DESCRIPTION = "Empty or short description"
INVALID_SCORE_RANGE = "Satisfaction score out of range"


@dataclass
class AnalysisResult:
    source_file: str
    total_records: int
    valid_records: int
    invalid_records: int
    invalid_breakdown: dict[str, int] = field(default_factory=dict)
    category_counts: dict[str, int] = field(default_factory=dict)
    status_counts: dict[str, int] = field(default_factory=dict)
    country_counts: dict[str, int] = field(default_factory=dict)
    satisfaction_counts: dict[int, int] = field(default_factory=dict)
    satisfaction_average: float | None = None
    scored_incidents: int = 0


def _is_valid_email(value: str) -> bool:
    return bool(value) and "@" in value


def _validate_row(row: dict[str, str]) -> str | None:
    country = (row.get("country") or "").strip()
    if country not in VALID_COUNTRIES:
        return INVALID_COUNTRY

    carrier = (row.get("carrier") or "").strip()
    if carrier not in CARRIERS_BY_COUNTRY.get(country, set()):
        return INVALID_CARRIER

    tracking = (row.get("tracking_number") or "").strip()
    if len(tracking) < 8:
        return INVALID_TRACKING

    category = (row.get("category") or "").strip()
    if category not in VALID_CATEGORIES:
        return INVALID_CATEGORY

    description = (row.get("description") or "").strip()
    if len(description) < 5:
        return INVALID_DESCRIPTION

    email = (row.get("customer_email") or "").strip()
    if not _is_valid_email(email):
        return INVALID_EMAIL

    status = (row.get("status") or "").strip()
    score_raw = (row.get("satisfaction_score") or "").strip()

    if status == "CLOSED" and not score_raw:
        return CLOSED_NO_SCORE

    if score_raw:
        try:
            score = int(score_raw)
        except ValueError:
            return INVALID_SCORE_RANGE
        if score < 1 or score > 5:
            return INVALID_SCORE_RANGE

    return None


def analyze_records(rows: list[dict[str, str]], source_file: str) -> AnalysisResult:
    invalid_breakdown: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    satisfaction_counts: Counter[int] = Counter()
    valid = 0
    score_sum = 0
    scored = 0

    for row in rows:
        reason = _validate_row(row)
        if reason is not None:
            invalid_breakdown[reason] += 1
            continue

        valid += 1
        category_counts[(row.get("category") or "").strip()] += 1
        status_counts[(row.get("status") or "").strip()] += 1
        country_counts[(row.get("country") or "").strip()] += 1

        score_raw = (row.get("satisfaction_score") or "").strip()
        if score_raw:
            score = int(score_raw)
            satisfaction_counts[score] += 1
            score_sum += score
            scored += 1

    total = len(rows)
    invalid = total - valid
    average = round(score_sum / scored, 2) if scored else None

    return AnalysisResult(
        source_file=source_file,
        total_records=total,
        valid_records=valid,
        invalid_records=invalid,
        invalid_breakdown=dict(invalid_breakdown),
        category_counts=dict(category_counts),
        status_counts=dict(status_counts),
        country_counts=dict(country_counts),
        satisfaction_counts=dict(satisfaction_counts),
        satisfaction_average=average,
        scored_incidents=scored,
    )


def result_summary_dict(result: AnalysisResult) -> dict[str, Any]:
    """Helper for debugging; not used by the API bridge."""
    return {
        "source_file": result.source_file,
        "total_records": result.total_records,
        "valid_records": result.valid_records,
        "invalid_records": result.invalid_records,
    }
