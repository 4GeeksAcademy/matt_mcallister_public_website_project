## `seed_incidents.py`

Helper scripts for the monorepo.

## Incident analysis (TrackFlow)

Shared validation and metrics (used by the CLI and `services/incident-api`):

- `stats.py` — validate rows + aggregate metrics
- `export.py` — write one-row-per-metric CSV
- `analyze.py` — CLI report + optional `results.csv` export

```bash
# from repo root
python scripts/analyze.py data/raw/incidents-trackflow.csv

# or from scripts/
cd scripts
python analyze.py ../data/raw/incidents-trackflow.csv
```

Expected CONTEXT values for `incidents-trackflow.csv` are documented in
`incident_file_analyzer/incident_analyzer_context.md`.

```bash
python -m pytest scripts/test_analyze_context.py -q
```

- Applies analyzer invalid-row rules, then CONTEXT transforms
- Forces `origin` to `customer`
- Maps `country` → `la_office` / `zaragoza_office`
- Idempotent on `incident_id`

## RAG evaluation

```bash
# CI path: in-memory Qdrant + deterministic embedder (gates Recall@3 >= 80%)
PYTHONPATH=. python scripts/run_rag_eval.py --local-index

# Optional stub retriever (no indexing)
python scripts/run_rag_eval.py --mock

# Live OpenAI + Qdrant index (requires OPENAI_API_KEY and Qdrant)
python scripts/run_rag_eval.py
```
