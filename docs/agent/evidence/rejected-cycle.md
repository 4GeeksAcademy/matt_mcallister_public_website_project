# Evidence: Rejected Memory Cycle

## Steps

1. **User:** `For future calls, prefer LA office.`
2. **Agent:** proposes remembering the preference.
3. **User:** `reject`
4. **Agent:** logs rejection; memory store remains empty.

## Alternate discard path

1. After a proposal, user asks unrelated question: `What is the TrackFlow return policy?`
2. Intent classified as `topic_change` → proposal discarded without commit.

## Automated proof

- `tests/pipelines/test_agent_memory.py::test_rejected_memory_cycle_leaves_store_empty`
- `tests/pipelines/test_agent_memory.py::test_topic_change_discards_pending_proposal_by_default`

## Expected audit log outcomes

- `proposed`
- `rejected` or `topic_change` discard via `memory_commit_or_discard`
