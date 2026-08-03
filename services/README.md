# TrackFlow services

Canonical backend services use separate directories and ports:

- `leads-api` — Express leads and executive snapshots on port 4000.
- `incident-api` — FastAPI incident analysis and RAG on port 8001.
- `supplier-api` — FastAPI supplier directory on port 8002.
- `inventory-api` — FastAPI inventory and reporting on port 8003.
- `talent-api` — FastAPI candidate and notes API on port 8004.
- `celery_app` — incident background jobs backed by Redis.

Each service owns its manifest, tests, README, and `/health` endpoint. Use the
root Docker Compose stack for integrated development.
