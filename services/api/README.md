# TrackFlow Incident Analysis API

## Run

```bash
cd services/api
pip install -r requirements.txt
PYTHONPATH=../..:../.. uvicorn app.main:app --app-dir . --reload --port 8001
```

From the repo root:

```bash
PYTHONPATH=. uvicorn app.main:app --app-dir services/api --reload --port 8001
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/incidents/analyze` | Upload CSV (`multipart/form-data`, field `file`) → JSON summary; stores last result |
| `GET` | `/api/incidents/results/export` | Download last analysis as `results.csv` |

Shared validation/metrics live in `scripts/stats.py` and `scripts/export.py` (same logic as `scripts/analyze.py`).
