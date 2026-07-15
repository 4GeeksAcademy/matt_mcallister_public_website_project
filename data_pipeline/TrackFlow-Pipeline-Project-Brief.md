# TrackFlow — Weekly Warehouse & Client Performance Pipeline

_Consolidated project brief: business context + full task checklist (Design → Implementation → Subflows & Tests)_

---

## Part A — Business Context (`CONTEXT-trackflow-pipeline.md`)

### 1. The business deliverable

Thomas (CEO) wants a **weekly report** he can open without calling Ana or Miguel, comparing how each warehouse is performing per client — the thing his directors currently spend hours assembling by hand every Sunday night.

> **Target deliverable:** a weekly, per-warehouse, per-client rollup of throughput, stockout activity, and inventory accuracy — the **"Weekly Warehouse & Client Performance Report."**

This is the **one concrete deliverable** the pipeline exists to produce. Everything in `PIPELINE_DESIGN.md` should trace back to it.

- **Audience:** Thomas (CEO) and Ana (Head of Warehouse Operations) — non-technical stakeholders who need numbers, not raw events.
- **Cadence:** weekly (fresh as of Monday morning, matching the existing "automated weekly executive report" expectation leadership already has).

### 2. KPIs to Measure

| KPI | What it measures | Why it matters to TrackFlow |
|---|---|---|
| **Inbound Volume** | How many units of a client's goods a warehouse received during the week. | Shows incoming workload per warehouse and client — basis for capacity planning (Ana). |
| **Outbound Throughput** | How many orders a warehouse picked and dispatched for a client during the week. | Processing-capacity signal — how much a warehouse can actually move, not just receive. |
| **Stockout Frequency** | How many times during the week a client's SKU at a warehouse fell below the configured minimum. | Early warning before a client-facing stockout occurs — Miguel needs this to manage client expectations. |
| **Discrepancy Rate** | The share of the week's outbound orders associated with a detected inventory discrepancy. | Inventory-accuracy signal — flags which warehouse/client combinations need an audit. |

### 3. Source data

Source: `telemetry_events`, filtered to the mandatory metrics already defined in the telemetry CONTEXT.

| `event_type` | Feeds which KPI(s) |
|---|---|
| `inbound_order_created` | Inbound Volume |
| `outbound_order_created` | Outbound Throughput, Discrepancy Rate (denominator) |
| `stock_threshold_triggered` | Stockout Frequency |
| `inventory_discrepancy_detected` | Discrepancy Rate (numerator) |

No event outside this list is needed for v1 — resist the urge to widen scope.

### 4. Required aggregation

- **Grain:** one row per `warehouse` per `client_id` per ISO week (`week_start` = the Monday of that week, UTC).
- **Dimensions:** `warehouse` (`los_angeles`/`zaragoza`), `client_id`, `week_start`.
- **Computed fields per row:**
  - `inbound_units_count` — Inbound Volume: sum of quantities from `inbound_order_created` for the week
  - `outbound_orders_count` — Outbound Throughput: count of `outbound_order_created` for the week
  - `stockout_events_count` — Stockout Frequency: count of `stock_threshold_triggered` for the week
  - `discrepancy_events_count` — supporting count of `inventory_discrepancy_detected` for the week
  - `discrepancy_rate` — Discrepancy Rate: `discrepancy_events_count / outbound_orders_count` (0 if no orders that week)

No currency dimension — this deliverable is operational (volume and accuracy), not cost-based.

### 5. Destination table

Create under a dedicated `reporting` schema — never write into `telemetry_events`:

```sql
create table reporting.weekly_warehouse_client_performance (
  id uuid primary key default gen_random_uuid(),
  warehouse text not null,
  client_id text not null,
  week_start date not null,
  inbound_units_count integer not null default 0,
  outbound_orders_count integer not null default 0,
  stockout_events_count integer not null default 0,
  discrepancy_events_count integer not null default 0,
  discrepancy_rate numeric not null default 0,
  computed_at timestamptz not null default now(),
  unique (warehouse, client_id, week_start)
);
```

