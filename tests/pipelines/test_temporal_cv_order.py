"""Verify TimeSeriesSplit folds preserve chronological order."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PIPELINE_DIR = Path(__file__).resolve().parents[2] / "data" / "pipelines" / "eval_regression"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from domain import N_SPLITS
from evaluate import assert_fold_chronological, make_time_series_split


def test_time_series_split_preserves_chronological_order():
    n_samples = 120
    X = pd.DataFrame({"x": np.arange(n_samples)})
    splitter = make_time_series_split(n_splits=N_SPLITS)
    assert splitter.get_n_splits() == N_SPLITS

    previous_test_max = -1
    for fold_i, (train_idx, test_idx) in enumerate(splitter.split(X)):
        assert_fold_chronological(train_idx, test_idx)

        # No index from a later fold appears before an earlier fold's indices
        # in the chronological (positional) sense: all train < all test,
        # and successive test blocks move forward in time.
        assert train_idx.max() < test_idx.min()
        assert np.all(train_idx < test_idx.min())
        assert test_idx.min() > previous_test_max or fold_i == 0
        previous_test_max = int(test_idx.max())

        # Within each fold, later indices never appear before earlier ones.
        combined = np.concatenate([train_idx, test_idx])
        assert np.all(np.diff(combined) > 0) or (
            # train then test may not be a single contiguous increasing block
            # across the join if TimeSeriesSplit leaves a gap — still require
            # each side sorted and train before test.
            np.all(np.diff(train_idx) > 0) and np.all(np.diff(test_idx) > 0)
        )


def test_shuffled_indices_fail_chronology_check():
    train_idx = np.array([0, 2, 1])
    test_idx = np.array([3, 4, 5])
    with pytest.raises(AssertionError, match="not strictly increasing"):
        assert_fold_chronological(train_idx, test_idx)


def test_overlapping_fold_fails_chronology_check():
    train_idx = np.array([0, 1, 2, 5])
    test_idx = np.array([3, 4, 6])
    with pytest.raises(AssertionError, match="mixes chronology"):
        assert_fold_chronological(train_idx, test_idx)
