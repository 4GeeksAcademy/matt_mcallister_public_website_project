# TrackFlow Incident Analysis API

Backend service exposing analysis and export endpoints for incident CSV files.

Heavy analysis runs asynchronously via Celery (see [`../celery_app/README.md`](../celery_app/README.md)).

## Run with Docker Compose (recommended)

From the repo root:

```bash
docker compose up --build
```

API: http://127.0.0.1:8001 — docs at `/docs`.

If something else is already bound to host port 8001, call the API from inside Compose (`docker compose exec api ...`) or change the published port mapping in `docker-compose.yml`.

## Run locally

```bash
# Terminal 1: Redis + Postgres (from repo root)
docker compose up redis postgres -d

# Terminal 2: Celery worker
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql://trackflow:trackflow@localhost:5432/trackflow
export UPLOAD_DIR=/tmp/trackflow_uploads
export PYTHONPATH=.
pip install -r services/api/requirements.txt
celery -A services.celery_app.celery worker --loglevel=info

# Terminal 3: API
cd services/api
export REDIS_URL=redis://localhost:6379/0
export UPLOAD_DIR=/tmp/trackflow_uploads
export PYTHONPATH=../..
uvicorn app.main:app --reload --port 8001
```

Use port **8001** by default so this service does not conflict with other APIs on port 8000.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/analyze` | Upload CSV; returns `202` with `{"task_id": "..."}` immediately |
| GET | `/tasks/{task_id}` | Poll Celery status (`pending`, `started`, `success`, `failure`) and result |
| POST | `/export` | Upload CSV, returns metrics CSV download (synchronous) |

### Async analyze flow

```bash
# Enqueue
curl -s -X POST http://127.0.0.1:8001/analyze \
  -F "file=@sample_incidents.csv"
# → {"task_id":"..."}

# Poll
curl -s http://127.0.0.1:8001/tasks/<task_id>
```

Docs: http://127.0.0.1:8001/docs
