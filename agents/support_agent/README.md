# TrackFlow Support Knowledge Agent

Commercial knowledge assistant for account managers, implemented as an explicit **LangGraph** over the Milestone 7 RAG pipeline with **MCP-backed incident ticket lookups**.

## Goal

Answer prospect and client questions the way a TrackFlow salesperson would — grounded in indexed policy docs — and look up real incident ticket status through the OAuth-protected MCP company-tools server when the question is operational.

## Graph

```mermaid
flowchart TD
  receiveQuestion[receive_question] --> validQ{valid?}
  validQ -->|no| setError[set_error]
  validQ -->|yes| classify[classify_route]
  classify -->|ticket| mcpTicket[mcp_ticket_lookup_node]
  classify -->|knowledge| retrieveNode[retrieve_node]
  mcpTicket --> ticketAnswer[format_ticket_answer]
  ticketAnswer --> endNode[END]
  setError --> endNode
  retrieveNode --> hasCtx{chunks?}
  hasCtx -->|no| noContext[no_context_response]
  hasCtx -->|yes| generateNode[generate_node]
  noContext --> endNode
  generateNode --> endNode
```

- **Knowledge path:** `retrieve()` + `generate_answer()` from [`data/pipelines/rag.py`](../../data/pipelines/rag.py)
- **Ticket path:** [`agents/mcp/client.py`](../mcp/client.py) loads tools via `langchain-mcp-adapters` and invokes `incidents_get` / `incidents_list` on the MCP server — no direct incident-api HTTP from the agent

Routing is automatic from question content (incident ID or ticket keywords → MCP ticket tool; otherwise → RAG).

## API

`POST /agent/query` (incident-api) coexists with `POST /knowledge/query`:

```bash
# Policy / knowledge question
curl -X POST http://localhost:8001/agent/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the standard return window?"}'

# Ticket lookup question
curl -X POST http://localhost:8001/agent/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the status of incident inc_abc123..."}'
```

Response:

```json
{
  "answer": "...",
  "sources": [{"source_document": "...", "section": "...", "language": "en"}],
  "trace_id": "uuid",
  "sources_used": ["rag"]
}
```

Ticket answers use `"sources_used": ["mcp_ticket_tool"]` and empty `sources` (no KB citations).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_SERVER_URL` | `http://localhost:8006/mcp` | MCP company-tools endpoint |
| `MCP_AGENT_ACCESS_TOKEN` | _(required for live MCP)_ | OAuth Bearer token with `incidents:read` |

See [`mcps/company_tools/README.md`](../../mcps/company_tools/README.md) for MCP server configuration.

## Trace inspection

```python
from agents.support_agent.trace import get_trace
get_trace(trace_id)
```

Each run records node order plus whether `rag` or `mcp_ticket_tool` was used.

## Tests

```bash
PYTHONPATH=. python3 -m pytest tests/pipelines/test_agent_graph.py tests/pipelines/test_agent_tools.py -q
```

Also included in `bash scripts/test-python.sh`.