The `unique (warehouse, client_id, week_start)` constraint is what the idempotency strategy (upsert) should rely on.

### 6. New reporting endpoint

Expose the pipeline's output through a **new** module, `services/reporting/`, separate from `services/telemetry/`:

- `GET /reporting/weekly-warehouse-client-performance` — accepts optional `week_start` (defaults to the most recent computed week); returns all warehouse/client combinations for that week:

```json
{
  "week_start": "2026-07-13",
  "entries": [
    {
      "warehouse": "los_angeles",
      "client_id": "fashion-co",
      "inbound_units_count": 4200,
      "outbound_orders_count": 980,
      "stockout_events_count": 3,
      "discrepancy_events_count": 2,
      "discrepancy_rate": 0.002
    }
  ]
}
```

- `GET /reporting/pipeline-runs/latest` — status and metadata of the last pipeline run (reusable pattern for future pipelines).
- `POST /reporting/pipeline-runs` — triggers a manual run.

### 7. Business constraints

- Each row belongs to a single client — never aggregate across clients within the same row.
- This pipeline reads `telemetry_events` **read-only**. It never writes back to it.
- `services/telemetry/analysis.py` and `GET /telemetry/report` are out of scope for this milestone — do not modify them.

---

## Part B — What You Need to Do

### 🖥️ Stage 1: Current State Analysis & Pipeline Design

**Phase 1 — Current state analysis**
- [ ] Document in a "Current State" section what you already have: the telemetry events captured so far, where they're stored, and what your existing technical report already answers for engineering.
- [ ] Identify the gap: which business question from your `CONTEXT-company.md` is still unanswered by that technical report, and would require a dedicated pipeline?

**Phase 2 — Pipeline design**
- [ ] Define the **purpose** of the pipeline in a single concrete sentence: name the specific business deliverable you're targeting (e.g., "produce the daily rollup that feeds [role]'s weekly executive report"), the KPI(s) it computes (from your `CONTEXT-company.md`'s "KPIs to Measure" section), and the mandatory metric(s) from your telemetry CONTEXT it's built on.
- [ ] Specify the **extraction format**: your source is `telemetry_events` (plus any other existing domain tables you need) — in what format the data arrives, and how often it's updated.
- [ ] Design the **data flow** with a text or Mermaid diagram showing at least three clearly separated stages: extraction, transformation, and load.
- [ ] Describe how you would handle a source that **updates existing records** rather than always inserting new ones — explain the concrete strategy to avoid duplicates in your specific case.
- [ ] Name the **new destination table(s)** under the `reporting` schema (`reporting.business_metrics`) where this pipeline's output will live, and the **new endpoint(s)** in `services/reporting/` that will expose it — explicitly separate from `telemetry_events` and `GET /telemetry/report`.

**Phase 3 — Resilience and idempotency**
- [ ] Define your **idempotency strategy**: if the pipeline fails during the load phase and is re-run, explain exactly how you guarantee that already-loaded data is neither corrupted nor duplicated.
- [ ] Design your **execution log**: specify the minimum fields you would record in every run (start time, end time, records processed, status, errors) and explain why each field is necessary to audit the pipeline in production.

**Phase 4 — Mapping to Prefect**
- [ ] Map your design to Prefect concepts: identify which parts would be **flows**, which would be **tasks**, and which **states** (Running, Completed, Failed) are relevant for your pipeline.
- [ ] Indicate which configuration or credentials you would manage as **Prefect blocks** (for example, the connection to Supabase).

**Phase 5 — Application integration (design only)**
- [ ] Sketch the **new endpoint(s)** in `services/reporting/` the business side will use to query the resulting metric(s) and/or trigger a run — kept separate from `services/telemetry/` and the `GET /telemetry/report` endpoint.
- [ ] For each endpoint, state which **function or flow** in `data/pipelines/` it will call — no ETL logic belongs in `services/`.

