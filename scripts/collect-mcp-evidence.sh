#!/usr/bin/env bash
# Collect evaluator-ready MCP evidence in Codespaces and write a markdown report.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${CODESPACE_NAME:-}" ]]; then
  echo "This script must run in GitHub Codespaces." >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required." >&2
  exit 1
fi

UV_BIN="${UV_BIN:-uv}"
if ! command -v "$UV_BIN" >/dev/null 2>&1; then
    echo "uv is required to run the evidence probe dependencies (PyJWT, requests)." >&2
    exit 1
fi

DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
PUBLIC_BASE="https://${CODESPACE_NAME}-8006.${DOMAIN}"
MCP_URL="${MCP_URL:-${PUBLIC_BASE}/mcp}"
MCP_URL="${MCP_URL%/}"

mkdir -p docs/incidents

# Ensure the port is public, then (re)start stack with public MCP resource URL.
gh codespace ports visibility 8006:public >/dev/null 2>&1 || true

export MCP_RESOURCE_URL="$MCP_URL"
export MCP_AUDIENCE="$MCP_URL"
export MCP_AUTH_TEST_MODE="${MCP_AUTH_TEST_MODE:-1}"
export MCP_OIDC_ISSUER="${MCP_OIDC_ISSUER:-https://test-issuer.local}"
export MCP_TEST_JWT_SECRET="${MCP_TEST_JWT_SECRET:-${SECRET_KEY:-local-development-secret-change-me}}"

bash scripts/compose-mcp-with-token.sh

REPORT="docs/incidents/mcp_submission_evidence.md"
TMP_JSON="$(mktemp)"

"$UV_BIN" run --no-project --with PyJWT --with requests python - "$MCP_URL" "$TMP_JSON" <<'PY'
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import jwt
import requests

mcp_url = sys.argv[1].rstrip("/")
out_path = sys.argv[2]
base = mcp_url[:-4] if mcp_url.endswith("/mcp") else mcp_url
host = urlparse(mcp_url).netloc

issuer = os.environ.get("MCP_OIDC_ISSUER", "https://test-issuer.local")
secret = os.environ.get(
    "MCP_TEST_JWT_SECRET",
    os.environ.get("SECRET_KEY", "local-development-secret-change-me"),
)
aud = mcp_url

headers_base = {
    "Accept": "application/json, text/event-stream",
    "Host": host,
}

def make_token(scopes: str) -> str:
    return jwt.encode(
        {
            "iss": issuer,
            "sub": "submission-evidence",
            "client_id": "codespaces-evidence-client",
            "scope": scopes,
            "aud": aud,
            "exp": int(time.time()) + 3600,
        },
        secret,
        algorithm="HS256",
    )

def parse_sse_payload(text: str) -> dict:
    match = re.search(r"data:\s*(\{.*\})", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def safe_resp_json(resp: requests.Response) -> dict:
    try:
        return resp.json()
    except Exception:
        return {
            "raw": (resp.text or "")[:800],
            "content_type": resp.headers.get("content-type", ""),
            "status": resp.status_code,
        }


def sse_content_text(payload: dict) -> str:
    content = (payload.get("result") or {}).get("content") or []
    if not content:
        return ""
    first = content[0] or {}
    return str(first.get("text") or "")


def safe_json_text(text: str) -> dict:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text[:800]}

def mcp_call(method: str, params: dict, token: str | None = None, req_id: int = 1):
    headers = dict(headers_base)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(
        mcp_url,
        json={"jsonrpc": "2.0", "id": req_id, "method": method, "params": params},
        headers=headers,
        timeout=30,
    )
    return resp

full_token = make_token("incidents:read incidents:write inventory:read")
read_only_token = make_token("incidents:read inventory:read")

results = {}
results["collector_errors"] = []

try:
    meta_resp = requests.get(
        f"{base}/.well-known/oauth-protected-resource/mcp",
        timeout=20,
    )
    results["metadata_status"] = meta_resp.status_code
    results["metadata_body"] = safe_resp_json(meta_resp)
