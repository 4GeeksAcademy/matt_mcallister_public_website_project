-- Reporting schema for Weekly Warehouse & Client Performance pipeline.
-- Source telemetry_events remains read-only; this migration never writes to it.

CREATE SCHEMA IF NOT EXISTS reporting;

CREATE TABLE IF NOT EXISTS reporting.weekly_warehouse_client_performance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  warehouse text NOT NULL,
  client_id text NOT NULL,
  week_start date NOT NULL,
  inbound_units_count integer NOT NULL DEFAULT 0,
  outbound_orders_count integer NOT NULL DEFAULT 0,
  stockout_events_count integer NOT NULL DEFAULT 0,
  discrepancy_events_count integer NOT NULL DEFAULT 0,
  discrepancy_rate numeric NOT NULL DEFAULT 0,
  computed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (warehouse, client_id, week_start)
);

CREATE INDEX IF NOT EXISTS weekly_wh_client_perf_week_idx
  ON reporting.weekly_warehouse_client_performance (week_start);

CREATE TABLE IF NOT EXISTS reporting.pipeline_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  flow_run_id text,
  week_start date,
  started_at timestamptz NOT NULL,
  finished_at timestamptz,
  records_processed integer NOT NULL DEFAULT 0,
  status text NOT NULL,
  error_message text
);

CREATE INDEX IF NOT EXISTS pipeline_runs_started_at_idx
  ON reporting.pipeline_runs (started_at DESC);

GRANT USAGE ON SCHEMA reporting TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA reporting TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA reporting
  GRANT SELECT, INSERT, UPDATE ON TABLES TO anon, authenticated, service_role;
