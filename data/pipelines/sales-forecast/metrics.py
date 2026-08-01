"""Test-set evaluation metrics for TrackFlow sales forecasting.

Low MSE alone is insufficient: a model can fit average magnitude while
distributions drift (PSI), rankings reverse (Gini), or residuals are
badly structured (K2). Report all four on the held-out test set.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from sklearn.metrics import mean_squared_error, roc_auc_score


def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Squared Error — average squared residual magnitude."""
    return float(mean_squared_error(y_true, y_pred))


def population_stability_index(
    expected: np.ndarray,
    actual: np.ndarray,
    n_bins: int = 10,
    eps: float = 1e-6,
) -> float:
    """
    Population Stability Index (PSI) between two distributions.

    Typically compare a reference (e.g. train target or train predictions)
    to the test distribution. Higher PSI ⇒ more drift / instability.
    """
    expected = np.asarray(expected, dtype=float).ravel()
    actual = np.asarray(actual, dtype=float).ravel()
    quantiles = np.linspace(0, 100, n_bins + 1)
    bins = np.unique(np.percentile(expected, quantiles))
    if len(bins) < 2:
        return 0.0
    expected_pct = np.histogram(expected, bins=bins)[0] / max(len(expected), 1)
    actual_pct = np.histogram(actual, bins=bins)[0] / max(len(actual), 1)
    expected_pct = np.clip(expected_pct, eps, None)
    actual_pct = np.clip(actual_pct, eps, None)
    # renormalize after clipping
    expected_pct = expected_pct / expected_pct.sum()
    actual_pct = actual_pct / actual_pct.sum()
    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def gini_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Ranking Gini via 2 * AUC - 1 on a median-split of y_true.

    Measures whether predictions preserve relative order of outcomes,
    not only absolute error.
    """
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    threshold = np.median(y_true)
    y_binary = (y_true >= threshold).astype(int)
    if y_binary.min() == y_binary.max():
        return 0.0
    auc = float(roc_auc_score(y_binary, y_pred))
    return 2.0 * auc - 1.0


def k2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    D'Agostino–Pearson K² statistic on residuals (y_true - y_pred).

    Tests departure from normality in residual shape. Reported as the
    K2 statistic (higher ⇒ residuals less normal). Companion to MSE:
    small errors can still be systematically skewed or heavy-tailed.
    """
    residuals = np.asarray(y_true, dtype=float).ravel() - np.asarray(
        y_pred, dtype=float
    ).ravel()
    if len(residuals) < 8:
        return float("nan")
    statistic, _p_value = stats.normaltest(residuals)
    return float(statistic)


def evaluate_regression(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    reference_for_psi: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute MSE, PSI, Gini, and K2 on the test set."""
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    ref = y_true if reference_for_psi is None else np.asarray(reference_for_psi, dtype=float).ravel()
    return {
        "mse": mse(y_true, y_pred),
        "psi": population_stability_index(ref, y_pred),
        "gini": gini_score(y_true, y_pred),
        "k2": k2_score(y_true, y_pred),
    }
