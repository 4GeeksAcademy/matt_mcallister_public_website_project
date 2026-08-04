#!/usr/bin/env python3
"""Seed historical TrackFlow incidents from the analyzer CSV into SQLite.

Applies analyzer validity rules, then CONTEXT-incidents.md transforms.
Forces origin=customer. Idempotent on CSV incident_id (seed_key).
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.shared.incident_validation import (  # noqa: E402
    map_branch_from_country,
    map_category,
    map_status,
    validate_incident_fields,
)

_API_DIR = _REPO_ROOT / "services" / "incident-api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from app.db import connect, ensure_db  # noqa: E402

US_CARRIERS = {"UPS", "FEDEX", "DHL_US"}
ES_CARRIERS = {"MRW", "SEUR", "DHL_ES", "LOCAL_ES"}
ANALYZER_CATEGORIES = {
    "LOST_PARCEL",
    "DELAYED_DELIVERY",
    "WRONG_ADDRESS",
    "RETURN_REQUEST",
    "DAMAGE",
}
ANALYZER_STATUSES = {"OPEN", "CLOSED", "DISCARDED"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed incidents from analyzer CSV")
    parser.add_argument(
        "--csv-path",
        default=str(_REPO_ROOT / "data" / "raw" / "incidents-trackflow.csv"),
        help="Path to incidents-trackflow.csv",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without writing",
    )
    return parser.parse_args()


def parse_created_at(raw_date: str) -> str | None:
    value = (raw_date or "").strip()
    if not value:
        return None
    try:
        day = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return day.isoformat()


def analyzer_row_errors(row: dict[str, str], index: int) -> list[str]:
    """Mirror incidents-file-analyzer invalidation rules so totals match CONTEXT."""
    errors: list[str] = []
    country = (row.get("country") or "").strip().upper()
    carrier = (row.get("carrier") or "").strip().upper()
    tracking = (row.get("tracking_number") or "").strip()
    category = (row.get("category") or "").strip().upper()
    description = (row.get("description") or "").strip()
    status = (row.get("status") or "").strip().upper()
    email = (row.get("customer_email") or "").strip()
    score_raw = (row.get("satisfaction_score") or "").strip()

    if country not in {"US", "ES"}:
        errors.append(f"row {index}: missing or invalid country")
    else:
        allowed = US_CARRIERS if country == "US" else ES_CARRIERS
        if not carrier or carrier not in allowed:
            errors.append(
                f"row {index}: carrier '{carrier}' is not valid for country '{country}'"
            )

    if len(tracking) < 8:
        errors.append(f"row {index}: missing or invalid tracking_number")

    if category not in ANALYZER_CATEGORIES:
        errors.append(f"row {index}: missing or invalid category")

    if len(description) < 5:
        errors.append(f"row {index}: empty or too-short description")

    if "@" not in email:
        errors.append(f"row {index}: missing or invalid customer_email")

    if status not in ANALYZER_STATUSES:
        errors.append(f"row {index}: missing or invalid status")

    if status == "CLOSED":
        if score_raw == "":
            errors.append(
                f"row {index}: status CLOSED with no satisfaction_score"
            )
        else:
            try:
                score = int(score_raw)
            except ValueError:
                score = -1
            if score < 1 or score > 5:
                errors.append(f"row {index}: satisfaction_score out of range")

    return errors


def transform_row(row: dict[str, str], index: int) -> tuple[dict[str, str] | None, list[str]]:
    errors = analyzer_row_errors(row, index)
    if errors:
        return None, errors

    incident_id = (row.get("incident_id") or "").strip()
    description = (row.get("description") or "").strip()
    title = description[:120].strip()
    created_at = parse_created_at(row.get("date") or "")
    status = map_status(row.get("status") or "")
    category = map_category(row.get("category") or "")
    branch = map_branch_from_country(row.get("country") or "")
    origin = "customer"

    if not incident_id:
        errors.append(f"row {index}: incident_id is required")
    if not title:
        errors.append(f"row {index}: title empty after trim")
    if created_at is None:
        errors.append(f"row {index}: date must be YYYY-MM-DD")
    if status is None:
        errors.append(f"row {index}: status cannot be mapped")
    if category is None:
        errors.append(f"row {index}: category cannot be mapped")
    if branch is None:
        errors.append(f"row {index}: country cannot be mapped to branch")

    if errors:
        return None, errors

    field_errors = validate_incident_fields(
        title=title,
        description=description,
        category=category or "",
        status=status or "",
        origin=origin,
        branch=branch or "",
    )
    for err in field_errors:
        errors.append(f"row {index}: {err['field']} — {err['message']}")
    if errors:
        return None, errors

    return {
        "seed_key": incident_id,
        "id": f"inc_seed_{incident_id.lower()}",
        "title": title,
        "description": description,
        "category": category or "",
        "status": status or "",
        "origin": origin,
        "branch": branch or "",
        "created_at": created_at or "",
        "updated_at": created_at or "",
    }, []


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return 1

    ensure_db()

    inserted = 0
    skipped_duplicates = 0
    invalid_rows: list[str] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            print("CSV has no header row")
            return 1

        with connect() as conn:
            existing = {
                row["seed_key"]
                for row in conn.execute(
                    "SELECT seed_key FROM incidents WHERE seed_key IS NOT NULL"
                ).fetchall()
            }

            for index, row in enumerate(reader, start=2):
                incident, row_errors = transform_row(row, index)
                if row_errors:
                    invalid_rows.extend(row_errors)
                    continue

                assert incident is not None
                if incident["seed_key"] in existing:
                    skipped_duplicates += 1
                    continue

                if not args.dry_run:
                    conn.execute(
                        """
                        INSERT INTO incidents (
                            id, title, description, category, status, origin, branch,
                            created_at, updated_at, seed_key
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            incident["id"],
                            incident["title"],
                            incident["description"],
                            incident["category"],
                            incident["status"],
                            incident["origin"],
                            incident["branch"],
                            incident["created_at"],
                            incident["updated_at"],
                            incident["seed_key"],
                        ),
                    )
                existing.add(incident["seed_key"])
                inserted += 1

            if not args.dry_run:
                conn.commit()

    print("Seed summary")
    print(f"- inserted: {inserted}")
    print(f"- skipped_duplicates: {skipped_duplicates}")
    print(f"- invalid_row_messages: {len(invalid_rows)}")
    if invalid_rows:
        print("Invalid row details:")
        for issue in invalid_rows:
            print(f"  - {issue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
