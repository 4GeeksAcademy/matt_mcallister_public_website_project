# TrackFlow Backend Architecture Proposal

## 1) Objective and Scope

This document proposes the backend architecture for TrackFlow and explains why it is the most suitable option for the current company context.

TrackFlow operates in two countries (United States and Spain), manages two warehouses with different systems, coordinates multiple carriers, and handles high return rates with largely manual processes. The company needs integration speed, operational reliability, and clear ownership boundaries more than it needs early distributed complexity.

Initial scope of this proposal:
- Architecture pattern selection and justification.
- Backend folder/module organization.
- FastAPI endpoint and router organization by domain.
- Alignment with common FastAPI project conventions.
- Frontend-backend separation considerations.
- Risks and points of attention.

Out of scope for now:
- Full infrastructure-as-code and cloud-specific deployment scripts.
- Detailed database schemas and event definitions.
- Full API contract implementation.

## 2) Recommended Architecture Pattern

### Decision

Use a Modular Monolith with Layered Architecture, implemented as a single FastAPI service in one container/VM for the first production stages.

### Why this pattern fits TrackFlow now

This is not a generic preference. It is based on TrackFlow realities:

1. Integration complexity is already high.
TrackFlow has two warehouse systems, a legacy ERP, and undocumented integrations. Starting with many microservices would increase coordination and operational overhead before core business flows are stabilized.

2. The team needs faster delivery and easier operations.
The context indicates slow feature deployments and weak incident visibility. A single deployable backend reduces platform complexity and allows faster iteration while telemetry and standards are being established.

3. Domain boundaries still need to be clarified in software.
Business areas are clear (inventory, carriers, returns, CX, reporting), but code boundaries do not exist yet. A modular monolith allows strict internal module boundaries without distributed systems cost.

4. A strong migration path is still possible.
If specific modules become bottlenecks (for example tracking aggregation or returns automation), those modules can later be extracted into independent services with lower risk.

### Why not serverless-first or microservices-first

- Serverless-first is not ideal as the initial default because TrackFlow needs several long-running integration workflows, coordinated monitoring, and predictable operations across two regions and many carrier APIs.
- Microservices-first is premature because current pain points are architecture fragmentation and low observability, not service-level scaling limits.

## 3) Architectural Principles

1. Domain-first boundaries: modules map to business capabilities, not technical layers only.
2. Layered dependencies: API -> application -> domain -> infrastructure.
3. Contract-first interfaces: stable input/output schemas between frontend and backend.
4. Adapter isolation: all external systems (carrier APIs, WMS, ERP, email parsers) accessed through adapters.
5. Observability by default: logs, metrics, traces, health/readiness checks from day one.
6. Evolutionary architecture: optimize for extraction later, not fragmentation now.

## 4) Proposed Backend Folder and Module Structure

The backend should live as a dedicated app, for example inside apps/trackflow-api.

Suggested structure:

```text
apps/
  trackflow-api/
    app/
      main.py
      api/
        deps/
        routers/
          inventory.py
          orders.py
          shipments.py
          carriers.py
          returns.py
          cx.py
          clients.py
          reporting.py
          platform.py
      application/
        inventory/
        orders/
        shipments/
        carriers/
        returns/
        cx/
        clients/
        reporting/
      domain/
        inventory/
        orders/
        shipments/
        carriers/
        returns/
        cx/
        clients/
        reporting/
      infrastructure/
        db/
        repositories/
        integrations/
          wms/
          erp/
          carriers/
          notifications/
      schemas/
      config/
      telemetry/
      security/
    tests/
      unit/
      integration/
      contract/
```

### Separation criteria used

- By business capability: each module owns one coherent business area.
- By change lifecycle: frequently changing integration logic is isolated from stable domain rules.
- By dependency direction: domain rules cannot depend on framework or external clients.
- By ownership potential: each module can later be owned by a squad and potentially extracted.

## 5) Domain Model and Responsibility Split

Primary domains:
- Inventory: stock visibility across both warehouses, adjustments, low-stock alerts.
- Orders: ingestion, normalization, validation, fulfillment state transitions.
- Shipments (MVP priority): dispatch creation, tracking timeline, delivery status unification.
- Carriers: carrier catalog, routing recommendation inputs, performance metrics.
- Returns: request intake, approval rules, collection orchestration, inspection decisions.
- CX: self-service tracking/returns queries, ticket intake.
- Clients: account-level views, client health signals, renewal support data.
- Reporting: executive KPIs, scheduled weekly report generation.
- Platform: auth, tenancy, audit, health/readiness, metrics.

