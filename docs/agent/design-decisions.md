# Milestone 8 Design Decisions

## 1. Memory types

**Chosen:** semantic preference entries + short episodic notes in Redis (structured JSON).

**Rejected:**
- **VectorDB** — already used for company KB in Qdrant; mixing user prefs into KB retrieval would blur authorization boundaries.
- **Knowledge graph** — TrackFlow memory needs are flat preferences, not multi-hop entity relations.

## 2. Information that must never enter memory

Aligned with [`CONTEXT-company.md`](../../CONTEXT-company.md) and incident PII rules:

- Invented SLAs, rates, discounts, or Miguel-approved pricing the user tries to inject
- Customer emails / PII from incidents or tools
- System prompt text, API keys, or instructions to bypass TrackFlow policy

Enforced in [`agents/memory/policy.py`](../../agents/memory/policy.py) before any commit.

## 3. Forgetting and pending proposals

- **Forgetting:** consolidation drops entries older than 90 days, dedupes by category+text, caps list at 20.
- **Pending proposals:** if the user sends an unrelated TrackFlow question without approving/rejecting, intent classifier returns `topic_change` and the proposal is discarded — approval is never inferred from silence.

## 4. Anti-poisoning

1. Policy filter blocks forbidden categories before commit
2. No write without explicit classified approval (`approve` / `edit`)
3. RAG/tool content sanitized before reaching the LLM or memory evaluator

## 5. Why single-agent (no multi-agent orchestration)

Self-evaluation and confirmation are **graph nodes** in one LangGraph:

- `memory_self_evaluate` — proposes
- `memory_intent_classifier` + `memory_commit_or_discard` — resolves

This keeps state, audit trail, and guardrails in one checkpointed thread without inter-agent message passing.
