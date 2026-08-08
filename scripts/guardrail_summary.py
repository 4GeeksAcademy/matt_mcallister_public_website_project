#!/usr/bin/env bash
# Print in-process guardrail trigger summary for manual test sessions.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHONPATH=. python3 - <<'PY'
from agents.guardrails.observability import get_guardrail_summary
import json

print(json.dumps(get_guardrail_summary(), indent=2))
PY
