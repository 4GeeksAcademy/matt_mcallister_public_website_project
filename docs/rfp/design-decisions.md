# Milestone 9 RFP Design Decisions

Authoritative requirements: [`CONTEXT-milestone-9.md`](../../CONTEXT-milestone-9.md).

## Pipeline layout

- Graph and agent logic live under `data/pipelines/rfp_intake/` (not the CX agent graph).
- HTTP routes in `services/incident-api` import and trigger the pipeline; they do not own agent logic.
- Uploaded files land under `data/raw/rfp/` at intake time.

## Scope-based departments

The orchestrator assigns only `warehouse`, `lastmile`, and/or `reverse` based on requested services. Services marked “not in scope” (e.g. client-owned last mile) are excluded. Unknown department names are not invented.

## Worker shared state

Workers receive shared metadata plus department-relevant extracts only. Missing volumes become open questions — workers never invent pallet/SKU/order counts absent from the RFP.

## Classifier false negatives

Valid RFPs must match at least two RFP markers. False negatives remain `discarded`. The carrier rate pitch fixture (`carrier_pitch.txt`) must be rejected.

## Part 1 → Part 2 → Part 3 status flow

| Status | Part | When |
| --- | --- | --- |
| `analyzing` | 1 | Upload accepted; pipeline running |
| `discarded` | 1 | Classifier rejected the document |
| `intake_complete` | 1 | Synthesizer done |
| `drafting` / `under_evaluation` | 2 | Generator–evaluator loop |
| `waiting_for_approval` | 3 | Human pause per department |
| `done` | 3 | Final document generated |

`run_rfp_intake_only()` stops after Part 1; Celery/sync full path runs all parts sequentially.

## Per-department generators

Each active department has its own generator module under `draft/generators/` (`warehouse.py`, `lastmile.py`, `reverse.py`).

## Compliance evaluator (§5)

Structured checks for currency (USD/US, EUR/Spain), on-time SLA %, no under-48h returns, volume discount tier table, and no carrier negotiated rates. Failures populate `EvaluationResult.compliance` with `rule_ids` and `violations`.

## Structured CONTEXT conflict triggers (§7)

| Trigger id | Detection | Fixed arbiter |
| --- | --- | --- |
| `volume-vs-capacity` | `lastmile` monthly volume exceeds `warehouse` capacity | Miguel Torres |
| `returns-sla-breach` | Any section promises returns under 48 hours | Sofía Ramos / Miguel Torres |
| `currency-mismatch` | Active sections quote conflicting currencies | Miguel Torres |

Agents may surface conflicts; the arbitration node resolves them deterministically — not via LLM consensus.

## Async crash behavior

Celery runs the pipeline asynchronously. Failures set ticket status to `failed` with `error_message` persisted so polling stays truthful.

## Evaluator concurrency

Parallel evaluators write to namespaced `evaluations[department_id]` keys via per-department merge helpers without blocking other departments.

## Surfacing `needs_human_review`

Ticket status becomes `needs_human_review` when `MAX_SECTION_ITERATIONS` is exhausted. Department progress stores the latest failing `EvaluationResult`.

## Post-interruption approval

Checkpoints are namespaced `rfp-{ticket_id}:{department_id}`. Approving department B does not clear department A’s interrupt. `reject` / `request_changes` routes back to the Part 2 generator for that department only.

## Persistence

PostgreSQL is the production source of truth when `DATABASE_URL` is set (`RFP_STORE_BACKEND=postgres` or default). Tests use `RFP_STORE_BACKEND=memory`.

## Minimum human approval payload

Approvers see department id, draft excerpt, overall pass flag, compliance violations, and iteration count.
