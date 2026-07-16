# `services` folder

Backend services and shared server-side modules for TrackFlow.

## Layout

| Path | Role |
| ---- | ---- |
| `api/migrations/` | SQL schema migrations (Postgres) |
| `job_runner/` | Create / update / query `job_runs` for orchestration jobs |

## `job_runner`

Used by `scripts/nightly_export.py` for idempotency and status tracking. Requires `DATABASE_URL` and the migrations in `api/migrations/`.

## Tracking layers (do not merge)

| Table | Owner | Tracks |
| ----- | ----- | ------ |
| `job_runs` | `services/job_runner` + `scripts/nightly_export.py` | Orchestration script executions |
| `pipeline_runs` | `data/pipelines/tracking.py` + pipeline modules | Individual pipeline executions (e.g. `telemetry_kpi_daily`) |

They coexist with separate responsibilities so each layer can fail, retry, and report independently.
