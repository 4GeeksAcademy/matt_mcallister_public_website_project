# TrackFlow API (AUTH-01)

FastAPI service for JWT authentication and user route protection.

## Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Export environment variables:

```bash
export SECRET_KEY="replace-with-a-long-random-string"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
export DATABASE_PATH="trackflow_auth.json"
```

4. Start server:

```bash
uvicorn app.main:app --reload
```

5. Open docs at `http://127.0.0.1:8000/docs`.

## Test

```bash
pytest -q
```

## Notes

- Persistence uses TinyDB JSON storage.
- Default DB file is `trackflow_auth.json` (set by `DATABASE_PATH`).
