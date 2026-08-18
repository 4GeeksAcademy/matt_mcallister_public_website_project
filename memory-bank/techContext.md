# Technical Context

## Tech Stack (Milestone 4 baseline + monorepo evolution)
- **Public UI**: Next.js App Router, TypeScript, React, Tailwind — [`uis/website`](uis/website)
- **Backoffice UI**: Next.js App Router with its own layout/nav — [`uis/backoffice`](uis/backoffice)
- **Shared business logic**: [`packages/trackflow-core`](packages/trackflow-core) (canonical Milestone 2; imported by backoffice, not copied)
- **Later services** (same monorepo): FastAPI microservices, Celery/Redis, PostgreSQL pipelines, Qdrant RAG — see `services/` and `data/pipelines/`

## Milestone 4 layout
| Path | Purpose |
| --- | --- |
| `uis/website` | Corporate marketing site; `/` renders full TrackFlow website in TS components |
| `uis/backoffice` | Internal ops UI; `/operations-analysis` shows Milestone 2 output from `trackflow-core` |
| `packages/trackflow-core` | Single source of business rules (inventory, carriers, shipments) |
| `memory-bank/` | Persistent agent context (business + technical) |
| `AGENTS.md` | Mandatory pre-commit workflow for agents |
| `.agents/` | Scoped development rules |
| `skills/` | Reusable agent skills with acceptance criteria |

## Architectural Decisions
- Monorepo: UIs under `uis/`, APIs under `services/`, pipelines under `data/pipelines/`.
- **No duplicated business logic** in UI apps — import from `packages/trackflow-core`.
- Next.js dev/build uses **Webpack** (`--webpack` scripts) and `distDir: "build"` to avoid Windows Turbopack MAX_PATH failures for graders.
- Memory bank and `AGENTS.md` are restricted; edit only with explicit developer confirmation.

## Technical Constraints
- Align features with [`CONTEXT.md`](CONTEXT.md) before implementation.
- Do not commit `node_modules/`, `build/`, `.next/`, secrets, or local databases.
- Each runnable app must start with documented commands (`npm run dev` in each UI folder).
