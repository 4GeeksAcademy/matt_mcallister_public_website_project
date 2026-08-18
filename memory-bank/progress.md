# Progress

## Current State
- Milestone 1: Corporate website created.
- Milestone 2: Business logic module implemented.
- Milestone 3: Initial repository structure established.

## Milestone 4 (agent harness + UIs)
- Memory bank, `AGENTS.md`, `.agents/development_rules.md`, and `skills/recurring_task_skill.md` in place.
- `uis/website`: corporate TrackFlow site (`npm run dev --webpack`).
- `uis/backoffice`: distinct layout with nav; Milestone 2 logic at `/operations-analysis`.
- Windows grader fix: Webpack + `distDir: "build"` documented in UI READMEs.

## Next Steps
- Continue later milestones (auth, inventory, RAG, agents) per course roadmap.

- 5/31/26 Milestone 4: verified "What We Will Evaluate" checklist (memory bank, agents, skills, both UIs, shared logic import).

- 7/29/26 Milestone 4 runtime fix: forced Webpack in both UI apps to avoid Turbopack MAX_PATH failures on Windows.

- 8/18/26 Milestone 4 resubmission: added `distDir: "build"`, UI README Windows grader notes, refreshed memory bank from `CONTEXT.md`.

-8/3/26 Repository consolidation: audited every remote branch and integrated all unique project lines into `master`. Removed tracked dependency folders, Python caches, a local database, and `.env.local`; expanded ignore rules; removed an empty Windows-incompatible filename; and separated the telemetry demo login from the primary authentication route. See `BRANCH_AUDIT.md` for the branch-by-branch record.

-7/31/26 Milestone 7 cleanup: excluded dependencies, Next.js build output, local databases, generated CSV results, and environment secrets from Git; made the RAG embedding vector size configurable and corrected local API CORS handling.

-8/3/26 Full remediation: established canonical UI and service boundaries, archived duplicate implementations, separated the incident, leads, and supplier APIs, repaired incident/inventory runtime failures, added the missing talent API, standardized ports and frontend API URLs, upgraded canonical Next.js apps to 16.3.0, removed production dependency vulnerabilities, and added root validation, complete Docker Compose definitions, and GitHub Actions CI.

-8/4/26 Context alignment: enforced runtime telemetry vocabulary and `packages/trackflow-core` as Milestone 2; aligned backoffice auth/inventory/supplier contracts; restored inventory telemetry emitters against inventory-api; returned RAG citations from `/knowledge/query` with UI sources; added `scripts/run_rag_eval.py` Recall@3 gate; fixed leads-api Docker packaging for trackflow-core; expanded Python validation to telemetry and KPI tests; refreshed memory bank and service docs to the logistics multi-service stack.