> ⚠️ **IMPORTANT:** Field names, entity IDs, and domain-specific values in your design must match your company's domain vocabulary in the monorepo. A generic design that ignores your company's data model will not be accepted.

---

### 🖥️ Stage 2: Implementation

**Phase 1 — Flows and tasks**
- [ ] Implement the pipeline as one or more Prefect **flows** (`@flow`) following the stage structure from your design: extraction, transformation, and load as a minimum.
- [ ] Each stage must be an independent **task** (`@task`) with explicit inputs and outputs.
- [ ] If your pipeline has optional steps (for example, notifications or secondary exports), invoke them with `return_state=True` so that a failure in them does not interrupt the main execution.

**Phase 2 — Resilience**
- [ ] Add `retries` and `retry_delay_seconds` to every task that interacts with external services (database, APIs). Justify the number of retries chosen in a comment.
- [ ] Handle at least one task failure explicitly in the flow using `return_state=True` rather than letting it propagate automatically.
- [ ] Add caching (`cache_key_fn`, `cache_expiration`) to at least one expensive transformation task. Explain in a comment what defines the cache key and how long it is valid.

**Phase 3 — Idempotency**
- [ ] The load phase must be idempotent: if the pipeline runs twice over the same data range, the result in your `reporting.business_metrics` table must be identical after both runs. Implement the strategy you documented in your design (upsert, control table, timestamp, or another) — the unique constraint from your `CONTEXT-company.md` schema is what your upsert should key off.
- [ ] Record in the database or in a log file the minimum execution metadata for each run: start time, end time, records processed, final status, and any captured errors.

**Phase 4 — Script-based execution**
- [ ] Ensure `data/pipelines/pipeline.py` can be executed directly as a CLI script (for example, with an `if __name__ == "__main__"` block that invokes the main flow).
- [ ] Verify the full pipeline runs without errors: `python data/pipelines/pipeline.py`.
- [ ] Document the intended schedule for your company's reporting cycle in `data/pipelines/PIPELINE_DESIGN.md` and the run command in a comment or the same design doc.

**Phase 5 — Backend endpoints**
- [ ] In `services/reporting/`, implement at least two endpoints related to this pipeline: one to query the status and metadata of the last run, and one to trigger a manual flow run. Keep them in their own module, separate from `services/telemetry/`.
- [ ] The endpoints must import flows or functions from `data/pipelines/` — do not duplicate pipeline logic in `services/`.
- [ ] The endpoints follow the same authentication conventions and response structure as the rest of your API, and the KPI query endpoint's response shape matches the contract in your `CONTEXT-company.md`.

> ⚠️ **IMPORTANT:** Flow names, task names, table names, and field names must match what is defined in `data/pipelines/PIPELINE_DESIGN.md` and your `CONTEXT-company.md` from the data pipelines context (KPIs and schema) — consistent, in turn, with the event fields already defined in your telemetry `CONTEXT-company.md`. A generic implementation that ignores your company's data model will not be accepted.

---

### 🖥️ Stage 3: Subflows, Tests, and Dashboard

**Phase 1 — Refactoring into subflows**
- [ ] Split the main flow into at least three subflows (`@flow`) that correspond to the stages from your design: one for extraction (from `telemetry_events` and any other domain tables), one for transformation, and one for load (into your `reporting.business_metrics` table). The main flow invokes them in sequence.
- [ ] Each subflow must have explicit inputs and outputs — do not rely on global variables between subflows.
- [ ] If you have optional steps (notifications, secondary exports), extract them as subflows too and invoke them with `return_state=True` from the main flow.