## 6) FastAPI Endpoint and Router Organization

### Grouping strategy

- Versioned base path: /v1
- One router per domain with clear prefixes.
- Router modules stay thin: validation, auth checks, orchestration call, response mapping.
- Business rules stay in application/domain layers.

### Proposed route groups

- /v1/inventory
  - GET /stock
  - GET /stock/{sku}
  - POST /adjustments

- /v1/orders
  - POST /ingest/email
  - POST /
  - GET /{order_id}

- /v1/shipments (MVP)
  - POST /dispatch
  - GET /{shipment_id}/tracking
  - GET /{shipment_id}/events

- /v1/carriers
  - GET /
  - GET /performance
  - POST /webhooks/{carrier}

- /v1/returns
  - POST /requests
  - POST /requests/{id}/decision
  - POST /requests/{id}/collection

- /v1/cx
  - GET /tracking/{reference}
  - GET /returns/{reference}
  - POST /tickets

- /v1/clients
  - GET /
  - GET /{client_id}/health

- /v1/reporting
  - GET /executive/kpis
  - POST /weekly-report/run

- /v1/platform
  - GET /health
  - GET /readiness
  - GET /metrics

### Router conventions

- Shared dependencies in api/deps (auth context, tenant context, request id).
- Consistent error model and HTTP status mapping across routers.
- OpenAPI tags per domain to preserve discoverability and ownership boundaries.

## 7) How Common FastAPI Structure Influences This Design

Common FastAPI production structures usually separate:
- App bootstrap and router registration.
- Routers/controllers from services/use cases.
- Pydantic schemas from persistence models.
- Config and settings management.
- Dependency injection and security helpers.
- Test layers (unit, integration, API contract).

This proposal follows that standard by:
- Keeping routers focused on transport concerns.
- Keeping domain logic independent from FastAPI objects.
- Centralizing settings and environment loading.
- Defining dedicated layers for integrations (carriers, WMS, ERP).
- Reserving explicit test folders for behavior and contract stability.

## 8) Frontend and Backend Separation Considerations

TrackFlow currently has a static website app and no implemented central backend yet. The architecture should support clear separation between UI and API concerns.

### Repository strategy

- Keep monorepo with separate app boundaries:
  - apps/trackflow-website (public frontend)
  - apps/trackflow-api (backend)
- Keep shared contracts in packages/shared when contract reuse is needed.

### API communication

- Frontend never calls carrier or ERP APIs directly.
- Frontend communicates only with trackflow-api endpoints.
- Backend aggregates, normalizes, and secures external data.

### Environment variables and configuration

- Frontend: public-safe variables only (for example API base URL).
- Backend: secrets and integration credentials only on server side.
- Distinct environments for local, staging, production with consistent variable naming.

### CORS and security

- Allow only known frontend origins per environment.
- Restrict methods/headers to required sets.
- Keep auth and rate limiting enforced at API layer.

### Versioning and contracts

- Use /v1 prefix from the beginning.
- Introduce backward-compatible changes by default.
- Use schema versioning and deprecation windows for breaking changes.

## 9) Risks and Points of Attention

1. Domain leakage risk
If teams place business rules in router files or integration adapters, module boundaries erode quickly. This creates duplicated logic and inconsistent behavior.
Mitigation: enforce layered dependency rules and domain code reviews.

2. Integration coupling risk
If carrier/WMS/ERP API logic is spread across multiple modules, each provider change can break many areas.
Mitigation: isolate external systems behind adapter interfaces owned by infrastructure/integrations.

3. Contract drift risk
If frontend and backend evolve without explicit shared contracts and versioning, production regressions are likely.
Mitigation: adopt contract tests and version policy from first release.

4. Observability gap risk
If telemetry is postponed, incident response will repeat the current reactive pattern.
Mitigation: require health/readiness endpoints, structured logs, and metrics as release criteria.

## 10) Evolution Path

This proposal intentionally starts with a modular monolith. Service extraction should happen only when measurable triggers appear, such as:
- Distinct scaling profiles by domain.
- Independent release cadence required by a module.
- Reliability isolation needs that cannot be solved in-process.

Likely first extraction candidates in the future:
- Tracking aggregation domain.
- Returns automation domain.

## 11) Final Recommendation

Implement a single FastAPI backend using modular domain boundaries and layered internals, prioritizing Shipments + Tracking for MVP value. This approach gives TrackFlow the best balance of delivery speed, operational control, and future scalability while reducing current architecture fragmentation.
