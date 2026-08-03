-- Additive migration if 001 was applied before pipeline_runs existed.
-- Safe to run even when 001 already created the table (IF NOT EXISTS).

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
