# `telemetry-stream` pipeline

Real-time and batch telemetry pipeline for TrackFlow warehouse operations and backoffice activity.

## Purpose

This folder holds the schema definitions and (future) ingestion configuration for TrackFlow's centralized telemetry system. Events are emitted from `services/inventory-api/` and `uis/backoffice/` and flow through stream or batch processors as defined in [docs/telemetry/telemetry-plan.md](../../../docs/telemetry/telemetry-plan.md).

## Contents

| File | Description |
|------|-------------|
| `event-schemas.json` | JSON Schema draft-07 definitions for all telemetry events |
| `README.md` | This file |

## Event schema

All events share a standard envelope (`eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`) and follow the `entity_action` naming taxonomy.

Supported `event_type` values:

- `session_started`, `credential_failed`, `session_expired`
- `product_created`, `product_create_rejected`
- `inbound_order_created`, `outbound_order_created`, `outbound_order_rejected`
- `stock_threshold_triggered`
- `page_viewed`, `form_abandoned`

## Validating events

Install a JSON Schema validator and validate sample events against the schema:

```bash
# Using ajv-cli (install once: npm install -g ajv-cli)
npx ajv-cli validate \
  -s data/pipelines/telemetry-stream/event-schemas.json \
  -d data/pipelines/telemetry-stream/sample-event.json \
  --spec=draft7 \
  --strict=false
```

### Sample event

`sample-event.json` in this folder can be used to test validation:

```json
{
  "eventId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-07-07T14:30:00.000Z",
  "sessionId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "userId": "usr_7f3a2b1c",
  "event_type": "inbound_order_created",
  "schemaVersion": "1.0.0",
  "requestId": "req_9e8d7c6b",
  "properties": {
    "order_id": 42,
    "product_id": 7,
    "sku": "TF-SHOE-001",
    "quantity": 50,
    "warehouse_location": "los_angeles",
    "client_brand": "AcmeApparel"
  }
}
```

## Processing modes

| Mode | Events | Sink (future) |
|------|--------|---------------|
| Stream | `stock_threshold_triggered`, `outbound_order_rejected`, `credential_failed`, `session_started` | Real-time alert bus |
| Batch (hourly) | `session_expired`, `product_create_rejected`, `form_abandoned` | Data warehouse staging |
| Batch (nightly) | `inbound_order_created`, `outbound_order_created`, `product_created`, `page_viewed` | Executive dashboard ETL |

See Phase 3 in the telemetry plan for business-urgency justifications.

## Related files

- [docs/telemetry/telemetry-plan.md](../../../docs/telemetry/telemetry-plan.md) — full design document
- [packages/shared/types/telemetry.ts](../../../packages/shared/types/telemetry.ts) — TypeScript envelope types
