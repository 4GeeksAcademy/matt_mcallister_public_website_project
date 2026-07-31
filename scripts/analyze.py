#!/usr/bin/env python3
"""CLI: analyze TrackFlow incident CSV and optionally export metrics."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from export import write_metrics_csv
from stats import (
    CLOSED_NO_SCORE,
    INVALID_CARRIER,
    INVALID_CATEGORY,
    INVALID_EMAIL,
    INVALID_TRACKING,
    AnalysisResult,
    analyze_records,
)

CATEGORY_ORDER = (
    "LOST_PARCEL",
    "DELAYED_DELIVERY",
    "WRONG_ADDRESS",
    "RETURN_REQUEST",
    "DAMAGE",
)
STATUS_ORDER = ("OPEN", "CLOSED", "DISCARDED")
COUNTRY_ORDER = ("US", "ES")
INVALID_ORDER = (
    INVALID_TRACKING,
    INVALID_CARRIER,
    INVALID_CATEGORY,
    INVALID_EMAIL,
    CLOSED_NO_SCORE,
)
SCORE_LABELS = {
    1: "Very dissatisfied",
    2: "Dissatisfied",
    3: "Neutral",
    4: "Satisfied",
    5: "Very satisfied",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")
        return [dict(row) for row in reader]


def _pct(count: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(count / total) * 100:.1f}%"


def _line(label: str, value: str, width: int = 34) -> str:
    dots = "." * max(2, width - len(label))
    return f"{label} {dots} {value}"


def format_report(result: AnalysisResult) -> str:
    valid = result.valid_records
    closed = result.status_counts.get("CLOSED", 0)
    average = result.satisfaction_average
    average_text = f"{average:.2f}" if average is not None else "n/a"

    lines = [
        "=" * 60,
        "  TRACKFLOW — INCIDENT REPORT ANALYSIS",
        f"  Source file: {result.source_file}",
        "=" * 60,
        "",
        _line("TOTAL RECORDS IN FILE", str(result.total_records)),
        f"  ├─ {_line('Valid records', str(result.valid_records), 28)}",
        f"  └─ {_line('Invalid / incomplete', str(result.invalid_records), 28)}",
        "",
        "INVALID RECORDS BREAKDOWN",
    ]

    invalid_items = [
        (reason, result.invalid_breakdown.get(reason, 0))
        for reason in INVALID_ORDER
        if result.invalid_breakdown.get(reason, 0)
    ]
    # Include any unexpected reasons as well
    for reason, count in sorted(result.invalid_breakdown.items()):
        if reason not in INVALID_ORDER and count:
            invalid_items.append((reason, count))

    for index, (reason, count) in enumerate(invalid_items):
        prefix = "└─" if index == len(invalid_items) - 1 else "├─"
        lines.append(f"  {prefix} {_line(reason, str(count), 30)}")

    lines.extend(["", "BREAKDOWN BY CATEGORY (valid records)"])
    categories = [c for c in CATEGORY_ORDER if c in result.category_counts] + [
        c for c in sorted(result.category_counts) if c not in CATEGORY_ORDER
    ]
    for index, category in enumerate(categories):
        count = result.category_counts[category]
        prefix = "└─" if index == len(categories) - 1 else "├─"
        lines.append(
            f"  {prefix} {_line(category, f'{count}  ({_pct(count, valid)})', 28)}"
        )

    lines.extend(["", "BREAKDOWN BY STATUS (valid records)"])
    statuses = [s for s in STATUS_ORDER if s in result.status_counts] + [
        s for s in sorted(result.status_counts) if s not in STATUS_ORDER
    ]
    for index, status in enumerate(statuses):
        count = result.status_counts[status]
        prefix = "└─" if index == len(statuses) - 1 else "├─"
        lines.append(
            f"  {prefix} {_line(status, f'{count}  ({_pct(count, valid)})', 28)}"
        )

    lines.extend(["", "BREAKDOWN BY COUNTRY (valid records)"])
    countries = [c for c in COUNTRY_ORDER if c in result.country_counts] + [
        c for c in sorted(result.country_counts) if c not in COUNTRY_ORDER
    ]
    for index, country in enumerate(countries):
        count = result.country_counts[country]
        prefix = "└─" if index == len(countries) - 1 else "├─"
        lines.append(
            f"  {prefix} {_line(country, f'{count}  ({_pct(count, valid)})', 28)}"
        )

    lines.extend(
        [
            "",
            "SATISFACTION INDEX (closed incidents)",
            f"  Scored incidents: {result.scored_incidents} of {closed}",
            f"  Average score: {average_text} / 5.00",
        ]
    )
    for score in range(1, 6):
        count = result.satisfaction_counts.get(score, 0)
        prefix = "└─" if score == 5 else "├─"
        label = f"Score {score} ({SCORE_LABELS[score]})"
        lines.append(f"  {prefix} {_line(label, str(count), 30)}")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze TrackFlow incident CSV reports.",
    )
    parser.add_argument(
        "csv_path",
        help="Path to the incidents CSV file (e.g. incidents-trackflow.csv)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    csv_path = Path(args.csv_path)

    if not csv_path.is_file():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        return 1

    try:
        rows = load_csv(csv_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print("Error: CSV must be UTF-8 encoded.", file=sys.stderr)
        return 1

    result = analyze_records(rows, csv_path.name)
    print(format_report(result))

    try:
        answer = input("Export results to CSV? [y / n]: ").strip().lower()
    except EOFError:
        answer = "n"

    if answer in {"y", "yes"}:
        output_path = Path("results.csv")
        write_metrics_csv(result, output_path)
        print(f"Results exported to {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
