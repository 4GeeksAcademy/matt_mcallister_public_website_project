-- TrackFlow: job_runs (orchestration), pipeline_runs (pipeline internals),
-- and minimal telemetry_events for nightly export.
-- Apply with: psql "$DATABASE_URL" -f services/incident-api/migrations/001_job_runs_and_telemetry.sql
--
-- job_runs and pipeline_runs coexist with separate responsibilities:
--   job_runs      -> scripts/nightly_export.py executions
--   pipeline_runs -> data.pipelines.* executions (e.g. telemetry_kpi_daily)

CREATE TABLE IF NOT EXISTS job_runs (
    id              BIGSERIAL PRIMARY KEY,
    job_name        TEXT NOT NULL,
    target_date     DATE NOT NULL,
    status          TEXT NOT NULL
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT job_runs_job_name_target_date_key UNIQUE (job_name, target_date)
);

CREATE INDEX IF NOT EXISTS idx_job_runs_job_name_target_date
    ON job_runs (job_name, target_date);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              BIGSERIAL PRIMARY KEY,
    pipeline_name   TEXT NOT NULL,
    target_date     DATE NOT NULL,
    status          TEXT NOT NULL
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_name_target_date
    ON pipeline_runs (pipeline_name, target_date);

CREATE TABLE IF NOT EXISTS telemetry_events (
    id              BIGSERIAL PRIMARY KEY,
    occurred_at     TIMESTAMPTZ NOT NULL,
    event_type      TEXT NOT NULL,
    user_id         TEXT,
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_events_occurred_at
    ON telemetry_events (occurred_at);
