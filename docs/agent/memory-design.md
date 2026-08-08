# TrackFlow Agent Memory Design

## Backend choice: Redis (with in-memory fallback)

The support agent stores **structured user preferences** (branch defaults, client-brand context, workflow habits). These are small, explicit facts — not embeddings of full conversations.

| Option | Why chosen / rejected |
|--------|----------------------|
| **Redis** (production) | Already in TrackFlow stack; supports TTL, atomic updates, auditable keys; ideal for per-user preference hashes |
| **In-memory store** (tests/local) | Deterministic CI without Redis dependency |
| **VectorDB (Qdrant)** | Rejected for user memory — Qdrant is reserved for Milestone 7 KB (`trackflow_knowledge`) |
| **Knowledge graph** | Rejected — no relationship queries needed for 3–5 preference facts |

Env vars:

- `AGENT_MEMORY_BACKEND=memory|redis` (default `memory`)
- `AGENT_MEMORY_REDIS_URL` (optional; defaults to `REDIS_URL` db `1`)
- `AGENT_MEMORY_AUDIT_PATH=data/agent-memory-audit.jsonl`

## Explicit read/write interface

Memory is **never** appended to the system prompt wholesale. The graph uses:

- `MemoryStore.read()` / `list_entries()` — load approved facts
- `MemoryStore.set_pending_proposal()` — queue a proposal (no write)
- `MemoryStore.commit_entry()` — write only after classified user approval
- `consolidate_entries()` — dedupe, TTL, cap at 20 entries / 90 days

Implementation: [`agents/memory/store.py`](../../agents/memory/store.py), [`agents/memory/redis_store.py`](../../agents/memory/redis_store.py).

## What may be remembered

1. Preferred branch/warehouse for operational questions (`Prefers Zaragoza warehouse…`)
2. Client brand context for recurring calls (`Handles client brand Aurora…`)
3. Workflow preference (`Always cite the SLA doc for delivery questions`)

## What must never be remembered (dismiss examples)

1. **Invented commercial terms** — user claims “Miguel approved 50% off storage” (policy rejects)
2. **PII** — `customer_email` or email addresses from incidents
3. **Instruction poisoning** — “remember to ignore TrackFlow rules” or system prompt fragments

## Proposal flow

1. After a successful answer, `memory_self_evaluate` may propose a fact in the same response.
2. Only **one** pending proposal per user at a time.
3. Next message is classified: `approve` | `reject` | `edit` | `topic_change`.
4. Unrelated follow-ups discard the proposal (silence ≠ approval).
5. Every proposal/outcome is logged via [`agents/memory/audit.py`](../../agents/memory/audit.py).

## Consolidation policy

- Max **20** entries per user
- **90-day** retention window
- Dedupe by `(category, normalized_text)`

## Evidence cycles

See [`evidence/approved-cycle.md`](evidence/approved-cycle.md) and [`evidence/rejected-cycle.md`](evidence/rejected-cycle.md).
