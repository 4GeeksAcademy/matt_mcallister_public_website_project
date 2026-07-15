# Telemetry Implementation Guide — TrackFlow

This document consolidates the full telemetry rollout plan across four milestones, tailored to **TrackFlow** (warehousing + last-mile delivery for fashion, electronics, and cosmetics brands, operating between Los Angeles and Zaragoza):

1. **Design** — Data opportunity catalogue & event envelope design
2. **Stub Endpoint** — Fake backend + frontend instrumentation
3. **Real Endpoint** — Supabase storage + full validation
4. **Analysis & Reporting** — Pandas metrics pipeline + report endpoint

The inventory system is the operational heart of TrackFlow — the stock of every client's SKU, in every warehouse. All mandatory telemetry revolves around it, and this same data will later feed Ana's warehouse operations dashboard and Thomas's global executive dashboard (US vs. Spain volume/SLA comparison). Design fields with that future aggregation in mind: **by warehouse, by client, by country.**

## Domain Reference

| Entity | At TrackFlow this means... |
|---|---|
| `Product` | A SKU belonging to a client (brand), e.g. `t-shirt size M — Fashion Co`, `bluetooth headset — ElectroBrand`. Has a category (`fashion`/`electronics`/`cosmetics`) and belongs to a client. |
| `InboundOrder` | Receipt of goods from a client at a warehouse (LA or Zaragoza). |
| `OutboundOrder` | Picking and dispatching of an order to the carrier. |
| `warehouse` | `los_angeles` or `zaragoza`. |
| `client` | The B2B brand that owns the SKU. |

### Mandatory Metrics (the floor — must be in the plan and fully instrumented by the end of the series)

| `event_type` | Fires when... | Business hypothesis | Decision it enables |
|---|---|---|---|
| `inbound_order_created` | A warehouse registers receipt of goods from a client | Need to know inbound volume, by client and warehouse | Plan warehouse capacity/staffing (Ana) |
| `outbound_order_created` | A warehouse completes picking and dispatch of an order | Need to know order throughput, by client and warehouse, and at what rate | Detect operational bottlenecks before they hit delivery SLA (Ana) |
| `stock_threshold_triggered` | A SKU's stock falls below the client's configured minimum | Need to know how often a client runs low on a SKU | Alert client + commercial team before a stockout (Miguel) |
| `direct_stock_edit_rejected` | A user attempts to modify stock directly (outside an order) and the system rejects it | Need to know if staff attempt to bypass traceability controls | Reinforce training/permissions at the offending warehouse |
| `inventory_discrepancy_detected` | A physical count/audit finds a difference between system and actual stock | Need to know which SKUs/warehouses see the most discrepancies | Prioritise inventory audits on the highest-discrepancy SKUs (Ana) |

**Minimum `properties` for every inventory event** (on top of the standard envelope): `warehouse` (`los_angeles`/`zaragoza`), `client_id`, `product_id` (SKU), `product_category`, `quantity`.

> ⚠️ Never include end-consumer personal data (package recipient) in `properties` — these events describe warehouse inventory, not individual home deliveries.

### Business Constraints (drive validation logic)

- Stock is never modified directly: every change must go through `InboundOrder` or `OutboundOrder`, traceable to a user. Any direct attempt must fire `direct_stock_edit_rejected` and be blocked.
- Each SKU belongs to a single client — never mix inventory across clients under the same `product_id`.
- Inventory events never include carrier or end-recipient data (out of scope — belongs to the last-mile domain).

### Seed Data Targets (for Milestone 3 end-to-end verification)

- 8–10 distinct SKUs across ≥2 clients, covering all 3 categories (fashion, electronics, cosmetics)
- Both warehouses represented (Los Angeles and Zaragoza)
- 15–20 inbound orders distributed across both warehouses
- 15–20 outbound orders
- At least 2 events that trigger `stock_threshold_triggered` and 1 that triggers `inventory_discrepancy_detected`

---

## Milestone 1 — Design: Catalogue & Event Envelope

### Phase 1 — Exhaustive Catalogue of Data Opportunities

