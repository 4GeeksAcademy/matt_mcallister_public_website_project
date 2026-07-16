# `data/pipelines` folder

This folder groups **all data pipelines in the monorepo** related to the company: ingestion, ETL/ELT, cleaning, transformation, and loading into analytical or production systems.

Each subfolder or file under `data/pipelines/` should represent **one pipeline or job set** (for example `sales-etl`, `telemetry-stream`, `customer-segmentation`) and include the required configuration (scripts, orchestration, connectors, schemas, etc.).

- **Main purpose**: consolidate in one place the data movement and transformation logic that powers the company’s applications and analytics.
- **Recommendation**: document pipelines as you add them—their goal, data sources and sinks, dependencies, and how to run them in development, testing, and production.

## Pipelines

### `telemetry_kpi_daily`

Stub pipeline triggered by `scripts/nightly_export.py`. Reads `telemetry_events` from Postgres (`DATABASE_URL`); does **not** read CSV snapshots under `data/raw/`. Each execution writes a row to `pipeline_runs` (pipeline layer), while `nightly_export` writes to `job_runs` (orchestration layer).

```bash
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect
# Optional:
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect --target-date 2025-01-15
```

> _Spanish version: [README.es.md](./README.es.md)._
