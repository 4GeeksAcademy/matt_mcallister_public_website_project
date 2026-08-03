# TrackFlow incident analysis and RAG API

Run from the repository root:

```bash
pip install -r services/incident-api/requirements.txt
REDIS_URL=redis://localhost:6379/0 \
DATABASE_URL=postgresql://trackflow:trackflow@localhost:5432/trackflow \
PYTHONPATH=. \
uvicorn app.main:app --app-dir services/incident-api --reload --port 8001
```

The service exposes `/health`, incident CSV analysis/export routes, background
job routes, and `/knowledge/query`.
