# TrackFlow talent API

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
```

The API persists candidates and notes in TinyDB. Override the local database
path with `TALENT_DB_PATH`. Its public routes are under `/tracker/api/v1`.

Run tests with:

```bash
PYTHONPATH=. pytest
```
