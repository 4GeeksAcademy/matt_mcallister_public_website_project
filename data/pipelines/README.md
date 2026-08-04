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

Nightly pipeline triggered by `scripts/nightly_export.py`. It reads the target
UTC day directly from Postgres `telemetry_events` (`DATABASE_URL`), never from
CSV snapshots, and idempotently upserts one row into
`reporting.telemetry_kpi_daily`.

The daily reporting row contains:

- `event_count`: total events, useful for traffic and ingestion-volume trends
- `unique_user_count`: distinct non-null telemetry users
- `event_type_counts`: JSON object containing the event mix by `event_type`
- `computed_at`: the latest successful calculation time

`target_date` is the primary key, so retrying a date refreshes its aggregates
without creating duplicate reporting rows. Each execution also writes a
`pipeline_runs` row (pipeline layer), while `nightly_export` writes to
`job_runs` (orchestration layer).

```bash
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect
# Optional:
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect --target-date 2025-01-15
```

> _Spanish version: [README.es.md](./README.es.md)._
