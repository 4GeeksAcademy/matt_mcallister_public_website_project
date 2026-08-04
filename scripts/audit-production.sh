#!/usr/bin/env bash
set -euo pipefail

projects=(
  "uis/website"
  "uis/backoffice"
  "uis/application"
  "uis/talent-pipeline-nextjs"
  "services/leads-api"
  "packages/trackflow-core"
)

for project in "${projects[@]}"; do
  echo "Auditing $project"
  npm --prefix "$project" audit --omit=dev --audit-level=high
done
