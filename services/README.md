# TrackFlow services

Backend services for the TrackFlow monorepo.

| Path | Role |
|------|------|
| [`api/`](api/) | FastAPI incident analysis API (`POST /analyze`, `GET /tasks/{task_id}`, `POST /export`) |
| [`celery_app/`](celery_app/) | Celery worker tasks, Redis broker client, and DLQ (`task_failures`) |

## Docker (Redis + Celery + API)

From the repo root:

```bash
docker compose up --build
```

| Service | URL / port |
|---------|------------|
| API | http://127.0.0.1:8001 |
| Flower | http://127.0.0.1:5555 |
| Redis | `localhost:6379` |
| Postgres (DLQ) | `localhost:5432` |

See [`celery_app/README.md`](celery_app/README.md) for local (non-Docker) worker commands.

> Nightly export / `job_runner` / `job_runs` are a separate orchestration path and are not used by these per-request Celery tasks.
