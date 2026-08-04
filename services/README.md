# TrackFlow services

Canonical backend services use separate directories and ports:

- `leads-api` — Express leads and executive snapshots on port 4000
  (imports `packages/trackflow-core`).
- `../apps/trackflow-api` — FastAPI authentication on port 8000.
- `incident-api` — FastAPI incident manager, CSV analysis, and RAG on port 8001.
- `supplier-api` — FastAPI supplier directory on port 8002.
- `inventory-api` — FastAPI products and inbound/outbound orders on port 8003.
- `talent-api` — FastAPI candidate and notes API on port 8004.
- `main.py` (operations API) — telemetry ingest/report, inventory stub helpers,
  and weekly reporting endpoints on port 8005.
- `celery_app` — incident background jobs backed by Redis.

Each service owns its manifest, tests, README, and `/health` endpoint. Use the
root Docker Compose stack for integrated development.
