# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Scripts

### `nightly_export.py`

Scheduled orchestration job that:

1. Resolves `target_date` from `TARGET_DATE` or **yesterday UTC**
2. Skips if another `nightly_export` run is `processing`, or if `(nightly_export, target_date)` is already `completed`
3. Exports `telemetry_events` for that day to `data/raw/telemetry_YYYY-MM-DD.csv` (only if the file is missing — audit snapshot only)
4. Triggers `python -m data.pipelines.telemetry_kpi_daily.run --no-prefect`
5. Records the result in `job_runs` (`pending` → `processing` → `completed` \| `failed`)
6. The pipeline records its own execution in `pipeline_runs` (separate table)

**Requirements**

```bash
pip install -r requirements.txt
# Apply schema once:
psql "$DATABASE_URL" -f services/api/migrations/001_job_runs_and_telemetry.sql
# If you already applied an older 001 without pipeline_runs:
psql "$DATABASE_URL" -f services/api/migrations/002_pipeline_runs.sql
```

**Environment**

| Variable       | Required | Description                                      |
| -------------- | -------- | ------------------------------------------------ |
| `DATABASE_URL` | yes      | Postgres connection string                       |
| `TARGET_DATE`  | no       | Override day as `YYYY-MM-DD` (for tests/backfill) |

**Manual run**

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/trackflow"
python scripts/nightly_export.py

# Backfill a specific day:
TARGET_DATE=2025-01-15 python scripts/nightly_export.py
```

**Production trigger (OS crontab)**

Runs as a **separate process** — not inside FastAPI / the API lifespan.

```cron
# Daily at 02:15 UTC
15 2 * * * cd /path/to/milestone_project_trackflow_getmystatsup-12 && DATABASE_URL=postgresql://... /usr/bin/python3 scripts/nightly_export.py >> /var/log/trackflow-nightly-export.log 2>&1
```
