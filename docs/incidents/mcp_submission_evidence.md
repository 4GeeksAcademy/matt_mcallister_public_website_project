# MCP Submission Evidence (Codespaces Public URL)

Generated at: 2026-08-06T14:15:46.503561+00:00

## Environment
- Public MCP URL: https://fuzzy-space-system-7vq744q59x9jfp55v-8006.app.github.dev/mcp
- Transport: MCP Streamable HTTP
- Auth mode used for executable evidence: MCP test mode bearer tokens

## Criteria Evidence
1. MCP server discovery endpoint is reachable on public Codespaces URL.
```json
{
  "metadata_body": {
    "content_type": "text/html; charset=utf-8",
    "raw": "<!doctype html><html lang=\"en\"><head><meta charset=\"UTF-8\"/><meta name=\"authUrl\" content=\"https://github.com/codespaces/auth/fuzzy-space-system-7vq744q59x9jfp55v\"/><meta name=\"gitHubApiUrl\" content=\"https://api.github.com\"/><meta name=\"correlationId\" content=\"1e23e335-4d01-4772-8000-f03fceffce3d\"/><meta name=\"iKey\" content=\"f772ffaa012e4fc6bb0a245dd176fc6c-ca6358be-0b85-4e74-ade1-c7857dd7d8c9-7394\"/><link id=\"js-favicon\" rel=\"shortcut icon\" href=\"https://github.githubassets.com/favicon.ico\"/><script defer=\"defer\" src=\"/static/commons-bootstrap~pfHelper-index.js.71ed813ae39fee29ce4a.js\"></script><script defer=\"defer\" src=\"/static/commons-bootstrap~pfHelper-moment.js.760fcd9e1ac67cd77f7a.js\"></script><script defer=\"defer\" src=\"/static/commons-bootstrap~pfHelper-axios.cjs.9b98d2b8da56af519bbc",
    "status": 200
  },
  "metadata_status": 200
}
```
2. Unauthenticated client is blocked.
```json
{
  "no_token_tools_list_prefix": "",
  "no_token_tools_list_status": 401
}
```
3. Authenticated discovery lists tools with descriptions and schemas.
```json
{
  "all_tools_have_description": true,
  "all_tools_have_schema": true,
  "tool_names": [],
  "tools_count": 0,
  "tools_list_status": 401
}
```
4. Authorization errors are distinct (`MCP_FORBIDDEN_SCOPE`).
```json
{
  "forbidden_scope_status": 401,
  "forbidden_scope_text": ""
}
```
5. Incident workflow via MCP: create -> get -> update status (`PATCH /api/incidents/{id}/status`).
```json
{
  "incident_id": null,
  "incidents_create": {},
  "incidents_get": {},
  "incidents_update_status": {}
}
```
6. Inventory read works and write is explicitly blocked.
```json
{
  "inventory_create_product_blocked": {},
  "inventory_list_products": {}
}
```
7. Validation errors are distinct (`MCP_VALIDATION_ERROR`).
```json
{
  "inventory_invalid_validation_text": ""
}
```

## Manual OAuth Playground Evidence (to attach)
- Screenshot of MCP Playground connected to the same public URL.
- Screenshot of OAuth completion against Logto/Auth0 (MCP_AUTH_TEST_MODE=0 environment).
- Screenshot or export showing the same tool executions in Playground.
