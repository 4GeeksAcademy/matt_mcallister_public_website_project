# Celery app (async task queue)

Redis-backed Celery workers for heavy API work (incident CSV analysis).

## Environment

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Broker and result backend (required) |
| `DATABASE_URL` | Postgres for `task_failures` DLQ (required on final failure) |
| `UPLOAD_DIR` | Shared directory for uploaded CSVs (default `/data/uploads`) |

Copy [`.env.example`](../../.env.example) at the repo root for local values.

## Database migration (DLQ)

```bash
export DATABASE_URL=postgresql://trackflow:trackflow@localhost:5432/trackflow
psql "$DATABASE_URL" -f services/celery_app/migrations/001_task_failures.sql
```

With Docker Compose, the migration is applied automatically on first Postgres start via `docker-entrypoint-initdb.d`.

## Start / stop the worker (local)

Prerequisites: Redis and Postgres running (e.g. `docker compose up redis postgres -d`).

```bash
cd /path/to/repo
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt

export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql://trackflow:trackflow@localhost:5432/trackflow
export UPLOAD_DIR=/tmp/trackflow_uploads
export PYTHONPATH=.

# Start worker (separate process — never inside FastAPI)
celery -A services.celery_app.celery worker --loglevel=info

# Stop: Ctrl+C in the worker terminal
```

## Flower (local)

```bash
export REDIS_URL=redis://localhost:6379/0
export PYTHONPATH=.
celery -A services.celery_app.celery flower --port=5555
```

Open http://127.0.0.1:5555

## Task

- `analyze_incident(upload_id, source_file)` — reads `{UPLOAD_DIR}/{upload_id}.csv`, runs `run_analysis`, returns the analysis dict.
- Retries: `max_retries=3` with exponential backoff (`countdown` 2, 4, 8 seconds).
- After retries are exhausted, records `task_id`, attempt, error message, and timestamp in `task_failures`.
