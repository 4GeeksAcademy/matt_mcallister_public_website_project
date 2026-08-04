# Technical Context

## Tech Stack
- **Frontend**: Next.js (App Router), TypeScript, React, Tailwind CSS
- **Backend**: FastAPI (Python) microservices; Express leads API (Node.js)
- **Shared logic**: `packages/trackflow-core` (canonical Milestone 2)
- **Persistence**: TinyDB (auth/supplier/talent), SQLite/SQLModel (inventory),
  PostgreSQL (telemetry/jobs/pipelines), Qdrant (RAG)
- **Orchestration**: Docker Compose, Prefect (weekly warehouse ETL), Celery/Redis
- **Validation**: Root `npm run validate` (git integrity, lint, TS/Python tests,
  production builds, dependency audits)

## Architectural Decisions
- Monorepo with four canonical UIs and distinct service ports (see README).
- Runtime telemetry vocabulary (`warehouse`, `client_id`, `user_login_*`) is
  authoritative across schema, shared types, emitters, and pipelines.
- `packages/trackflow-core` is the only Milestone 2 business-logic module.
- Historical apps live under `archive/` and are excluded from Docker/CI.

## Technical Constraints
- Align contracts with context documents before adding features.
- Keep each service independently runnable with health endpoints.
- Do not commit secrets, dependency folders, build output, or local databases.
- Memory-bank and AGENTS.md require explicit confirmation before edits.
