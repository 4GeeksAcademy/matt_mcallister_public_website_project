# Data Pipeline Project Plan

This project is broken into three parts. Complete them in order — each part builds on the deliverables of the previous one.

---

## Part 1 — Design the Pipeline

**Goal:** Document the current state and design the pipeline before writing implementation code.

### Phase 1 — Current State Analysis
- [ ] Document a "Current State" section: which telemetry events you already capture, where they're stored, and which reports you already generate with Pandas.
- [ ] Identify the limitations of your current implementation: what happens if the script fails mid-run? Can you tell whether data has already been processed?

### Phase 2 — Pipeline Design
- [ ] Define the **purpose** of the pipeline in a single concrete sentence: what problem it solves and what value it delivers to your company.
- [ ] Specify the **extraction format**: where data comes from (table, endpoint, file), what format it arrives in, and how often it's updated.
- [ ] Design the **data flow** with a text or Mermaid diagram showing at least three clearly separated stages: extraction, transformation, and load.
- [ ] Describe how you'd handle a source that **updates existing records** rather than always inserting new ones — explain the concrete strategy to avoid duplicates in your specific case.

### Phase 3 — Resilience and Idempotency
- [ ] Define your **idempotency strategy**: if the pipeline fails during the load phase and is re-run, explain exactly how you guarantee that already-loaded data is neither corrupted nor duplicated.
- [ ] Design your **execution log**: specify the minimum fields you'd record in every run (start time, end time, records processed, status, errors) and explain why each field is necessary to audit the pipeline in production.

### Phase 4 — Mapping to Prefect
- [ ] Map your design to Prefect concepts: identify which parts would be **flows**, which would be **tasks**, and which **states** (Running, Completed, Failed) are relevant for your pipeline.
- [ ] Indicate which configuration or credentials you'd manage as **Prefect blocks** (e.g., the connection to Supabase).

> ⚠️ **IMPORTANT:** Field names, entity IDs, and domain-specific values in your design must match what's specified in your `CONTEXT-company.md`. A generic design that ignores your company's context will not be accepted.

---

## Part 2 — Implement Flows and Tasks

**Goal:** Turn the design from Part 1 into a working Prefect pipeline.

### Phase 1 — Flows and Tasks
- [ ] Implement the pipeline as one or more Prefect **flows** (`@flow`) following the stage structure from your design: extraction, transformation, and load as a minimum.
- [ ] Each stage must be an independent **task** (`@task`) with explicit inputs and outputs.
- [ ] If your pipeline has optional steps (e.g., notifications or secondary exports), invoke them with `return_state=True` so that a failure in them does not interrupt the main execution.

### Phase 2 — Resilience
- [ ] Add `retries` and `retry_delay_seconds` to every task that interacts with external services (database, APIs). Justify the number of retries chosen in a comment.
- [ ] Handle at least one task failure explicitly in the flow using `return_state=True` rather than letting it propagate automatically.
- [ ] Add caching (`cache_key_fn`, `cache_expiration`) to at least one expensive transformation task. Explain in a comment what defines the cache key and how long it's valid.

### Phase 3 — Idempotency
- [ ] The load phase must be idempotent: if the pipeline runs twice over the same data range, the result in the database must be identical after both runs. Implement the strategy you documented in your design (upsert, control table, timestamp, or another).
- [ ] Record in the database or in a log file the minimum execution metadata for each run: start time, end time, records processed, final status, and any captured errors.

### Phase 4 — Script-Based Execution
- [ ] Ensure `data/pipelines/pipeline.py` can be executed directly as a CLI script (e.g., with an `if __name__ == "__main__"` block that invokes the main flow).
- [ ] Verify the full pipeline runs without errors: `python data/pipelines/pipeline.py`.
- [ ] Document the intended schedule for your company's data cycle in `data/pipelines/PIPELINE_DESIGN.md` and the run command in a comment or the same design doc.

### Phase 5 — Backend Endpoints
- [ ] In `services/`, implement at least two endpoints related to the pipeline: one to query the status and metadata of the last run, and one to trigger a manual flow run.
- [ ] The endpoints must import flows or functions from `data/pipelines/` — do not duplicate pipeline logic in `services/`.
- [ ] The endpoints follow the same authentication conventions and response structure as the rest of your API.

> ⚠️ **IMPORTANT:** Flow names, task names, table names, and field names must match what's defined in `data/pipelines/PIPELINE_DESIGN.md` and your monorepo's existing telemetry schema. A generic implementation that ignores your company's data model will not be accepted.

---

## Part 3 — Refactor, Test, and Harden

**Goal:** Split the pipeline into subflows and add proper test coverage.

### Phase 1 — Refactoring into Subflows
- [ ] Split the main flow into at least three subflows (`@flow`) that correspond to the stages from your design: one for extraction, one for transformation, and one for load. The main flow invokes them in sequence.
- [ ] Each subflow must have explicit inputs and outputs — do not rely on global variables between subflows.
- [ ] If you have optional steps (notifications, secondary exports), extract them as subflows too and invoke them with `return_state=True` from the main flow.

### Phase 2 — Unit Tests
- [ ] Create the file `tests/pipelines/test_pipeline.py` with unit tests for at least three transformation tasks.
- [ ] Each test must verify the task's behavior in isolation: it must not depend on a database or external APIs. Use in-memory test data.
- [ ] Include at least one test that verifies the defensive behavior of a task against invalid or malformed input (e.g., a null field where none is expected, or an incorrect type).
- [ ] The tests must pass with `python -m pytest tests/pipelines/test_pipeline.py` without errors.

### Phase 3 — Script-Based Execution
- [ ] Ensure `data/pipelines/pipeline.py` can be executed directly as a CLI script (e.g., with an `if __name__ == "__main__"` block that invokes the main flow).
- [ ] Verify the full pipeline runs without errors: `python data/pipelines/pipeline.py`.
- [ ] Document the run command in a comment or in `data/pipelines/PIPELINE_DESIGN.md`.

> ⚠️ **IMPORTANT:** Subflow names, task names, and test names must follow the same domain vocabulary defined in `data/pipelines/PIPELINE_DESIGN.md`. A subflow named `extract_data` is not acceptable if your company has concrete entities — name it `extract_sales_events` or whatever fits your domain.

---

## Progress Tracker

| Part | Description | Status |
|------|-------------|--------|
| 1 | Design the Pipeline | Complete |
| 2 | Implement Flows and Tasks | Complete |
| 3 | Refactor, Test, and Harden | Complete |
