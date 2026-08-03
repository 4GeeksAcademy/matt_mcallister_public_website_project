CREATE TABLE IF NOT EXISTS public.telemetry_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id text NOT NULL UNIQUE,
  timestamp timestamptz NOT NULL,
  event_type text NOT NULL,
  session_id text NOT NULL,
  user_id text NOT NULL,
  schema_version text NOT NULL,
  request_id text NOT NULL,
  tags jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS telemetry_events_timestamp_idx
  ON public.telemetry_events (timestamp);
CREATE INDEX IF NOT EXISTS telemetry_events_event_type_idx
  ON public.telemetry_events (event_type);
CREATE INDEX IF NOT EXISTS telemetry_events_tags_gin_idx
  ON public.telemetry_events USING gin (tags);

REVOKE UPDATE, DELETE ON public.telemetry_events FROM authenticated, anon;

ALTER TABLE public.telemetry_events ENABLE ROW LEVEL SECURITY;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT INSERT, SELECT ON TABLE public.telemetry_events TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

DROP POLICY IF EXISTS telemetry_events_insert ON public.telemetry_events;
DROP POLICY IF EXISTS telemetry_events_select ON public.telemetry_events;

CREATE POLICY telemetry_events_insert ON public.telemetry_events
  FOR INSERT WITH CHECK (true);

CREATE POLICY telemetry_events_select ON public.telemetry_events
  FOR SELECT USING (true);
