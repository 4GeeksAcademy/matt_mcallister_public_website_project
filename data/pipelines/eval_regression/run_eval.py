"""CLI: temporal CV + learning curve for TrackFlow CSAT regression."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Stable matplotlib defaults before pyplot is imported via evaluate.
_PIPELINE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(_PIPELINE_DIR / ".mplconfig"))
(_PIPELINE_DIR / ".mplconfig").mkdir(exist_ok=True)

# Allow running as `python run_eval.py` from this directory.
sys.path.insert(0, str(_PIPELINE_DIR))

from domain import N_SPLITS
from evaluate import plot_learning_curve, save_metrics, temporal_cross_validate
from load_data import build_xy, default_data_path, load_scored_incidents


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TrackFlow regression evaluation")
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--n-splits", type=int, default=N_SPLITS)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=_repo_root() / "data" / "eval",
    )
    args = parser.parse_args()

    data_path = args.data or default_data_path()
    df = load_scored_incidents(data_path)
    X, y = build_xy(df)

    cv = temporal_cross_validate(X, y, n_splits=args.n_splits, alpha=args.alpha)
    lc = plot_learning_curve(
        X,
        y,
        output_path=args.eval_dir / "learning_curve.png",
        n_splits=args.n_splits,
        alpha=args.alpha,
    )
    payload = {
        "data_path": str(data_path),
        "n_rows": int(len(df)),
        "features": list(X.columns),
        "target": "satisfaction_score",
        "cross_validation": cv,
        "learning_curve": lc,
    }
    metrics_path = args.eval_dir / "cv_metrics.json"
    save_metrics(payload, metrics_path)

    summary = cv["summary"]
    print(f"Rows: {len(df)}")
    print(f"Primary metric (val MAE): {summary['primary_mean_pm_std']}")
    print(f"Val RMSE: {summary['val_rmse_mean']:.4f} ± {summary['val_rmse_std']:.4f}")
    print(f"Learning curve: {args.eval_dir / 'learning_curve.png'}")
    print(f"Metrics JSON: {metrics_path}")


if __name__ == "__main__":
    main()
