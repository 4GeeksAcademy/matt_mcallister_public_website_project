# `telemetry-stream` pipeline

Real-time and batch telemetry pipeline for TrackFlow warehouse operations and backoffice activity.

## Purpose

This folder holds the schema definitions and (future) ingestion configuration for TrackFlow's centralized telemetry system. Events are emitted client-side from `uis/backoffice/` (inventory and telemetry pages) via `track()` into the operations API at `POST /telemetry/events` (`services/main.py`). They are not emitted from `services/inventory-api`. See [docs/telemetry/telemetry-plan.md](../../../docs/telemetry/telemetry-plan.md).

## Contents

| File | Description |
|------|-------------|
| `event-schemas.json` | JSON Schema draft-07 definitions for all telemetry events |
| `README.md` | This file |

## Event schema

All events share a standard envelope (`eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`) and follow the `entity_action` naming taxonomy.

Supported `event_type` values match the backoffice runtime:

- Inventory: `inbound_order_created`, `outbound_order_created`, `outbound_order_rejected`, `stock_threshold_triggered`, `direct_stock_edit_rejected`, `inventory_discrepancy_detected`, `inbound_order_validation_failed`, `picking_duration_recorded`
- Authentication: `user_login_succeeded`, `user_login_failed`, `session_expired`
- Technical/navigation: `page_viewed`, `page_load_recorded`, `api_latency_recorded`, `frontend_error_uncaught`, `flow_abandoned`

Inventory properties use the canonical runtime identifiers `warehouse`, `client_id`, `product_id`, `product_category`, and `quantity`.

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
    "warehouse": "los_angeles",
    "client_id": "client_fashion_co",
    "product_id": "SKU-F-001",
    "product_category": "fashion",
    "quantity": 50,
    "order_id": "IN-42"
  }
}
```

## Processing modes

| Mode | Events | Sink (future) |
|------|--------|---------------|
| Stream | `stock_threshold_triggered`, `outbound_order_rejected`, `direct_stock_edit_rejected`, `user_login_failed`, `frontend_error_uncaught` | Real-time alert bus |
| Batch (hourly) | `session_expired`, `inbound_order_validation_failed`, `flow_abandoned` | Data warehouse staging |
| Batch (nightly) | Inventory success/discrepancy events, performance events, `user_login_succeeded`, `page_viewed` | Reporting and dashboard ETL |

See Phase 3 in the telemetry plan for business-urgency justifications.

## Related files

- [docs/telemetry/telemetry-plan.md](../../../docs/telemetry/telemetry-plan.md) — full design document
- [packages/shared/types/telemetry.ts](../../../packages/shared/types/telemetry.ts) — TypeScript envelope types
