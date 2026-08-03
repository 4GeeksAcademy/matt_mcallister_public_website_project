# TrackFlow

TrackFlow is a milestone tracking and logistics operations platform. This
repository contains the public website, operations interfaces, backend
services, data pipelines, shared business logic, and RAG workflows.

`master` is the canonical integration branch.

## Canonical applications

Only the projects below are part of the supported runtime. Other historical
implementations are retained temporarily for migration and will be archived
after their unique behavior has been covered.

### User interfaces

| Application | Path | Local port |
| --- | --- | ---: |
| Public website | `uis/website` | 3000 |
| Operations backoffice | `uis/backoffice` | 3001 |
| Supplier directory | `uis/application` | 3002 |
| Talent pipeline | `uis/talent-pipeline-nextjs` | 3003 |

### APIs and infrastructure

| Service | Current path | Local port |
| --- | --- | ---: |
| Leads and executive snapshot API | `services/leads-api` | 4000 |
| Authentication API | `apps/trackflow-api` | 8000 |
| Incident analysis and RAG API | `services/incident-api` | 8001 |
| Supplier API | `services/supplier-api` | 8002 |
| Inventory API | `services/inventory-api` | 8003 |
| Talent API | `services/talent-api` | 8004 |
| Operations telemetry API | `services/main.py` | 8005 |
| PostgreSQL | Docker Compose | 5432 |
| Flower | Docker Compose | 5555 |
| Qdrant | Docker Compose | 6333 |
| Redis | Docker Compose | 6379 |

## Local configuration

Copy `.env.example` to `.env` and replace placeholder credentials. Frontends
use these public URLs:

```text
NEXT_PUBLIC_WEBSITE_API_URL=http://localhost:4000
NEXT_PUBLIC_AUTH_API_URL=http://localhost:8000
NEXT_PUBLIC_INCIDENTS_API_URL=http://localhost:8001
NEXT_PUBLIC_SUPPLIER_API_URL=http://localhost:8002
NEXT_PUBLIC_INVENTORY_API_URL=http://localhost:8003
NEXT_PUBLIC_TALENT_API_URL=http://localhost:8004/tracker/api/v1
NEXT_PUBLIC_OPERATIONS_API_URL=http://localhost:8005
```

Never commit `.env`, dependency folders, build output, local databases, cache
files, coverage data, or generated evaluation output.

## Development workflow

Each project currently owns its dependency lockfile and commands. Install and
run commands from the relevant project directory. The root validation command
and complete Docker Compose stack are being added as part of the consolidation
work.

Before opening a pull request:

1. Install from lockfiles.
2. Run Python and TypeScript tests.
3. Run ESLint and TypeScript checks.
4. Build all four canonical interfaces.
5. Validate Docker Compose and service health endpoints.
6. Confirm `git diff --check` and `git ls-files -u` are clean.

## Archive policy

Historical projects are not deleted until their unique routes, tests, or
business behavior have been migrated into a canonical project. Archived code
must not be included by Docker, CI, root scripts, or production deployments.
Generated artifacts and empty placeholders are removed rather than archived.

See `BRANCH_AUDIT.md` for the branch consolidation record and
`docs/architecture_proposal.md` for the original architecture discussion.