**Phase 2 — Unit tests**
- [ ] Create the file `tests/pipelines/test_pipeline.py` with unit tests for at least three transformation tasks — the ones that compute the KPIs from your `CONTEXT-company.md`.
- [ ] Each test must verify the task's behaviour in isolation: it must not depend on a database or external APIs. Use in-memory test data shaped like your telemetry events (per your `CONTEXT-company.md`).
- [ ] Include at least one test that verifies the defensive behaviour of a task against invalid or malformed input (for example, a null field where none is expected, or an incorrect type).
- [ ] Include at least one test that asserts a computed KPI value matches the definition in your `CONTEXT-company.md` for a known, hand-calculated input.
- [ ] The tests must pass with `python -m pytest tests/pipelines/test_pipeline.py` without errors.

**Phase 3 — Script-based execution**
- [ ] Ensure `data/pipelines/pipeline.py` can be executed directly as a CLI script (for example, with an `if __name__ == "__main__"` block that invokes the main flow).
- [ ] Verify the full pipeline runs without errors: `python data/pipelines/pipeline.py`.
- [ ] Document the run command in a comment or in `data/pipelines/PIPELINE_DESIGN.md`.

**Phase 4 — Business dashboard (mandatory)**

> Your pipeline produces KPIs — but a table nobody looks at isn't a deliverable. This phase is not optional: leadership needs to actually *see* the numbers, not query an endpoint with curl.

- [ ] Build a page in `uis/backoffice/` (e.g. `/reporting`) that fetches your `services/reporting/` endpoint and renders every KPI from your `CONTEXT-company.md`'s "KPIs to Measure" section — a chart or a table per KPI is enough.
- [ ] Label each KPI clearly with the same name it has in your `CONTEXT-company.md`, and show the period (week or month, per your cadence) the data covers.
- [ ] This dashboard is business-facing, not a developer tool: it should be legible to the stakeholder named in your `CONTEXT-company.md` (e.g. the CEO or department head) without needing anything translated or explained.
- [ ] No need for visual polish — a working, correctly labeled view of real data from `reporting.business_metrics` is the goal.

> ⚠️ **IMPORTANT:** Subflow names, task names, and test names must follow the same domain vocabulary defined in `data/pipelines/PIPELINE_DESIGN.md` and your `CONTEXT-company.md`. A subflow named `extract_data` is not acceptable if your company has concrete entities and KPI names — name it after the actual business metric this pipeline produces.

**🔵 Additional Activity — Extra Enhancements from Your Design Questions**
- [ ] Go back to the "Questions to Help You Design the Pipeline" section from Part 1. If, while answering those questions, you identified resilience or observability enhancements beyond what Phases 1–3 already cover (for example, a heartbeat plus silence alert, a concurrency lock for overlapping runs, or an `Idempotency-Key` pattern for retries) and haven't implemented them yet, this is the place to do it.
- [ ] For each enhancement you add, note in `data/pipelines/PIPELINE_DESIGN.md` which question it answers and why you prioritized it.
- [ ] This is optional — only pick it up if your own design doc actually flagged something worth building. Don't invent an enhancement just to check a box.

---

## Quick Reference — Naming Consistency Checklist

Applying the TrackFlow domain vocabulary from Part A, your implementation should consistently use:

| Concept | TrackFlow-specific name |
|---|---|
| Destination schema | `reporting` |
| Destination table | `reporting.weekly_warehouse_client_performance` |
| Dimensions | `warehouse`, `client_id`, `week_start` |
| KPI fields | `inbound_units_count`, `outbound_orders_count`, `stockout_events_count`, `discrepancy_events_count`, `discrepancy_rate` |
| Source events | `inbound_order_created`, `outbound_order_created`, `stock_threshold_triggered`, `inventory_discrepancy_detected` |
| New service module | `services/reporting/` |
| Query endpoint | `GET /reporting/weekly-warehouse-client-performance` |
| Run status endpoint | `GET /reporting/pipeline-runs/latest` |
| Trigger endpoint | `POST /reporting/pipeline-runs` |
| Warehouse values | `los_angeles`, `zaragoza` |
