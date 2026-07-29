"""MSE, PSI, Gini, and K2 (KS) metrics for TrackFlow sales regression."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_squared_error


def mse_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mse = float(mean_squared_error(y_true, y_pred))
    avg_revenue = float(np.mean(y_true))
    # RMSE as % of average monthly revenue (interpretable for Thomas/Ana).
    rmse = float(np.sqrt(mse))
    rmse_pct_of_avg = float(100.0 * rmse / avg_revenue) if avg_revenue else float("nan")
    mse_pct_of_avg_sq = (
        float(100.0 * mse / (avg_revenue**2)) if avg_revenue else float("nan")
    )
    return {
        "mse_eur2": mse,
        "rmse_eur": rmse,
        "avg_monthly_revenue_eur": avg_revenue,
        "mse_as_pct_of_avg_revenue_squared": mse_pct_of_avg_sq,
        "rmse_as_pct_of_avg_revenue": rmse_pct_of_avg,
    }


def population_stability_index(
    expected: np.ndarray,
    actual: np.ndarray,
    n_bins: int = 10,
    eps: float = 1e-6,
) -> float:
    """PSI between expected (train) and actual (test) distributions."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    quantiles = np.linspace(0, 1, n_bins + 1)
    breaks = np.unique(np.quantile(expected, quantiles))
    if len(breaks) < 3:
        breaks = np.linspace(expected.min(), expected.max(), n_bins + 1)

    expected_counts = np.histogram(expected, bins=breaks)[0].astype(float)
    actual_counts = np.histogram(actual, bins=breaks)[0].astype(float)
    expected_perc = expected_counts / expected_counts.sum()
    actual_perc = actual_counts / actual_counts.sum()
    expected_perc = np.clip(expected_perc, eps, None)
    actual_perc = np.clip(actual_perc, eps, None)
    return float(np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc)))


def _gini_from_ranking(actual: np.ndarray, pred: np.ndarray) -> float:
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    order = np.argsort(pred)
    actual_sorted = actual[order]
    n = len(actual_sorted)
    if n == 0 or actual_sorted.sum() == 0:
        return 0.0
    cum = np.cumsum(actual_sorted)
    # Area between Lorenz of ranked actuals and equality line proxy.
    return float((np.sum(cum) / (cum[-1] * n)) - (n + 1) / (2 * n))


def gini_normalized(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Normalized Gini (model vs perfect ranking). Higher = better separation."""
    perfect = _gini_from_ranking(y_true, y_true)
    if perfect == 0:
        return 0.0
    return float(_gini_from_ranking(y_true, y_pred) / perfect)


def k2_score_ks(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    K2 Score implemented as Kolmogorov–Smirnov discrimination (KS).

    Splits months into high vs low actual revenue (median), then measures
    separation of the predicted-score distributions — the usual companion
    metric to Gini/PSI in model validation (assignment name: K2 Score).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    threshold = np.median(y_true)
    high = y_pred[y_true >= threshold]
    low = y_pred[y_true < threshold]
    if len(high) == 0 or len(low) == 0:
        return 0.0

    scores = np.unique(np.concatenate([high, low]))
    scores.sort()
    best = 0.0
    for s in scores:
        cdf_high = np.mean(high <= s)
        cdf_low = np.mean(low <= s)
        best = max(best, abs(cdf_high - cdf_low))
    return float(best)


def interpret_psi(psi: float) -> str:
    if psi < 0.1:
        return "no significant shift"
    if psi < 0.25:
        return "moderate shift — monitor LA vs Zaragoza mix"
    return "significant shift — possible expansion/contraction in one country"
