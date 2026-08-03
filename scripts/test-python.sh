#!/usr/bin/env bash
set -euo pipefail

UV_BIN="${UV_BIN:-uv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$PWD/.uv-python}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"

if ! command -v "$UV_BIN" >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

export DATABASE_PATH="${DATABASE_PATH:-$(mktemp -t trackflow-auth.XXXXXX.json)}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export DATABASE_URL="${DATABASE_URL:-postgresql://trackflow:trackflow@localhost:5432/trackflow}"

PYTHONPATH=apps/trackflow-api \
  "$UV_BIN" run --python 3.11 --project apps/trackflow-api \
  python -m pytest apps/trackflow-api/tests

PYTHONPATH=services/supplier-api \
  "$UV_BIN" run --python 3.11 --project services/supplier-api --extra dev \
  python -m pytest services/supplier-api/tests

PYTHONPATH=services/incident-api \
  "$UV_BIN" run --no-project --python 3.11 \
  --with-requirements services/incident-api/requirements.txt \
  python -m pytest services/incident-api/tests tests/pipelines scripts/test_analyze_context.py

PYTHONPATH=services/inventory-api \
  "$UV_BIN" run --no-project --python 3.11 \
  --with-requirements services/inventory-api/requirements.txt \
  --with pytest --with httpx \
  python -m pytest services/inventory-api/tests

PYTHONPATH=services/talent-api \
  "$UV_BIN" run --no-project --python 3.11 \
  --with-requirements services/talent-api/requirements.txt \
  python -m pytest services/talent-api/tests

PYTHONPATH=services \
  "$UV_BIN" run --no-project --python 3.11 \
  --with-requirements services/requirements.txt \
  python -c "from main import app; assert any(getattr(route, 'path', None) == '/health' for route in app.routes)"
