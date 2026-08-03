# `data/pipelines` folder

This folder groups **all data pipelines in the monorepo** related to the company: ingestion, ETL/ELT, cleaning, transformation, and loading into analytical or production systems.

## Weekly Warehouse & Client Performance

| File | Role |
|------|------|
| [`PIPELINE_DESIGN.md`](./PIPELINE_DESIGN.md) | Design: KPIs, grain, idempotency, Prefect mapping |
| [`pipeline.py`](./pipeline.py) | Prefect ETL (extract / transform / load subflows) |
| [`reporting_store.py`](./reporting_store.py) | Destination upsert + query helpers (no Prefect) |
| [`requirements.txt`](./requirements.txt) | Prefect + pandas + pytest |

```bash
cd data/pipelines && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../..
WEEK_START=2026-07-06 python data/pipelines/pipeline.py
python -m pytest tests/pipelines/test_pipeline.py
```

Schedule: Mondays ~07:00 UTC (see design doc).

## Pipelines

### `telemetry_kpi_daily`

Stub pipeline triggered by `scripts/nightly_export.py`. Reads `telemetry_events` from Postgres (`DATABASE_URL`); does **not** read CSV snapshots under `data/raw/`. Each execution writes a row to `pipeline_runs` (pipeline layer), while `nightly_export` writes to `job_runs` (orchestration layer).

```bash
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect
# Optional:
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect --target-date 2025-01-15
```

> _Spanish version: [README.es.md](./README.es.md)._
