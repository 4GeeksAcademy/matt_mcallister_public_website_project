"""Validate TrackFlow sales 8-year train / 2-year test split."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
DATA = REPO_ROOT / "data" / "raw" / "trackflow_sales.csv"

sys.path.insert(0, str(SCRIPTS))

from sales_split import (  # noqa: E402
    TEST_END_YEAR,
    TEST_START_YEAR,
    TRAIN_END_YEAR,
    assert_valid_8_2_split,
    load_consolidated_sales,
    split_train_test,
)


@pytest.fixture(scope="module")
def sales_df() -> pd.DataFrame:
    if not DATA.exists():
        pytest.skip(f"Missing dataset: {DATA}")
    return load_consolidated_sales(DATA)


def test_eight_two_year_split(sales_df: pd.DataFrame):
    split = split_train_test(sales_df)
    assert_valid_8_2_split(split.train, split.test)

    assert len(split.train) == 96
    assert len(split.test) == 24
    assert split.train["month"].dt.year.min() == 2016
    assert split.train["month"].dt.year.max() == TRAIN_END_YEAR
    assert split.test["month"].dt.year.min() == TEST_START_YEAR
    assert split.test["month"].dt.year.max() == TEST_END_YEAR

    # No leakage: every train month is strictly before every test month
    assert split.train["month"].max() < split.test["month"].min()


def test_split_rejects_overlapping_frames():
    months = pd.date_range("2016-01-01", periods=5, freq="MS")
    bad_train = pd.DataFrame({"month": months})
    bad_test = pd.DataFrame({"month": months})
    with pytest.raises(AssertionError):
        assert_valid_8_2_split(bad_train, bad_test)
