# Evidence: RFP Part 1 through Part 3

## Fixtures (CONTEXT §4)

| Curriculum PDF | Text fixture | Expected outcome |
| --- | --- | --- |
| `CONTEXT-trackflow-request-1.pdf` (ModaViva) | `tests/fixtures/rfp/modaviva_rfp.txt` | Accept → `warehouse`, `reverse` (EUR) |
| `CONTEXT-trackflow-request-2.pdf` (Luna Cosmetics) | `tests/fixtures/rfp/luna_cosmetics_rfp.txt` | Accept → `warehouse`, `lastmile` (USD) |
| `CONTEXT-trackflow-request-3.pdf` (carrier pitch) | `tests/fixtures/rfp/carrier_pitch.txt` | Reject → `discarded` |

## Manual steps

1. Upload a fixture (or curriculum PDF) via backoffice `/rfp` or `POST /api/rfp/upload`
2. Poll `GET /api/rfp/{ticket_id}` — Part 1 ends at `intake_complete` or `discarded`
3. Full pipeline continues through drafting/evaluation to `waiting_for_approval`
4. Approve each active department via `POST /api/rfp/{ticket_id}/resume`
5. Fetch final document at `GET /api/rfp/{ticket_id}/document`

## Automated proof

- `tests/pipelines/test_rfp_intake.py` — classifier, scope routing, metadata
- `tests/pipelines/test_rfp_draft_eval.py` — generators, compliance §5, iteration limit
- `tests/pipelines/test_rfp_approval.py` — interrupt/resume, arbitration, parallel approval
- `tests/pipelines/test_rfp_e2e.py::test_rfp_lifecycle_part1_through_part3`
- `scripts/run_rfp_e2e.py`

```bash
PYTHONPATH=. RFP_STORE_BACKEND=memory RFP_RUN_SYNC=true python3 scripts/run_rfp_e2e.py
```
