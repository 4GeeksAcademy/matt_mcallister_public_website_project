# TrackFlow Services

FastAPI backend for inventory stubs, telemetry, and weekly reporting.

## Setup

```bash
cd services
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill SUPABASE_URL and SUPABASE_KEY (anon or service role)
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Pipeline triggers also need the Prefect env under `data/pipelines/`:

```bash
cd data/pipelines
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| POST | `/telemetry/events` | Ingest event batch |
| GET | `/telemetry/report` | Operational metrics (60s cache) |
| GET | `/inventory/products` | SKU catalogue |
| GET | `/inventory/stock` | Current stock |
| POST | `/inventory/inbound` | Create inbound order |
| POST | `/inventory/outbound` | Create outbound order |
| POST | `/inventory/stock/direct-edit` | Always rejects |
| POST | `/inventory/discrepancy` | Record audit discrepancy |
| POST | `/inventory/auth/login` | Demo login (`password=trackflow`) |
| GET | `/reporting/weekly-warehouse-client-performance` | Weekly warehouse/client KPIs |
| GET | `/reporting/pipeline-runs/latest` | Latest ETL run metadata |
| POST | `/reporting/pipeline-runs` | Trigger weekly ETL (calls `data/pipelines/pipeline.py`) |

## Supabase

Apply migrations under [`supabase/migrations/`](supabase/migrations/) if tables are missing:

1. `001_telemetry_events.sql` — immutable telemetry store
2. `002_fix_telemetry_rls.sql` — RLS/grants
3. `003_reporting_weekly_performance.sql` — `reporting` schema + KPI + run-log tables

Without Supabase credentials the weekly pipeline falls back to `data/raw/telemetry_events.jsonl` → `data/process/reporting.db`.
