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


def load_csv_text(content: str) -> list[dict[str, str]]:
    handle = io.StringIO(content)
    reader = csv.DictReader(handle)
    return [dict(row) for row in reader]


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
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as handle:
        temp_path = Path(handle.name)
    write_metrics_csv(result, temp_path)
    csv_text = temp_path.read_text(encoding="utf-8")
    temp_path.unlink(missing_ok=True)
    return csv_text
