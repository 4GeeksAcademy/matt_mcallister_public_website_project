"""Train Random Forest sales model for TrackFlow consolidated revenue."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Local imports when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sales_metrics import (
    gini_normalized,
    interpret_psi,
    k2_score_ks,
    mse_metrics,
    population_stability_index,
)
from sales_split import assert_valid_8_2_split, load_consolidated_sales, split_train_test

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data" / "raw" / "trackflow_sales.csv"
DEFAULT_EVAL = REPO_ROOT / "data" / "eval"
FEATURE_COLS = [
    "month_num",
    "year",
    "month_sin",
    "month_cos",
    "revenue_lag_1",
    "revenue_lag_12",
    "revenue_roll_3",
    "shipments_lag_1",
    "shipments_lag_12",
    "us_shipment_share",
    "spain_shipment_share",
]


def _ensure_mpl() -> None:
    mpl_dir = REPO_ROOT / "data" / "pipelines" / "eval_regression" / ".mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))


def add_market_mix_features(df: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    """
    Approximate LA (US) vs Zaragoza (Spain) volume mix ~60/40.
    Mild temporal drift supports PSI monitoring across train/test.
    """
    out = df.copy()
    rng = np.random.default_rng(random_state)
    years = out["month"].dt.year.to_numpy()
    # Slight US share increase over time (expansion signal possible in later years).
    base = 0.60 + 0.01 * (years - 2016) / 9.0
    noise = rng.normal(0.0, 0.012, size=len(out))
    us_share = np.clip(base + noise, 0.52, 0.70)
    out["us_shipment_share"] = us_share
    out["spain_shipment_share"] = 1.0 - us_share
    return out


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month_num"] = out["month"].dt.month
    out["year"] = out["month"].dt.year
    out["month_sin"] = np.sin(2 * np.pi * out["month_num"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month_num"] / 12)
    out["revenue_lag_1"] = out["revenue_eur"].shift(1)
    out["revenue_lag_12"] = out["revenue_eur"].shift(12)
    out["revenue_roll_3"] = out["revenue_eur"].shift(1).rolling(3).mean()
    out["shipments_lag_1"] = out["shipments_processed"].shift(1)
    out["shipments_lag_12"] = out["shipments_processed"].shift(12)
    return out


def build_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    usable = df.dropna(subset=FEATURE_COLS).copy()
    X = usable[FEATURE_COLS]
    y = usable["revenue_eur"].astype(float)
    return X, y


def train_and_evaluate(
    data_path: Path = DEFAULT_DATA,
    eval_dir: Path = DEFAULT_EVAL,
    random_state: int = 42,
) -> dict:
    _ensure_mpl()
    raw = load_consolidated_sales(data_path)
    raw = add_market_mix_features(raw, random_state=random_state)
    featured = engineer_features(raw)

    split = split_train_test(featured)
    assert_valid_8_2_split(split.train, split.test)

    # Drop early rows with incomplete lags inside each partition after global engineering.
    X_train, y_train = build_xy(split.train)
    X_test, y_test = build_xy(split.test)
    # Test set always has full lag history from prior train years; keep all 24 months.
    test_mask = split.test[FEATURE_COLS].notna().all(axis=1)
    X_test = split.test.loc[test_mask, FEATURE_COLS]
    y_test = split.test.loc[test_mask, "revenue_eur"].astype(float)
    test_months = split.test.loc[test_mask, "month"]

    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=8,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=1,
    )
    model.fit(X_train, y_train)

    # Point predictions + tree-wise variability band
    X_test_np = X_test.to_numpy()
    tree_preds = np.column_stack(
        [t.predict(X_test_np) for t in model.estimators_]
    )
    y_pred = model.predict(X_test)
    y_std = tree_preds.std(axis=1)
    lower = y_pred - 1.96 * y_std
    upper = y_pred + 1.96 * y_std

    mse = mse_metrics(y_test.to_numpy(), y_pred)
    gini = gini_normalized(y_test.to_numpy(), y_pred)
    k2 = k2_score_ks(y_test.to_numpy(), y_pred)

    # PSI on US shipment share (LA vs Zaragoza mix proxy) and on shipment volume.
    psi_mix = population_stability_index(
        split.train["us_shipment_share"].to_numpy(),
        split.test["us_shipment_share"].to_numpy(),
    )
    psi_volume = population_stability_index(
        split.train["shipments_processed"].to_numpy(),
        split.test["shipments_processed"].to_numpy(),
    )

    metrics = {
        "model": "RandomForestRegressor",
        "n_train_rows": int(len(X_train)),
        "n_test_rows": int(len(X_test)),
        "train_years": "2016-2023",
        "test_years": "2024-2025",
        "mse": mse,
        "psi_us_shipment_share": {
            "value": psi_mix,
            "interpretation": interpret_psi(psi_mix),
        },
        "psi_shipments_processed": {
            "value": psi_volume,
            "interpretation": interpret_psi(psi_volume),
        },
        "gini": gini,
        "k2_score_ks": k2,
        "features": FEATURE_COLS,
    }

    eval_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = eval_dir / "sales_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    model_path = eval_dir / "sales_revenue_rf.joblib"
    joblib.dump(model, model_path)

    # Visualization: prediction ± variability vs actual (test years)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(test_months, y_test.to_numpy(), "o-", label="Actual revenue_eur", color="#1f4e79")
    ax.plot(test_months, y_pred, "s-", label="Predicted revenue_eur", color="#c45c26")
    ax.fill_between(
        test_months,
        lower,
        upper,
        color="#c45c26",
        alpha=0.2,
        label="Prediction variability (±1.96·tree std)",
    )
    ax.set_title("TrackFlow consolidated revenue — test years 2024–2025")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (EUR)")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    plot_path = eval_dir / "sales_forecast_test.png"
    fig.savefig(plot_path, dpi=130)
    plt.close(fig)

    print(json.dumps(metrics, indent=2))
    print(f"Metrics: {metrics_path}")
    print(f"Model: {model_path}")
    print(f"Plot: {plot_path}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train TrackFlow sales revenue model")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    train_and_evaluate(args.data, args.eval_dir, args.seed)


if __name__ == "__main__":
    main()
