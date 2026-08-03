# Event Envelope — TrackFlow

Shared schema version: **1.0.0**

Every telemetry event includes:

| Field | Type | Source |
|---|---|---|
| `eventId` | UUID string | Generated at capture (`track()`) |
| `timestamp` | ISO 8601 | Capture instant |
| `sessionId` | string | Set at login via `setTelemetryIdentity` |
| `userId` | string | Authenticated operator id |
| `event_type` | string | Argument to `track()` |
| `schemaVersion` | string | `SCHEMA_VERSION` constant |
| `requestId` | string | Correlation id per event |
| `properties` | object | Allowlisted keys only (see `event-schemas.json`) |

Components must call `track(eventType, properties)` only — never send envelope fields manually.

Full per-event property allowlists:
[`../data/pipelines/telemetry-stream/event-schemas.json`](../data/pipelines/telemetry-stream/event-schemas.json).
Delivery modes and exclusions: [`DELIVERY_STRATEGY.md`](DELIVERY_STRATEGY.md).