- [ ] Confirm the 5 mandatory metrics above (`inbound_order_created`, `outbound_order_created`, `stock_threshold_triggered`, `direct_stock_edit_rejected`, `inventory_discrepancy_detected`) are in your plan as the floor. They are not optional and not a ceiling.
- [ ] Map the **inventory management flow**: from an authenticated user accessing the system to completing an inbound or outbound order. The 5 mandatory events already cover the main instrumentation points (creation, threshold breach, rejected direct edit, discrepancy) — identify at least one more point in that flow (e.g. a failed order validation) so you meet the **5+ instrumentation point minimum** with real coverage, not just the bare mandatory list.
- [ ] Explore, without capping yourself at a minimum count, other backoffice sections that can also provide valuable data: authentication (login attempts, expired sessions, credential failures), performance (API response times, load times), uncaught frontend errors, and navigation (which sections operators visit most, which flows get abandoned). The goal is a broad catalogue, not a minimalist list checked off as a formality. At TrackFlow, also consider warehouse-specific opportunities beyond the 5 mandatory events — e.g. picking time per order, carrier handoff, or per-client SLA breaches.
- [ ] For each opportunity you identify, complete the sentence: *"We capture `[event_type]` because we need to know `[hypothesis]`, which allows us to make the decision `[decision]`."* If you cannot complete it, discard the event. Use the mandatory metrics table above as the template — each row already models this sentence for you.
- [ ] Classify every event in your catalogue into two groups: **mandatory** (the 5 events above, from CONTEXT) or **identified opportunity** (you proposed it). This gives the team visibility into what is baseline and what is exploration.

> ⚠️ **IMPORTANT:** The mandatory metrics, entities, and identifiers in your plan must match exactly what CONTEXT-trackflow specifies (`event_type` names, `properties` keys like `warehouse`/`client_id`/`product_id`/`product_category`/`quantity`). In addition, the catalogue of additional opportunities is expected to be broad and well-grounded — a plan that only covers the mandatory minimum, without exploring the rest of the application, will not be accepted.

### Phase 2 — Event Envelope Design

