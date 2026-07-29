"""Unit tests for the TrackFlow sales 8-year / 2-year temporal split."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPLIT_PATH = ROOT / "data" / "pipelines" / "sales-forecast" / "split.py"
CSV_PATH = ROOT / "data" / "raw" / "trackflow_sales.csv"


def _load_temporal_split():
    spec = importlib.util.spec_from_file_location("sales_forecast_split", SPLIT_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.temporal_split


temporal_split = _load_temporal_split()


@pytest.fixture(scope="module")
def sales_df() -> pd.DataFrame:
    assert CSV_PATH.exists(), f"Missing dataset: {CSV_PATH}"
    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_temporal_split_respects_eight_two_year_rule(sales_df: pd.DataFrame) -> None:
    train, test = temporal_split(sales_df, train_years=8, test_years=2)

    assert len(train["year"].unique()) == 8
    assert len(test["year"].unique()) == 2

    train_years = sorted(train["year"].unique().tolist())
    test_years = sorted(test["year"].unique().tolist())
    all_years = sorted(sales_df["year"].unique().tolist())

    assert train_years == all_years[:8]
    assert test_years == all_years[-2:]
    assert max(train_years) < min(test_years)


def test_temporal_split_has_no_date_leakage(sales_df: pd.DataFrame) -> None:
    train, test = temporal_split(sales_df, train_years=8, test_years=2)

    train_dates = set(train["date"])
    test_dates = set(test["date"])

    assert train_dates.isdisjoint(test_dates)
    assert train["date"].max() < test["date"].min()
    assert set(train["year"]).isdisjoint(set(test["year"]))


def test_temporal_split_rejects_wrong_year_count() -> None:
    short = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01"]),
            "year": [2020, 2021, 2022],
            "revenue_eur": [1.0, 2.0, 3.0],
        }
    )
    with pytest.raises(ValueError, match="Expected 10 distinct calendar years"):
        temporal_split(short, train_years=8, test_years=2)
