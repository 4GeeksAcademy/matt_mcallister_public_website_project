# Evidence: Approved Memory Cycle

## Steps

1. **User:** `For future inventory questions, prefer Zaragoza warehouse.`
2. **Agent:** answers KB question + proposes memory in the same response.
3. **User:** `approve`
4. **Agent:** commits memory; continues normally on next question.

## Automated proof

`tests/pipelines/test_agent_memory.py::test_approved_memory_cycle_is_reflected_later`

## Expected audit log outcomes

- `proposed`
- `approved`

Committed entry example:

```json
{
  "category": "preference",
  "text": "Prefers Zaragoza warehouse for inventory questions."
}
```
