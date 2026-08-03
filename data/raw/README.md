# `data/raw` folder

This folder is intended for **raw data** related to the company: dumps, exports, sample files, event samples, or untransformed datasets.

- **Main purpose**: serve as a landing zone or reference for original data before pipelines process it.
- **Recommendation**: document each dataset’s origin, format, expected size, privacy/PII considerations, and how it is versioned (ideally avoiding sensitive data in the repository).

## Nightly telemetry snapshots

`scripts/nightly_export.py` writes audit CSV snapshots named `telemetry_YYYY-MM-DD.csv` (UTC calendar day). These files are **backup/audit only** — the `telemetry_kpi_daily` pipeline reads from the database, never from these CSVs. Prefer keeping generated CSVs out of version control.

> _Spanish version: [README.es.md](./README.es.md)._
