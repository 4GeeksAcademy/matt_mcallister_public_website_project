"""Temporal train/test split for TrackFlow sales (8-year / 2-year rule)."""

from __future__ import annotations

import pandas as pd


def temporal_split(
    df: pd.DataFrame,
    train_years: int = 8,
    test_years: int = 2,
    date_col: str = "date",
    year_col: str = "year",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split a time-ordered sales frame into the first `train_years` calendar years
    (train) and the last `test_years` calendar years (test).

    Raises ValueError if year counts, chronology, or date leakage constraints fail.
    """
    if train_years < 1 or test_years < 1:
        raise ValueError("train_years and test_years must be >= 1")

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    if year_col not in work.columns:
        work[year_col] = work[date_col].dt.year

    years = sorted(work[year_col].unique().tolist())
    expected = train_years + test_years
    if len(years) != expected:
        raise ValueError(
            f"Expected {expected} distinct calendar years, found {len(years)}: {years}"
        )

    train_year_set = set(years[:train_years])
    test_year_set = set(years[-test_years:])
    if train_year_set & test_year_set:
        raise ValueError("Train and test year sets overlap")

    train = work[work[year_col].isin(train_year_set)].sort_values(date_col).reset_index(drop=True)
    test = work[work[year_col].isin(test_year_set)].sort_values(date_col).reset_index(drop=True)

    if train.empty or test.empty:
        raise ValueError("Train or test split is empty")

    if train[date_col].max() >= test[date_col].min():
        raise ValueError(
            "Chronology violated: max(train.date) must be strictly before min(test.date)"
        )

    train_dates = set(train[date_col])
    test_dates = set(test[date_col])
    if train_dates & test_dates:
        raise ValueError("Date leakage: train and test share date values")

    if len(train[year_col].unique()) != train_years:
        raise ValueError(f"Train must contain exactly {train_years} years")
    if len(test[year_col].unique()) != test_years:
        raise ValueError(f"Test must contain exactly {test_years} years")

    return train, test
