# TrackFlow Telemetry — Data Opportunity Catalogue

## Inventory management flow (instrumentation map)

1. Authenticated user opens backoffice → `page_viewed`, `page_load_recorded`
2. User logs in → `user_login_succeeded` / `user_login_failed`
3. Session expires or is abandoned → `session_expired`
4. User creates inbound receipt → validate → `inbound_order_created` or `inbound_order_validation_failed`
5. User completes outbound pick/dispatch → `outbound_order_created`; may also fire `stock_threshold_triggered`
6. User attempts direct stock edit → blocked → `direct_stock_edit_rejected`
7. Physical count/audit reconcile → `inventory_discrepancy_detected`
8. API calls for inventory → `api_latency_recorded`
9. Uncaught UI errors anywhere → `frontend_error_uncaught`

---

## Mandatory metrics (floor)

| event_type | Hypothesis | Decision | Classification |
|---|---|---|---|
| `inbound_order_created` | We need inbound volume by client and warehouse | Plan warehouse capacity/staffing (Ana) | mandatory |
| `outbound_order_created` | We need order throughput by client/warehouse and rate | Detect bottlenecks before delivery SLA impact (Ana) | mandatory |
| `stock_threshold_triggered` | We need how often a client runs low on a SKU | Alert client + commercial before stockout (Miguel) | mandatory |
| `direct_stock_edit_rejected` | We need if staff attempt to bypass traceability controls | Reinforce training/permissions at offending warehouse | mandatory |
| `inventory_discrepancy_detected` | We need which SKUs/warehouses see most discrepancies | Prioritise audits on highest-discrepancy SKUs (Ana) | mandatory |

**Minimum properties (inventory events):** `warehouse`, `client_id`, `product_id`, `product_category`, `quantity`.

---

## Identified opportunities

| event_type | Hypothesis | Decision | Classification |
|---|---|---|---|
| `inbound_order_validation_failed` | We need how often inbound payloads fail validation and why | Fix data-entry UX or client ASN quality at the source | identified opportunity |
| `user_login_succeeded` | We need successful auth volume by day | Confirm backoffice availability for ops shifts | identified opportunity |
| `user_login_failed` | We need credential/auth failure rate | Spot lockouts, phishing, or shared-password misuse | identified opportunity |
| `session_expired` | We need how often sessions expire mid-flow | Tune session TTL vs security trade-offs | identified opportunity |
| `page_viewed` | We need which backoffice sections operators visit most | Prioritise UX for high-traffic flows | identified opportunity |
| `page_load_recorded` | We need page load times for main sections | Target performance regressions before they slow picking | identified opportunity |
| `api_latency_recorded` | We need latency of inventory API calls | Scale or optimise slow endpoints | identified opportunity |
| `frontend_error_uncaught` | We need uncaught UI errors in production | Triage and fix the highest-frequency UI failures | identified opportunity |
| `picking_duration_recorded` | We need time from outbound start to dispatch by warehouse | Staffing and layout decisions for slow pick zones | identified opportunity |
| `flow_abandoned` | We need which multi-step flows are abandoned mid-way | Simplify or train on high-abandon flows | identified opportunity |

---

## Sentence template (applied)

> We capture `[event_type]` because we need to know `[hypothesis]`, which allows us to make the decision `[decision]`.

Events considered and discarded are listed in `DELIVERY_STRATEGY.md` (risks & exclusions).
