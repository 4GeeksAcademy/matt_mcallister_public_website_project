# TrackFlow Company Tools MCP Server

OAuth-protected MCP resource server exposing TrackFlow incident and inventory tools.

## Tools

| Tool | Scope | Backend |
|------|-------|---------|
| `incidents_create` | `incidents:write` | `POST /api/incidents` |
| `incidents_get` | `incidents:read` | `GET /api/incidents/{id}` |
| `incidents_list` | `incidents:read` | `GET /api/incidents` |
| `incidents_update_status` | `incidents:write` | `PATCH /api/incidents/{id}/status` |
| `inventory_list_products` | `inventory:read` | `GET /inventory/products` |
| `inventory_create_product` | `inventory:read` | Always rejected (`INVENTORY_WRITE_FORBIDDEN`) |

Status changes **must** use `incidents_update_status`, which calls the dedicated lifecycle endpoint `PATCH /api/incidents/{id}/status`.

## Authentication

This server uses **[MCP Auth](https://mcpauth.dev)** (`mcpauth`) as a resource server. It does **not** use FastMCP built-in OAuth.

- Protected Resource Metadata (RFC 9728): `GET /.well-known/oauth-protected-resource/mcp`
- All MCP `tools/list` and `tools/call` requests require `Authorization: Bearer <access_token>`
- Configure a course OIDC provider (Logto, Auth0, etc.) via env vars

### Required env vars (production)

```bash
MCP_RESOURCE_URL=https://<codespaces-host>-8006.app.github.dev/mcp
MCP_OIDC_ISSUER=https://<tenant>.logto.app/oidc
MCP_JWKS_URI=https://<tenant>.logto.app/oidc/jwks
MCP_AUDIENCE=<same as MCP_RESOURCE_URL>
MCP_AUTH_TEST_MODE=0
INVENTORY_SERVICE_TOKEN=<inventory-api JWT>
```

### Local / CI test mode

Set `MCP_AUTH_TEST_MODE=1` and sign HS256 tokens with `MCP_TEST_JWT_SECRET` (defaults to `SECRET_KEY`).

## Run locally

```bash
export PYTHONPATH=.
export MCP_AUTH_TEST_MODE=1
export INCIDENTS_API_URL=http://localhost:8001
export INVENTORY_API_URL=http://localhost:8003
export INVENTORY_SERVICE_TOKEN=<token from inventory-api /auth/register>

uvicorn mcps.company_tools.server:app --host 0.0.0.0 --port 8006
```

Or via Docker Compose:

```bash
docker compose up company-tools-mcp incident-api inventory-api
```

## MCP Playground (Codespaces)

### One-command setup (inside your Codespace)

```bash
# Start APIs + MCP, then publish port 8006 publicly
bash scripts/codespaces-forward-mcp.sh --start
```

Or with Docker Compose already running:

```bash
docker compose up -d incident-api inventory-api company-tools-mcp
bash scripts/codespaces-forward-mcp.sh
```

The script prints your public MCP URL and sets port **8006** to **Public** via `gh` (or tells you to use the Ports panel).

`.devcontainer/devcontainer.json` auto-forwards port **8006** as **public** when you reopen the Codespace after pulling this branch.

### Manual (Ports panel)

1. Start the stack in GitHub Codespaces (`docker compose up` or `scripts/run-mcp-manual-test.sh`).
2. Open **Ports** → find **8006** → set **Visibility** to **Public**.
3. Copy the forwarded URL (e.g. `https://<codespace-name>-8006.app.github.dev`).
4. Set `MCP_RESOURCE_URL` to that URL with `/mcp` appended (not localhost).
5. Connect MCP Playground and complete OAuth against your Logto/Auth0 app.
6. Execute one workflow per tool:
   - `incidents_create` → `incidents_get` → `incidents_update_status`
   - `inventory_list_products`
   - `inventory_create_product` (must fail with `INVENTORY_WRITE_FORBIDDEN`)

### Inventory write rejection (document for evaluators)

Calling `inventory_create_product` returns:

```json
{
  "ok": false,
  "error_code": "INVENTORY_WRITE_FORBIDDEN",
  "message": "Inventory write operations are not permitted through MCP. Use the inventory backoffice for product changes."
}
```

The MCP server rejects the write **before** contacting inventory-api.

## Error codes

| Code | Meaning |
|------|---------|
| `MCP_AUTH_REQUIRED` | Missing or invalid Bearer token |
| `MCP_FORBIDDEN_SCOPE` | Token lacks required scopes |
| `MCP_VALIDATION_ERROR` | Invalid tool input |
| `INCIDENT_NOT_FOUND` | Unknown incident id |
| `INCIDENT_STATUS_TRANSITION_INVALID` | Illegal status transition |
| `INVENTORY_WRITE_FORBIDDEN` | Inventory write blocked by design |
| `BACKEND_UNAVAILABLE` | Upstream API timeout or HTTP error |

## Logging

Every tool invocation emits a structured log line:

```json
{"event":"mcp_tool_invocation","client_id":"my-client","tool":"incidents_get","success":true,"error_code":null}
```

## Agent integration

The LangGraph support agent loads MCP tools through `langchain-mcp-adapters` (`agents/mcp/client.py`) and routes ticket questions via `mcp_ticket_lookup_node`. Set:

```bash
MCP_SERVER_URL=http://company-tools-mcp:8006/mcp
MCP_AGENT_ACCESS_TOKEN=<oauth access token with incidents:read>
```
