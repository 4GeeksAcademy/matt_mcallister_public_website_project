-- RFP ticket persistence for Milestone 9 Agentic RFP Workflow
-- Apply with: psql "$DATABASE_URL" -f services/incident-api/migrations/003_rfp_tickets.sql

CREATE TABLE IF NOT EXISTS rfp_tickets (
    id                  TEXT PRIMARY KEY,
    filename            TEXT NOT NULL,
    status              TEXT NOT NULL,
    pdf_path            TEXT NOT NULL DEFAULT '',
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    readability_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message       TEXT,
    payload             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rfp_tickets_status ON rfp_tickets (status);

CREATE TABLE IF NOT EXISTS rfp_node_logs (
    id              BIGSERIAL PRIMARY KEY,
    ticket_id       TEXT NOT NULL REFERENCES rfp_tickets(id) ON DELETE CASCADE,
    department_id   TEXT,
    node            TEXT NOT NULL,
    agent           TEXT NOT NULL,
    input_summary   TEXT NOT NULL DEFAULT '',
    output_summary  TEXT NOT NULL DEFAULT '',
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rfp_node_logs_ticket_id ON rfp_node_logs (ticket_id);
