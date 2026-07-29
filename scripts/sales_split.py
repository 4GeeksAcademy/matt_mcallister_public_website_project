"""Train/test split helpers for TrackFlow sales regression (8 years / 2 years)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

TRAIN_YEARS = 8
TEST_YEARS = 2
START_YEAR = 2016
END_YEAR = 2025
TRAIN_END_YEAR = START_YEAR + TRAIN_YEARS - 1  # 2023
TEST_START_YEAR = TRAIN_END_YEAR + 1  # 2024
TEST_END_YEAR = END_YEAR  # 2025


@dataclass(frozen=True)
class SalesSplit:
    train: pd.DataFrame
    test: pd.DataFrame


def load_consolidated_sales(csv_path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["month"] = pd.to_datetime(df["month"])
    df = df[df["market"] == "consolidated"].copy()
    df = df.sort_values("month", kind="mergesort").reset_index(drop=True)
    return df


def split_train_test(df: pd.DataFrame) -> SalesSplit:
    """First 8 years (2016–2023) train; last 2 years (2024–2025) test."""
    years = df["month"].dt.year
    train = df[years <= TRAIN_END_YEAR].copy().reset_index(drop=True)
    test = df[years >= TEST_START_YEAR].copy().reset_index(drop=True)
    return SalesSplit(train=train, test=test)


def assert_valid_8_2_split(train: pd.DataFrame, test: pd.DataFrame) -> None:
    train_years = sorted(train["month"].dt.year.unique().tolist())
    test_years = sorted(test["month"].dt.year.unique().tolist())
    expected_train = list(range(START_YEAR, TRAIN_END_YEAR + 1))
    expected_test = list(range(TEST_START_YEAR, TEST_END_YEAR + 1))
    if train_years != expected_train:
        raise AssertionError(f"Train years {train_years} != {expected_train}")
    if test_years != expected_test:
        raise AssertionError(f"Test years {test_years} != {expected_test}")
    if len(train) != TRAIN_YEARS * 12:
        raise AssertionError(f"Expected {TRAIN_YEARS * 12} train rows, got {len(train)}")
    if len(test) != TEST_YEARS * 12:
        raise AssertionError(f"Expected {TEST_YEARS * 12} test rows, got {len(test)}")
    if train["month"].max() >= test["month"].min():
        raise AssertionError("Train and test month ranges overlap or are unordered")
