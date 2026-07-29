# TrackFlow sales revenue forecast — notes

Trained with [`scripts/train_sales_model.py`](../../scripts/train_sales_model.py) on [`data/raw/trackflow_sales.csv`](../raw/trackflow_sales.csv).

- **Split:** 2016–2023 train (8y) / 2024–2025 test (2y)
- **Model:** `RandomForestRegressor` → [`sales_revenue_rf.joblib`](./sales_revenue_rf.joblib)
- **Metrics:** [`sales_metrics.json`](./sales_metrics.json)
- **Plot:** [`sales_forecast_test.png`](./sales_forecast_test.png) — actual vs prediction with tree-std band

**K2 Score** is reported as the Kolmogorov–Smirnov (KS) discrimination score (high vs low revenue months by median), the usual companion to Gini/PSI in validation packs.