- [ ] Define the **standard Event Envelope** your company will use: the mandatory fields every event must include (`eventId`, `timestamp` in ISO 8601, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId` for correlation, and `properties` for event-specific payload).
- [ ] Design the complete schema for **all 5 mandatory metrics** (table above), plus **at least 8 additional events** from your catalogue, covering at least 3 distinct categories (e.g. inventory/business, authentication, performance, errors, navigation). Each `event_type` must follow the `entity_action` taxonomy with consistent verbs — TrackFlow's own mandatory events already model this: `inbound_order_created`, `stock_threshold_triggered`, `direct_stock_edit_rejected`. Extend the same pattern for your additional events, e.g. `session_expired`, `api_latency_recorded`.
- [ ] For each event, define a **property allowlist**: an explicit list of the permitted keys for that event. For all inventory events this allowlist must include, at minimum, `warehouse`, `client_id`, `product_id`, `product_category`, `quantity` — nothing outside the allowlist should be included, and never end-consumer/recipient personal data.
- [ ] For each event, specify: `event_type`, description, `properties` (name, type, required/optional, description), and whether it contains sensitive data or PII — in which case document how it is anonymised or sanitised before the event is emitted.
- [ ] Export the schemas to the `event-schemas.json` file with a validatable structure (you may use JSON Schema draft-07 or a documented custom structure).

### Phase 3 — Delivery Strategy

- [ ] For each event designed, decide and justify whether it should be processed as **stream** (real time) or **batch** (periodic batches). The justification must be based on the urgency of the decision it feeds or the operational need to detect it quickly — not on technical preference.
- [ ] Document the **throttle/debounce** strategy for high-frequency events (if any exist in your design).
- [ ] Write a **risks and exclusions** section in the plan: events you considered and discarded, and why; data that will not be captured for privacy or cost reasons. At minimum, document the exclusion of end-consumer/recipient personal data from inventory events per the CONTEXT constraint (that belongs to the separate last-mile tracking domain).

---

## Milestone 2 — Stub Endpoint & Frontend Instrumentation

### Phase 1 — Stub Endpoint in FastAPI

> ⚠️ This endpoint is **temporary and for verification purposes**. Its only purpose is to let you check that the payload arrives on the correct format. In Phase 3 (next project) you will replace it with the real implementation including full validation and persistence in Supabase.

- [ ] Create the `POST /telemetry/events` endpoint in the backend, in its own router inside `services/`. For now it should:
  - Accept a body with the shape `{ "events": [...] }`
  - Log the number of events received and the `event_type` of each one
  - Return `200 OK` with `{ "received": N }` where N is the number of events in the batch
- [ ] Define the Pydantic model `TelemetryEvent` with the standard envelope fields from your plan (`eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`). This model will be reused as-is in Phase 3 — define it properly from the start.
- [ ] Read the endpoint URL from the `TELEMETRY_ENDPOINT` environment variable in the backend, even if you are not using it to redirect traffic yet. Establish the pattern from the beginning.

### Phase 2 — TelemetryService in the Frontend

- [ ] Create `uis/backoffice/src/services/telemetry.ts` (or equivalent) with the following responsibilities:
  - **Local queue:** accumulate events in memory as an internal array
  - **Batch + debounce:** send the queue to `NEXT_PUBLIC_TELEMETRY_ENDPOINT` every 10 seconds or when the queue reaches 20 events, whichever comes first
  - **Reliable flush:** use `navigator.sendBeacon` on the `visibilitychange` event to guarantee pending events are sent when the tab is closed or hidden
  - **Retry with backoff:** if sending fails, retry up to 3 times with exponential wait before discharging the batch
- [ ] The service must automatically add to each event: `eventId` (UUID generated at capture time), `sessionId` (generated at login and stored in session memory), `userId` (from the authenticated session), `timestamp` in ISO 8601 at the moment of capture, `schemaVersion` from a shared constant, and `requestId` for correlation. Components calling `track()` must not pass these fields manually.
- [ ] Expose a single public function `track(eventType: string, properties: Record<string, unknown>): void`. The `eventType` argument becomes the envelope `event_type`. All backoffice tracking goes through this function — never through direct `fetch` or `axios`.

### Phase 3 — Broad Instrumentation: Technical and Business

- [ ] Instrument, without exception, **every mandatory metric** from your `CONTEXT-company.md` (through your approved plan).
- [ ] Instrument a **cross-cutting technical baseline**, one that applies to any part of the application and not just the inventory module:
  - Uncaught frontend errors (`window.onerror`, `unhandledrejection`, or Error Boundaries)
  - At least one performance metric (page load time or the latency of a relevant API call)
  - Page view / navigation tracking on at least the main sections of the backoffice
- [ ] Instrument the rest of the business events from your plan that you prioritised (inventory or other flows in your company), respecting the property allowlist defined for each event in your `event-schemas.json`. Do not add extra properties "just in case".
- [ ] Verify in the browser DevTools (Network tab) that batches are reaching the stub endpoint with the correct format and that the backend responds 200.

> ⚠️ **IMPORTANT:** `event_type` values and `properties` keys must match your approved Phase 1 schemas, which were grounded in the TrackFlow CONTEXT (`inbound_order_created`, `stock_threshold_triggered`, etc., with `warehouse`/`client_id`/`product_id`/`product_category`/`quantity` properties). Copying generic event names from this README instead of your plan will not be accepted.

---

## Milestone 3 — Real Endpoint & Supabase Storage

### Phase 1 — Storage Table in Supabase

- [ ] Create the `telemetry_events` table in Supabase with the following structure.
- [ ] Map each `TelemetryEvent` from the API to a table row using this contract.
- [ ] Create the three indexes that make the table queryable at scale: on `timestamp`, on `event_type`, and a GIN index on `tags` for searches inside the JSONB.
- [ ] Confirm the table has no UPDATE or DELETE logic — telemetry events are immutable once recorded.

### Phase 2 — Real Endpoint in FastAPI

- [ ] Replace the stub with the full implementation. The real endpoint must:
  - Accept the same envelope as the stub: `{ "events": [...] }` — parse the list loosely; do **not** declare `events: list[TelemetryEvent]` as the FastAPI body type (see partial validation above)
  - Validate each raw event individually with `TelemetryEvent.model_validate(...)` inside the handler — the same model from the previous phase, without modifying it
  - Reject individually the events that don't meet the contract, **without cancelling the batch** — valid events in the same batch are persisted regardless
  - Insert the valid events into `telemetry_events` in a single bulk insert operation
  - Return `{ "received": N, "stored": M, "rejected": R }` where N is the total received, M the persisted, and R the rejected
- [ ] Verify that the real endpoint's response is compatible with the existing frontend — the `TelemetryService` only looks at the HTTP status code, not the response body.

### Phase 3 — End-to-End Verification

- [ ] With the real endpoint active, use the backoffice to generate real events: register at least one inbound order and one outbound order in the inventory module, and generate at least one technical event (an error, a failed login, etc.).
- [ ] Query the `telemetry_events` table directly in Supabase and confirm that events appear with the correct fields — especially `event_type`, `timestamp`, and `tags`.
- [ ] Test the rejection behaviour: send manually (with curl or your preferred HTTP client) a batch that mixes valid and invalid events and verify that the response correctly reflects `stored` and `rejected`.

---

## Milestone 4 — Analysis Pipeline & Reporting

### Phase 1 — Analysis Pipeline with Pandas

- [ ] Create `services/telemetry/analysis.py` with at least **3 metric functions**, each encapsulating the calculation of a distinct operational dimension from your own event catalogue. At TrackFlow, valid examples drawn from the mandatory events include: inbound/outbound order volume per day per warehouse, stock threshold breach rate per client, and discrepancy rate per warehouse — adapt to what you actually captured.
- [ ] Each function must be **independent and side-effect free** — calling it twice with the same parameters must produce the same result.
- [ ] Do not use loops to calculate metrics — only Pandas operations (`.groupby()`, `.agg()`, `.count()`, `.sum()`, `.mean()`).

> ⚠️ **IMPORTANT:** The metrics you choose must answer **technical or operational** questions about the system's behaviour — volume, errors, latency, availability — not business questions (sales, conversion, revenue). A business report disguised as a technical report will not be accepted; that analysis belongs to the Data Pipelines milestone.

### Phase 2 — Report Endpoint

- [ ] Create the `GET /telemetry/report` endpoint in FastAPI. It must:
  - Accept optional query parameters `start_date` and `end_date` in ISO 8601 format; if not provided, default to the last 7 days (`start_date = now - 7d`, `end_date = now`, both UTC)
  - Resolve the period once and pass `start_date` / `end_date` to every metric function — functions do not apply their own default window
  - Call the metric functions from the analysis pipeline with those parameters
  - Return a JSON with the structure:
    ```json
    {
      "period": { "from": "...", "to": "..." },
      "metrics": {
        "events_per_day": [...],
        "error_rate_by_type": [...]
      }
    }
    ```
- [ ] The endpoint **must not run the pipeline on every request** — implement a simple in-memory cache with a 60-second TTL. If the same `start_date`/`end_date` combination is requested within the TTL, return the cached result without recalculating.

### 🔵 Additional Activity — Authentication Metric

- [ ] If you instrumented the authentication flow in the previous project, add a third metric function that calculates the **daily login failure rate**: `user_login_failed` divided by total login attempts (`user_login_failed` + `user_login_succeeded`) per day. Load both event types with `event_type IN (...)` in SQL, then compute the ratio in Pandas. Include it in the endpoint under the key `auth_failure_rate`.

### 🔵 Additional Activity — Simple Visual Dashboard

- [ ] Build a minimal page in `uis/backoffice/` (e.g. `/telemetry`) that fetches `GET /telemetry/report` and renders it visually — a chart or table per metric is enough (bar/line chart for `events_per_day`, `error_rate_by_type`, etc.). Use any charting library already available in the frontend, or a simple HTML table if you'd rather keep it minimal.
- [ ] The page should let you pick or display the current `period` (`from`/`to`) being shown, so it's clear what window the numbers cover.
- [ ] This dashboard is a **technical** view for the engineering team, not a business dashboard — keep it visualizing the same operational metrics from your report, nothing more.
- [ ] No need for polish here: a working, readable visualization of real data is the goal, not a design exercise.

---

## Quick Reference: File Map

| Purpose | Path |
|---|---|
| Telemetry event Pydantic model & stub/real endpoint | `services/telemetry/` (router) |
| Analysis pipeline (Pandas metric functions) | `services/telemetry/analysis.py` |
| Event schema definitions | `event-schemas.json` |
| Frontend telemetry service | `uis/backoffice/src/services/telemetry.ts` |
| Optional visual dashboard | `uis/backoffice/` (e.g. `/telemetry` page) |
| Supabase table | `telemetry_events` |
| Company requirements source of truth | `CONTEXT-company.md` |

## Environment Variables

| Variable | Used by | Purpose |
|---|---|---|
| `TELEMETRY_ENDPOINT` | Backend | Reference to the telemetry endpoint URL |
| `NEXT_PUBLIC_TELEMETRY_ENDPOINT` | Frontend | Target URL for batched event delivery |
