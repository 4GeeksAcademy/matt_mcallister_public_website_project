#!/usr/bin/env bash
# Start inventory/incident APIs, provision INVENTORY_SERVICE_TOKEN, then start company-tools-mcp.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE_BUILD="${COMPOSE_BUILD:-1}"
COMPOSE_FLAGS="-d"
if [[ "$COMPOSE_BUILD" == "1" ]]; then
  COMPOSE_FLAGS="-d --build"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required." >&2
  exit 1
fi

echo "Starting incident-api and inventory-api..."
docker compose up $COMPOSE_FLAGS incident-api inventory-api

echo "Waiting for inventory-api health on http://127.0.0.1:8003/health ..."
for _ in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8003/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sf http://127.0.0.1:8003/health >/dev/null 2>&1; then
  echo "inventory-api is not healthy after waiting." >&2
  exit 1
fi

echo "Provisioning inventory service token..."
REGISTER_PAYLOAD='{"name":"MCP Service","email":"mcp-service@example.com","password":"password123"}'
LOGIN_PAYLOAD='{"email":"mcp-service@example.com","password":"password123"}'

TOKEN_JSON="$(curl -sf -X POST http://127.0.0.1:8003/auth/register \
  -H 'Content-Type: application/json' \
  -d "$REGISTER_PAYLOAD" || true)"

if [[ -z "$TOKEN_JSON" || "$TOKEN_JSON" != *'"token"'* ]]; then
  TOKEN_JSON="$(curl -sf -X POST http://127.0.0.1:8003/auth/login \
    -H 'Content-Type: application/json' \
    -d "$LOGIN_PAYLOAD")"
fi

INVENTORY_SERVICE_TOKEN="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["token"])' "$TOKEN_JSON")"

if [[ -z "$INVENTORY_SERVICE_TOKEN" ]]; then
  echo "Unable to extract INVENTORY_SERVICE_TOKEN." >&2
  exit 1
fi

echo "Starting company-tools-mcp with provisioned token..."
INVENTORY_SERVICE_TOKEN="$INVENTORY_SERVICE_TOKEN" docker compose up $COMPOSE_FLAGS company-tools-mcp

echo "Done. MCP metadata endpoint:"
echo "  http://127.0.0.1:8006/.well-known/oauth-protected-resource/mcp"
echo ""
echo "Token summary:"
echo "  INVENTORY_SERVICE_TOKEN is set for this compose start command only."
echo ""
echo "Next:"
echo "  bash scripts/codespaces-forward-mcp.sh --start   # in Codespaces"
