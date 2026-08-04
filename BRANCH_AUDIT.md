# Branch Consolidation Audit

Date: 2026-08-03

This audit compares every remote branch with `main` as it existed before consolidation. The new `master` branch preserves every unique branch history while producing one clean working tree. Existing remote branches remain unchanged.

## Consolidation policy

- Branches were integrated in project chronology so later implementations resolve overlapping files.
- A branch already contained by a later branch was not merged a second time, but remains in `master` history through that descendant.
- Generated dependencies, build/cache files, a local SQLite database, and `.env.local` were removed from the final tree. Source manifests and lockfiles were retained.
- The empty file `CONTEXT — Background Processing: Async Task Queue with Redis and Celery.md` was removed because its colon prevents Windows checkouts.
- The telemetry demo login was moved to `/telemetry/login`; the primary authentication page remains `/login`. This avoids a duplicate Next.js route created by combining two project branches.

## Branch inventory

`Behind` and `Ahead` are commit counts relative to the pre-consolidation `main` branch.

| Branch | Behind | Ahead | Consolidation result |
|---|---:|---:|---|
| `authentication_flows_in_the_frontend` | 3 | 3 | Included through `milestone_5_backoffice_inventory_interface` |
| `backend_architecture_getmystatsup` | 6 | 1 | Merged; adds the architecture proposal |
| `background_processing` | 3 | 1 | Merged; adds job runner and nightly export work |
| `bullet_proof_apps` | 3 | 2 | Merged; includes `securing_api` and its follow-up hardening |
| `centralized_incident_manager` | 3 | 2 | Merged; adds incident management API/UI work |
| `company_incident_file` | 4 | 4 | Merged; adds incident analyzer, API/UI, and evidence |
| `data_pipeline_full_plan` | 3 | 3 | Merged; includes `telemetry_full_plan` and pipeline implementation |
| `error_handling` | 3 | 2 | Merged; includes `test` and error-handling work |
| `feature/dockerize-monorepo` | 3 | 1 | Merged; adds container configuration |
| `main` | 0 | 0 | Fully included; used as the current project baseline |
| `message_queue_async_tasks` | 2 | 0 | Already contained in `main` |
| `milestone-2` | 6 | 4 | Merged; generated `node_modules` content removed from final tree |
| `milestone-3` | 6 | 1 | Merged; tracked `.env.local` removed from final tree |
| `milestone-4` | 4 | 0 | Already contained in `main` and most later branches |
| `milestone-5-orm-dual` | 3 | 4 | Included through `milestone_5_backoffice_inventory_interface` |
| `milestone-_6_data_pipeline` | 3 | 1 | Same commit as `milestone_6_data_pipeline` |
| `milestone_5_backoffice_inventory_interface` | 3 | 5 | Merged; includes authentication, ORM, and inventory UI/API work |
| `milestone_6_data_pipeline` | 3 | 1 | Merged; duplicate alias also covered |
| `milestone_7_rag` | 0 | 3 | Merged last; includes the current baseline plus RAG work |
| `password_reset_flow` | 3 | 2 | Merged; adds reset UI and supporting logic |
| `securing_api` | 3 | 1 | Included through `bullet_proof_apps` |
| `supplier_directory` | 3 | 5 | Merged; adds supplier API, tests, and UI |
| `support_agent_langraph_p1` | 0 | 0 | Same commit as pre-consolidation `main` |
| `telemetry_full_plan` | 3 | 1 | Included through `data_pipeline_full_plan` |
| `telemetry_plan_design` | 3 | 1 | Merged; adds telemetry design artifacts |
| `test` | 3 | 1 | Included through `error_handling` |

## Notable audit findings

1. Most feature branches diverged from commit `54a2ce8` and were three commits behind `main`; the student repeatedly branched from the same stale milestone base.
2. `milestone-2` tracked about 8,700 changed files, overwhelmingly dependency folders. `error_handling` similarly tracked a full `services/api/node_modules` tree.
3. Several Python branches tracked `__pycache__` and `.pyc` files. The inventory branch tracked a local SQLite database.
4. `milestone-3` tracked `.env.local`. Its value was a public API URL rather than a credential, but local environment files should still remain untracked.
5. No live credential was found in the consolidated working tree. Values in `.env.example` and documentation are placeholders or local development defaults.
6. Two backoffice branches independently defined `/login`. The authentication flow keeps `/login`; the telemetry demonstration now uses `/telemetry/login`.

## Future branch workflow

Before starting each project branch:

```text
git switch main
git pull --ff-only
git switch -c <new-project-branch>
```

After review, merge the project branch into `main` before creating the next one. Keep dependency folders, local environments, caches, databases, and secrets out of Git.
