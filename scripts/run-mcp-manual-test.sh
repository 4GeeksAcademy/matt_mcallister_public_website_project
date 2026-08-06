#!/usr/bin/env bash
# Start incident-api, inventory-api, and MCP company-tools for local manual testing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Codespaces port forwarding requires listening on all interfaces.
BIND_HOST="127.0.0.1"
if [[ -n "${CODESPACE_NAME:-}" || "${CODESPACES:-}" == "true" ]]; then
  BIND_HOST="0.0.0.0"
  DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
  export MCP_RESOURCE_URL="${MCP_RESOURCE_URL:-https://${CODESPACE_NAME}-8006.${DOMAIN}/mcp}"
  export MCP_AUDIENCE="${MCP_AUDIENCE:-$MCP_RESOURCE_URL}"
  export MCP_SERVER_URL="${MCP_SERVER_URL:-$MCP_RESOURCE_URL}"
fi

PY="${ROOT}/.venv-mcp/bin/python"
UVICORN="${ROOT}/.venv-mcp/bin/uvicorn"
if [[ ! -x "$PY" ]]; then
  echo "Missing .venv-mcp. Create it first:" >&2
  echo "  python3 -m venv .venv-mcp && .venv-mcp/bin/pip install -r mcps/company_tools/requirements.txt ..." >&2
  exit 1
fi

export POSTGRES_DATABASE_URL="${POSTGRES_DATABASE_URL:-postgresql://trackflow:trackflow@localhost:5432/trackflow}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export DATABASE_URL="${DATABASE_URL:-$POSTGRES_DATABASE_URL}"
export UPLOAD_DIR="${UPLOAD_DIR:-/tmp/trackflow_uploads}"
export INCIDENTS_DB_PATH="${INCIDENTS_DB_PATH:-$ROOT/data/manual-test/incidents.db}"
export SECRET_KEY="${SECRET_KEY:-local-development-secret-change-me}"
export MCP_AUTH_TEST_MODE=1
export MCP_OIDC_ISSUER="${MCP_OIDC_ISSUER:-https://test-issuer.local}"
export MCP_RESOURCE_URL="${MCP_RESOURCE_URL:-http://localhost:8006/mcp}"
export MCP_AUDIENCE="${MCP_AUDIENCE:-http://localhost:8006/mcp}"
export MCP_TEST_JWT_SECRET="${MCP_TEST_JWT_SECRET:-$SECRET_KEY}"
export INCIDENTS_API_URL="${INCIDENTS_API_URL:-http://localhost:8001}"
export INVENTORY_API_URL="${INVENTORY_API_URL:-http://localhost:8003}"
export MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8006/mcp}"

export INVENTORY_DATABASE_URL="${INVENTORY_DATABASE_URL:-sqlite:///$ROOT/data/manual-test/inventory.db}"
export TINYDB_PATH="${TINYDB_PATH:-$ROOT/data/manual-test/inventory-auth.json}"

mkdir -p "$ROOT/data/manual-test" "$UPLOAD_DIR"

echo "Starting inventory-api on :8003 ..."
(
  cd "$ROOT/services/inventory-api"
  PYTHONPATH="$ROOT/services/inventory-api" \
    DATABASE_URL="$INVENTORY_DATABASE_URL" \
    TINYDB_PATH="$TINYDB_PATH" \
    SECRET_KEY="$SECRET_KEY" \
    "$UVICORN" app.main:app --host "$BIND_HOST" --port 8003
) &
INV_PID=$!

sleep 3

echo "Creating inventory service token ..."
INV_JSON="$(curl -sf -X POST http://127.0.0.1:8003/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"MCP Service","email":"mcp-service@example.com","password":"password123"}' || true)"
if [[ -z "$INV_JSON" || "$INV_JSON" != *'"token"'* ]]; then
  INV_JSON="$(curl -sf -X POST http://127.0.0.1:8003/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"mcp-service@example.com","password":"password123"}')"
fi
INV_TOKEN="$("$PY" -c 'import sys,json; print(json.loads(sys.argv[1])["token"])' "$INV_JSON")"
export INVENTORY_SERVICE_TOKEN="$INV_TOKEN"

