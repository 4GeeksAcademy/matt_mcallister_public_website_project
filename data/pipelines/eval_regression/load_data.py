"""Load and prepare chronological TrackFlow incident features for regression."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from domain import FEATURE_COLUMNS, TARGET_COLUMN


def default_data_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "raw" / "incidents_train.csv"


def load_scored_incidents(csv_path: Path | None = None) -> pd.DataFrame:
    """Load incidents, keep CLOSED scored rows, sort ascending by date."""
    path = csv_path or default_data_path()
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    scored = df[
        (df["status"] == "CLOSED")
        & df[TARGET_COLUMN].notna()
        & df[TARGET_COLUMN].between(1, 5)
    ].copy()
    scored = scored.sort_values("date", kind="mergesort").reset_index(drop=True)
    scored["month"] = scored["date"].dt.month
    scored["day_of_week"] = scored["date"].dt.dayofweek
    return scored


def build_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = df.loc[:, list(FEATURE_COLUMNS)].copy()
    y = df[TARGET_COLUMN].astype(float)
    return X, y
