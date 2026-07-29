# `data/raw` folder

This folder is intended for **raw data** related to the company: dumps, exports, sample files, event samples, or untransformed datasets.

- **Main purpose**: serve as a landing zone or reference for original data before pipelines process it.
- **Recommendation**: document each dataset’s origin, format, expected size, privacy/PII considerations, and how it is versioned (ideally avoiding sensitive data in the repository).

## TrackFlow sales

| File | Description |
|------|-------------|
| `trackflow_sales.csv` | Monthly sales slices (2016–2025) for forecasting |
| `CONTEXT-company.md` | Column schema, seasonality, and growth rules |

Regenerate with: `python data/pipelines/sales-forecast/generate_sales.py`

> _Spanish version: [README.es.md](./README.es.md)._
