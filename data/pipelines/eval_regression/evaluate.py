"""Temporal cross-validation, MAE/RMSE, and learning-curve artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, learning_curve

from domain import N_SPLITS
from model import build_model


@dataclass
class FoldMetrics:
    fold: int
    train_mae: float
    train_rmse: float
    val_mae: float
    val_rmse: float
    n_train: int
    n_val: int
    max_train_idx: int
    min_val_idx: int


def make_time_series_split(n_splits: int = N_SPLITS) -> TimeSeriesSplit:
    """Return a temporal splitter that does not shuffle."""
    return TimeSeriesSplit(n_splits=n_splits)


def assert_fold_chronological(train_idx: np.ndarray, test_idx: np.ndarray) -> None:
    """Verify train precedes test and indices stay in chronological order."""
    if len(train_idx) == 0 or len(test_idx) == 0:
        raise AssertionError("Empty train or test fold")
    if not np.all(np.diff(train_idx) > 0):
        raise AssertionError("Train indices are not strictly increasing")
    if not np.all(np.diff(test_idx) > 0):
        raise AssertionError("Test indices are not strictly increasing")
    if train_idx.max() >= test_idx.min():
        raise AssertionError(
            f"Fold mixes chronology: max(train)={train_idx.max()} >= min(test)={test_idx.min()}"
        )


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def temporal_cross_validate(
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = N_SPLITS,
    alpha: float = 1.0,
) -> dict[str, Any]:
    splitter = make_time_series_split(n_splits=n_splits)
    folds: list[FoldMetrics] = []

    for fold_i, (train_idx, test_idx) in enumerate(splitter.split(X)):
        assert_fold_chronological(train_idx, test_idx)
        model = build_model(alpha=alpha)
        X_train, X_val = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[test_idx]
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        folds.append(
            FoldMetrics(
                fold=fold_i,
                train_mae=float(mean_absolute_error(y_train, train_pred)),
                train_rmse=_rmse(y_train.to_numpy(), train_pred),
                val_mae=float(mean_absolute_error(y_val, val_pred)),
                val_rmse=_rmse(y_val.to_numpy(), val_pred),
                n_train=len(train_idx),
                n_val=len(test_idx),
                max_train_idx=int(train_idx.max()),
                min_val_idx=int(test_idx.min()),
            )
        )

    val_maes = np.array([f.val_mae for f in folds])
    val_rmses = np.array([f.val_rmse for f in folds])
    train_maes = np.array([f.train_mae for f in folds])
    train_rmses = np.array([f.train_rmse for f in folds])

    return {
        "n_splits": n_splits,
        "primary_metric": "MAE",
        "folds": [asdict(f) for f in folds],
        "summary": {
            "val_mae_mean": float(val_maes.mean()),
            "val_mae_std": float(val_maes.std(ddof=1)),
            "val_rmse_mean": float(val_rmses.mean()),
            "val_rmse_std": float(val_rmses.std(ddof=1)),
            "train_mae_mean": float(train_maes.mean()),
            "train_mae_std": float(train_maes.std(ddof=1)),
            "train_rmse_mean": float(train_rmses.mean()),
            "train_rmse_std": float(train_rmses.std(ddof=1)),
            "primary_mean_pm_std": (
                f"{val_maes.mean():.4f} ± {val_maes.std(ddof=1):.4f}"
            ),
        },
    }


def plot_learning_curve(
    X: pd.DataFrame,
    y: pd.Series,
    output_path: Path,
    n_splits: int = N_SPLITS,
    alpha: float = 1.0,
) -> dict[str, Any]:
    """Train/validation MAE vs training size; save PNG under data/eval/."""
    splitter = make_time_series_split(n_splits=n_splits)
    model = build_model(alpha=alpha)
    train_sizes, train_scores, val_scores = learning_curve(
        model,
        X,
        y,
        cv=splitter,
        scoring="neg_mean_absolute_error",
        train_sizes=np.linspace(0.2, 1.0, 8),
        shuffle=False,
        n_jobs=1,
    )
    train_err = -train_scores.mean(axis=1)
    val_err = -val_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    val_std = val_scores.std(axis=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(train_sizes, train_err, "o-", label="Training MAE")
    ax.fill_between(train_sizes, train_err - train_std, train_err + train_std, alpha=0.15)
    ax.plot(train_sizes, val_err, "o-", label="Validation MAE")
    ax.fill_between(train_sizes, val_err - val_std, val_err + val_std, alpha=0.15)
    ax.set_xlabel("Training set size")
    ax.set_ylabel("MAE (error)")
    ax.set_title("Learning curve — TrackFlow satisfaction_score")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)

    gap = float((val_err - train_err)[-1])
    return {
        "train_sizes": train_sizes.tolist(),
        "train_mae_mean": train_err.tolist(),
        "val_mae_mean": val_err.tolist(),
        "final_train_mae": float(train_err[-1]),
        "final_val_mae": float(val_err[-1]),
        "final_gap": gap,
    }


def save_metrics(metrics: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
