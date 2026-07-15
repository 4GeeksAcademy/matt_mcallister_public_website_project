# TrackFlow Services

FastAPI backend for inventory stubs and telemetry.

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

## Supabase

Apply [`supabase/migrations/001_telemetry_events.sql`](supabase/migrations/001_telemetry_events.sql) if the table is missing.
Events are immutable (insert-only). Storage also mirrors in memory for local reports.
