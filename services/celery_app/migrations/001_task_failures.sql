-- TrackFlow: Celery dead-letter queue for exhausted async task retries.
-- Apply with: psql "$DATABASE_URL" -f services/celery_app/migrations/001_task_failures.sql
--
-- Separate from job_runs (nightly cron orchestration). Do not reuse job_runs for
-- per-request Celery tasks.

CREATE TABLE IF NOT EXISTS task_failures (
    id              BIGSERIAL PRIMARY KEY,
    task_id         TEXT NOT NULL,
    attempt         INTEGER NOT NULL,
    error_message   TEXT NOT NULL,
    failed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_failures_task_id
    ON task_failures (task_id);

CREATE INDEX IF NOT EXISTS idx_task_failures_failed_at
    ON task_failures (failed_at);