echo "Starting incident-api on :8001 ..."
(
  cd "$ROOT/services/incident-api"
  PYTHONPATH="$ROOT/services/incident-api:$ROOT" \
    REDIS_URL="$REDIS_URL" \
    DATABASE_URL="$POSTGRES_DATABASE_URL" \
    INCIDENTS_DB_PATH="$INCIDENTS_DB_PATH" \
    UPLOAD_DIR="$UPLOAD_DIR" \
    "$UVICORN" app.main:app --host "$BIND_HOST" --port 8001
) &
INC_PID=$!

sleep 2

echo "Starting MCP company-tools on :8006 ..."
(
  cd "$ROOT"
  PYTHONPATH="$ROOT" \
    MCP_AUTH_TEST_MODE=1 \
    MCP_OIDC_ISSUER="$MCP_OIDC_ISSUER" \
    MCP_RESOURCE_URL="$MCP_RESOURCE_URL" \
    MCP_AUDIENCE="$MCP_AUDIENCE" \
    MCP_TEST_JWT_SECRET="$MCP_TEST_JWT_SECRET" \
    INCIDENTS_API_URL="$INCIDENTS_API_URL" \
    INVENTORY_API_URL="$INVENTORY_API_URL" \
    INVENTORY_SERVICE_TOKEN="$INVENTORY_SERVICE_TOKEN" \
    "$UVICORN" mcps.company_tools.server:app --host "$BIND_HOST" --port 8006
) &
MCP_PID=$!

sleep 2

MCP_TOKEN="$(
  MCP_AUTH_TEST_MODE=1 MCP_OIDC_ISSUER="$MCP_OIDC_ISSUER" MCP_AUDIENCE="$MCP_AUDIENCE" \
  MCP_TEST_JWT_SECRET="$MCP_TEST_JWT_SECRET" "$PY" - <<'PY'
import os, time, jwt
secret = os.environ["MCP_TEST_JWT_SECRET"]
issuer = os.environ["MCP_OIDC_ISSUER"]
audience = os.environ["MCP_AUDIENCE"]
print(jwt.encode({
    "iss": issuer,
    "sub": "manual-test-user",
    "client_id": "mcp-playground",
    "scope": "incidents:read incidents:write inventory:read",
    "aud": audience,
    "exp": int(time.time()) + 86400,
}, secret, algorithm="HS256"))
PY
)"

if [[ -n "${CODESPACE_NAME:-}" ]]; then
  echo ""
  echo "Codespaces: run in another terminal to publish port 8006:"
  echo "  bash scripts/codespaces-forward-mcp.sh"
  echo ""
fi

cat <<EOF

============================================================
Manual MCP test stack is running
============================================================
  incident-api     http://${BIND_HOST}:8001/health
  inventory-api    http://${BIND_HOST}:8003/health
  MCP server       ${MCP_SERVER_URL}
  OAuth metadata   ${MCP_SERVER_URL%/mcp}/.well-known/oauth-protected-resource/mcp

MCP Bearer token (test mode, 24h):
  $MCP_TOKEN

Quick checks:
  curl -s http://127.0.0.1:8006/.well-known/oauth-protected-resource/mcp | python3 -m json.tool
  curl -s http://127.0.0.1:8001/api/incidents | python3 -m json.tool

Agent endpoint (needs MCP_AGENT_ACCESS_TOKEN):
  export MCP_AGENT_ACCESS_TOKEN='$MCP_TOKEN'
  export MCP_SERVER_URL=http://127.0.0.1:8006/mcp
  curl -s -X POST http://127.0.0.1:8001/agent/query \\
    -H 'Content-Type: application/json' \\
    -d '{"question":"What is the status of incident inc_..."}'

Press Ctrl+C to stop all services.
PIDs: inventory=$INV_PID incident=$INC_PID mcp=$MCP_PID
============================================================
EOF

trap 'kill $INV_PID $INC_PID $MCP_PID 2>/dev/null; exit 0' INT TERM
wait
