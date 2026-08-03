-- Updated grants/policies (applied via MCP as fix_telemetry_rls_grants)
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT INSERT, SELECT ON TABLE public.telemetry_events TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

DROP POLICY IF EXISTS telemetry_events_insert ON public.telemetry_events;
DROP POLICY IF EXISTS telemetry_events_select ON public.telemetry_events;

CREATE POLICY telemetry_events_insert ON public.telemetry_events
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY telemetry_events_select ON public.telemetry_events
  FOR SELECT
  USING (true);