except Exception as exc:
    results["metadata_status"] = 0
    results["metadata_body"] = {"error": str(exc)}
    results["collector_errors"].append(f"metadata: {exc}")

try:
    unauth = mcp_call("tools/list", {}, token=None, req_id=1)
    results["no_token_tools_list_status"] = unauth.status_code
    results["no_token_tools_list_prefix"] = (unauth.text or "")[:200]
except Exception as exc:
    results["no_token_tools_list_status"] = 0
    results["no_token_tools_list_prefix"] = f"error: {exc}"
    results["collector_errors"].append(f"tools/list unauth: {exc}")

tools = []
try:
    auth_list = mcp_call("tools/list", {}, token=full_token, req_id=2)
    auth_payload = parse_sse_payload(auth_list.text)
    tools = ((auth_payload.get("result") or {}).get("tools") or [])
    results["tools_list_status"] = auth_list.status_code
except Exception as exc:
    results["tools_list_status"] = 0
    results["collector_errors"].append(f"tools/list auth: {exc}")
results["tools_count"] = len(tools)
results["tool_names"] = sorted(t.get("name", "") for t in tools)
results["all_tools_have_description"] = all(bool(t.get("description")) for t in tools)
results["all_tools_have_schema"] = all("inputSchema" in t for t in tools)

forbidden_create = mcp_call(
    "tools/call",
    {
        "name": "incidents_create",
        "arguments": {
            "title": "Forbidden scope proof",
            "description": "Scope check evidence.",
            "category": "carrier_issue",
            "status": "open",
            "origin": "customer",
            "branch": "la_office",
        },
    },
    token=read_only_token,
    req_id=3,
)
forbidden_payload = parse_sse_payload(forbidden_create.text)
forbidden_text = sse_content_text(forbidden_payload)
results["forbidden_scope_status"] = forbidden_create.status_code
results["forbidden_scope_text"] = forbidden_text

create_resp = mcp_call(
    "tools/call",
    {
        "name": "incidents_create",
        "arguments": {
            "title": "Codespaces evidence incident",
            "description": "Created by evidence collection script.",
            "category": "carrier_issue",
            "status": "open",
            "origin": "customer",
            "branch": "la_office",
        },
    },
    token=full_token,
    req_id=4,
)
create_payload = parse_sse_payload(create_resp.text)
create_text = sse_content_text(create_payload)
create_json = safe_json_text(create_text)
incident_id = (((create_json.get("data") or {}).get("id")) if create_json.get("ok") else None)

get_resp = mcp_call(
    "tools/call",
    {"name": "incidents_get", "arguments": {"incident_id": incident_id}},
    token=full_token,
    req_id=5,
)
get_payload = parse_sse_payload(get_resp.text)
get_text = sse_content_text(get_payload)
get_json = safe_json_text(get_text)

update_resp = mcp_call(
    "tools/call",
    {
        "name": "incidents_update_status",
        "arguments": {"incident_id": incident_id, "status": "in_progress"},
    },
    token=full_token,
    req_id=6,
)
update_payload = parse_sse_payload(update_resp.text)
update_text = sse_content_text(update_payload)
update_json = safe_json_text(update_text)

inventory_list = mcp_call(
    "tools/call",
    {"name": "inventory_list_products", "arguments": {}},
    token=full_token,
    req_id=7,
)
inventory_list_payload = parse_sse_payload(inventory_list.text)
inventory_list_text = sse_content_text(inventory_list_payload)
inventory_list_json = safe_json_text(inventory_list_text)

inventory_write_blocked = mcp_call(
    "tools/call",
    {
        "name": "inventory_create_product",
        "arguments": {
            "name": "Blocked through MCP",
            "sku": "BLOCK-EVIDENCE-001",
            "warehouse_location": "los_angeles",
            "client_brand": "TrackFlow",
            "low_stock_threshold": 10,
        },
    },
    token=full_token,
    req_id=8,
)
inv_block_payload = parse_sse_payload(inventory_write_blocked.text)
inv_block_text = sse_content_text(inv_block_payload)
inv_block_json = safe_json_text(inv_block_text)

