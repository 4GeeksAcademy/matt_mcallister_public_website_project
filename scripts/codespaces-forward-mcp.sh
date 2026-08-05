#!/usr/bin/env bash
# Configure public MCP port 8006 in GitHub Codespaces for Playground evidence.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SETUP_ONLY=0
START_STACK=0
for arg in "$@"; do
  case "$arg" in
    --setup-only) SETUP_ONLY=1 ;;
    --start) START_STACK=1 ;;
  esac
done

if [[ -z "${CODESPACE_NAME:-}" ]]; then
  echo "This script must run inside GitHub Codespaces (CODESPACE_NAME is unset)." >&2
  echo "From your Codespace terminal:" >&2
  echo "  bash scripts/codespaces-forward-mcp.sh --start" >&2
  exit 1
fi

DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
PUBLIC_BASE="https://${CODESPACE_NAME}-8006.${DOMAIN}"
export MCP_RESOURCE_URL="${MCP_RESOURCE_URL:-${PUBLIC_BASE}/mcp}"
export MCP_AUDIENCE="${MCP_AUDIENCE:-$MCP_RESOURCE_URL}"

codespace_port_url() {
  if command -v gh >/dev/null 2>&1; then
    gh codespace ports --json browseUrl,sourcePort,visibility \
      -q '.[] | select(.sourcePort == 8006) | .browseUrl' 2>/dev/null || true
  fi
}

make_port_public() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not found; set port 8006 to Public in the Ports panel." >&2
    return 0
  fi
  if gh codespace ports visibility 8006:public 2>/dev/null; then
    echo "Port 8006 visibility set to public via gh CLI."
  else
    echo "Could not set visibility via gh (port may not be forwarded yet)." >&2
    echo "Open Ports → 8006 → Visibility → Public" >&2
  fi
}

print_playground_info() {
  local url
  url="$(codespace_port_url)"
  if [[ -z "$url" ]]; then
    url="${PUBLIC_BASE}/"
  fi
  local mcp_url="${url%/}/mcp"
  if [[ "$mcp_url" == */mcp/mcp ]]; then
    mcp_url="${PUBLIC_BASE}/mcp"
  fi

  cat <<EOF

============================================================
MCP Playground (Codespaces)
============================================================
  Public MCP URL:     ${mcp_url}
  OAuth metadata:     ${mcp_url%/mcp}/.well-known/oauth-protected-resource/mcp

  Export before Playground OAuth (production mode):
    export MCP_RESOURCE_URL='${mcp_url}'
    export MCP_AUDIENCE='${mcp_url}'
    export MCP_AUTH_TEST_MODE=0

  Playground checklist:
    1. Connect to ${mcp_url}
    2. Complete OAuth (Logto/Auth0)
    3. incidents_create → incidents_get → incidents_update_status
    4. inventory_list_products
    5. inventory_create_product (expect INVENTORY_WRITE_FORBIDDEN)
============================================================
EOF
}

if [[ "$SETUP_ONLY" -eq 1 ]]; then
  print_playground_info
  exit 0
fi

if [[ "$START_STACK" -eq 1 ]]; then
  if command -v docker >/dev/null 2>&1 && [[ -f docker-compose.yml ]]; then
    echo "Starting incident-api, inventory-api, company-tools-mcp via docker compose ..."
    docker compose up -d incident-api inventory-api company-tools-mcp
    echo "Waiting for MCP health ..."
    for _ in $(seq 1 30); do
      if curl -sf "http://127.0.0.1:8006/.well-known/oauth-protected-resource/mcp" >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done
  else
    echo "Docker not available; starting local stack (binds 0.0.0.0 in Codespaces) ..."
    exec bash "$ROOT/scripts/run-mcp-manual-test.sh"
  fi
fi

make_port_public
sleep 1
print_playground_info
