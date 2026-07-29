"""Sklearn pipeline: one-hot categoricals + Ridge for CSAT regression."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from domain import FEATURE_COLUMNS

CATEGORICAL_FEATURES = ["country", "customer_type", "carrier", "category"]
NUMERIC_FEATURES = ["month", "day_of_week"]


def _one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_model(alpha: float = 1.0) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", _one_hot_encoder(), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("regressor", Ridge(alpha=alpha)),
        ]
    )


def feature_column_names() -> tuple[str, ...]:
    return FEATURE_COLUMNS
