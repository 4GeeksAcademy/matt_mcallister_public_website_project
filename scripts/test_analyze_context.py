"""Regression checks for TrackFlow incident analysis metrics."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from stats import analyze_records  # noqa: E402

CSV_PATH = ROOT / "data" / "raw" / "incidents-trackflow.csv"


def test_analyze_records_matches_context_fixture() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]

    result = analyze_records(rows, CSV_PATH.name)

    assert result.total_records == 100
    assert result.valid_records == 95
    assert result.invalid_records == 5
    assert result.category_counts == {
        "LOST_PARCEL": 14,
        "DELAYED_DELIVERY": 38,
        "WRONG_ADDRESS": 19,
        "RETURN_REQUEST": 17,
        "DAMAGE": 7,
    }
    assert result.status_counts == {"OPEN": 29, "CLOSED": 52, "DISCARDED": 14}
    assert result.country_counts == {"US": 50, "ES": 45}
    assert result.invalid_breakdown == {
        "Invalid tracking number": 1,
        "Carrier/country mismatch": 1,
        "Invalid or missing category": 1,
        "Invalid or missing email": 1,
        "Closed incident, no score": 1,
    }
    assert result.scored_incidents == 52
    assert result.satisfaction_average == 3.06
    assert result.satisfaction_counts == {1: 6, 2: 11, 3: 15, 4: 14, 5: 6}