invalid_validation = mcp_call(
    "tools/call",
    {
        "name": "inventory_create_product",
        "arguments": {
            "name": "Bad validation",
            "sku": "BAD-EVIDENCE-001",
            "warehouse_location": "los_angeles",
            "client_brand": "TrackFlow",
            "low_stock_threshold": -1,
        },
    },
    token=full_token,
    req_id=9,
)
invalid_payload = parse_sse_payload(invalid_validation.text)
invalid_text = sse_content_text(invalid_payload)

results["public_mcp_url"] = mcp_url
results["incident_id"] = incident_id
results["incidents_create"] = create_json
results["incidents_get"] = get_json
results["incidents_update_status"] = update_json
results["inventory_list_products"] = inventory_list_json
results["inventory_create_product_blocked"] = inv_block_json
results["inventory_invalid_validation_text"] = invalid_text

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2, sort_keys=True)
PY

python3 - "$TMP_JSON" "$REPORT" <<'PY'
import json
import sys
from datetime import datetime, timezone

src = sys.argv[1]
report = sys.argv[2]

with open(src, "r", encoding="utf-8") as fh:
    data = json.load(fh)

def code_block(obj):
    return "```json\n" + json.dumps(obj, indent=2, sort_keys=True) + "\n```"

lines = []
lines.append("# MCP Submission Evidence (Codespaces Public URL)")
lines.append("")
lines.append(f"Generated at: {datetime.now(timezone.utc).isoformat()}")
lines.append("")
lines.append("## Environment")
lines.append(f"- Public MCP URL: {data.get('public_mcp_url')}")
lines.append("- Transport: MCP Streamable HTTP")
lines.append("- Auth mode used for executable evidence: MCP test mode bearer tokens")
lines.append("")
lines.append("## Criteria Evidence")
lines.append("1. MCP server discovery endpoint is reachable on public Codespaces URL.")
lines.append(code_block({"metadata_status": data.get("metadata_status"), "metadata_body": data.get("metadata_body")}))
lines.append("2. Unauthenticated client is blocked.")
lines.append(code_block({"no_token_tools_list_status": data.get("no_token_tools_list_status"), "no_token_tools_list_prefix": data.get("no_token_tools_list_prefix")}))
lines.append("3. Authenticated discovery lists tools with descriptions and schemas.")
lines.append(code_block({
    "tools_list_status": data.get("tools_list_status"),
    "tools_count": data.get("tools_count"),
    "tool_names": data.get("tool_names"),
    "all_tools_have_description": data.get("all_tools_have_description"),
    "all_tools_have_schema": data.get("all_tools_have_schema"),
}))
lines.append("4. Authorization errors are distinct (`MCP_FORBIDDEN_SCOPE`).")
lines.append(code_block({"forbidden_scope_status": data.get("forbidden_scope_status"), "forbidden_scope_text": data.get("forbidden_scope_text")}))
lines.append("5. Incident workflow via MCP: create -> get -> update status (`PATCH /api/incidents/{id}/status`).")
lines.append(code_block({
    "incident_id": data.get("incident_id"),
    "incidents_create": data.get("incidents_create"),
    "incidents_get": data.get("incidents_get"),
    "incidents_update_status": data.get("incidents_update_status"),
}))
lines.append("6. Inventory read works and write is explicitly blocked.")
lines.append(code_block({
    "inventory_list_products": data.get("inventory_list_products"),
    "inventory_create_product_blocked": data.get("inventory_create_product_blocked"),
}))
lines.append("7. Validation errors are distinct (`MCP_VALIDATION_ERROR`).")
lines.append(code_block({"inventory_invalid_validation_text": data.get("inventory_invalid_validation_text")}))
lines.append("")
lines.append("## Manual OAuth Playground Evidence (to attach)")
lines.append("- Screenshot of MCP Playground connected to the same public URL.")
lines.append("- Screenshot of OAuth completion against Logto/Auth0 (MCP_AUTH_TEST_MODE=0 environment).")
lines.append("- Screenshot or export showing the same tool executions in Playground.")

with open(report, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
PY

echo "Evidence report written to $REPORT"
