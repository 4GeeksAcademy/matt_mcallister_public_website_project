# TrackFlow Telemetry — Delivery Strategy

## Standard event envelope

Every event includes:

| Field | Type | Notes |
|---|---|---|
| `eventId` | string (UUID) | Generated at capture time |
| `timestamp` | string (ISO 8601) | Capture instant, UTC |
| `sessionId` | string | Generated at login; session memory |
| `userId` | string | From authenticated session |
| `event_type` | string | `entity_action` taxonomy |
| `schemaVersion` | string | Shared constant (e.g. `"1.0.0"`) |
| `requestId` | string | Correlation id for the flush/request |
| `properties` | object | Event-specific allowlisted payload |

## Stream vs batch

| event_type | Mode | Justification |
|---|---|---|
| `inbound_order_created` | batch | Capacity planning is daily/hourly; near-real-time not required |
| `outbound_order_created` | batch | Throughput dashboards tolerate ~10s delay |
| `stock_threshold_triggered` | stream | Low-stock alerts should reach Miguel/commercial quickly |
| `direct_stock_edit_rejected` | stream | Security/control violations should surface immediately |
| `inventory_discrepancy_detected` | batch | Audit prioritisation runs on periodic reviews |
| `inbound_order_validation_failed` | batch | Form quality trends; not instant-pager |
| `user_login_succeeded` | batch | Auth volume analytics are periodic |
| `user_login_failed` | stream | Spike detection for lockouts/attacks needs low latency |
| `session_expired` | batch | TTL tuning is not real-time |
| `page_viewed` | batch | Navigation heatmaps are aggregated |
| `page_load_recorded` | batch | Perf baselines are aggregated; high volume |
| `api_latency_recorded` | batch | Latency percentiles computed in windows |
| `frontend_error_uncaught` | stream | Production UI failures need fast triage |
| `picking_duration_recorded` | batch | Ops staffing uses shift-level aggregates |
| `flow_abandoned` | batch | UX prioritisation is weekly/periodic |

**Frontend delivery note:** The Milestone 2 `TelemetryService` always batches to the endpoint (10s / 20 events). “Stream” events are still sent via the same queue but are flushed immediately when enqueued (urgency flush), while “batch” events wait for the timer/size threshold. `sendBeacon` always drains the pending queue on tab hide.

## Throttle / debounce

| event_type | Strategy |
|---|---|
| `page_viewed` | Debounce identical `path` within 1s (Strict Mode / remount) |
| `page_load_recorded` | Once per page load (performance mark) |
| `api_latency_recorded` | Sample or flush with batch; no more than one event per request |
| `frontend_error_uncaught` | Throttle identical `message`+`path` to 1 per 30s |
| All others | No throttle; emit on business action |

## Risks and exclusions

### Discarded opportunities

| Candidate | Why discarded |
|---|---|
| `package_recipient_viewed` | End-consumer PII; belongs to last-mile domain, not inventory telemetry |
| `carrier_assigned` | Carrier/last-mile scope; out of inventory mandate |
| `keystroke_heatmap` | High volume + privacy cost; poor decision value |
| `mouse_move_sampled` | Cost and noise; discarded for privacy and storage cost |

### Explicit exclusions (privacy / cost)

- **No end-consumer / recipient personal data** in inventory event `properties` (name, address, phone, email). That data belongs to last-mile tracking.
- **No carrier identifiers** on inventory events.
- **No raw credentials** or password fields on auth events — only outcome flags and optional failure reason codes.
- **No full stack traces with secrets** — error events may include truncated `message` and `path` only.

### Operational risks

- Batch loss on hard browser kill before `sendBeacon` — mitigated by short flush interval and beacon.
- Schema drift if frontend emits non-allowlisted keys — mitigated by server-side validation (M3) and documented allowlists in `event-schemas.json`.
