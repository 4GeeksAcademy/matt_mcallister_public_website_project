"""Bridge FastAPI to shared scripts/stats.py and scripts/export.py."""

from __future__ import annotations

import csv
import io
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from export import write_metrics_csv  # noqa: E402
from stats import AnalysisResult, analyze_records  # noqa: E402

__all__ = [
    "AnalysisError",
    "AnalysisResult",
    "export_result_csv",
    "load_csv_text",
    "result_to_dict",
    "run_analysis",
]

REQUIRED_COLUMNS = {
    "incident_id",
    "date",
    "country",
    "customer_type",
    "tracking_number",
    "carrier",
    "category",
    "description",
    "status",
    "customer_email",
    "satisfaction_score",
}


class AnalysisError(ValueError):
    """Raised when uploaded CSV content cannot be analyzed."""


def load_csv_text(content: str) -> list[dict[str, str]]:
    if not content or not content.strip():
        raise AnalysisError("CSV file is empty.")

    handle = io.StringIO(content)
    reader = csv.DictReader(handle)
    if not reader.fieldnames:
        raise AnalysisError("CSV has no header row.")

    headers = {name.strip() for name in reader.fieldnames if name}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise AnalysisError(
            "CSV is missing required columns: " + ", ".join(sorted(missing))
        )

    rows = [dict(row) for row in reader]
    if not rows:
        raise AnalysisError("CSV contains no data rows.")

    return rows


def run_analysis(content: str, source_file: str) -> AnalysisResult:
    rows = load_csv_text(content)
    return analyze_records(rows, source_file)


def result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["satisfaction_counts"] = {
        str(score): count for score, count in result.satisfaction_counts.items()
    }
    return payload


def export_result_csv(result: AnalysisResult) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as handle:
        temp_path = Path(handle.name)
    try:
        write_metrics_csv(result, temp_path)
        return temp_path.read_text(encoding="utf-8")
    finally:
        temp_path.unlink(missing_ok=True)
