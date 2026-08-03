"""Export AnalysisResult metrics as a one-row-per-metric CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from stats import AnalysisResult


def write_metrics_csv(result: AnalysisResult, output_path: Path) -> None:
    rows: list[tuple[str, str]] = [
        ("source_file", result.source_file),
        ("total_records", str(result.total_records)),
        ("valid_records", str(result.valid_records)),
        ("invalid_records", str(result.invalid_records)),
        ("scored_incidents", str(result.scored_incidents)),
        (
            "satisfaction_average",
            "" if result.satisfaction_average is None else str(result.satisfaction_average),
        ),
    ]

    for key, value in sorted(result.invalid_breakdown.items()):
        rows.append((f"invalid:{key}", str(value)))
    for key, value in sorted(result.category_counts.items()):
        rows.append((f"category:{key}", str(value)))
    for key, value in sorted(result.status_counts.items()):
        rows.append((f"status:{key}", str(value)))
    for key, value in sorted(result.country_counts.items()):
        rows.append((f"country:{key}", str(value)))
    for score, value in sorted(result.satisfaction_counts.items()):
        rows.append((f"satisfaction:{score}", str(value)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)
