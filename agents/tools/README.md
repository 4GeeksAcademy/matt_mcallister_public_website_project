# `agents/tools` folder

This folder groups **reusable tools** that agents in the monorepo can use (for example: connectors to internal APIs, database wrappers, scraping utilities, validators, service clients, etc.).

- **Main purpose**: avoid duplicated code across agents and standardize how agents interact with company systems.
- **Recommendation**: document each tool you add (what it does, inputs/outputs, permissions/security, limits, and usage examples) and link to it from the agents that use it.

## Tools

| Tool | Path | Description |
|------|------|-------------|
| Incident ticket lookup | [`incident_lookup.py`](./incident_lookup.py) | Typed HTTP client for `GET /api/incidents` with timeout and honest fallbacks |

> _Spanish version: [README.es.md](./README.es.md)._
