# Project Brief

## Business Description
TrackFlow is a logistics and warehouse operations platform serving e-commerce
brands in the United States and Spain. The monorepo covers the public website,
operations backoffice, supplier directory, talent pipeline, FastAPI services,
data pipelines, telemetry, and commercial knowledge (RAG) workflows.

## Objectives
- Provide canonical UIs and APIs for leads, auth, incidents, inventory,
  suppliers, talent, telemetry, and reporting.
- Keep every supported component aligned with its authoritative context
  document (see root README requirements source map).
- Deliver actionable warehouse and carrier insights from shared TypeScript
  business logic (`packages/trackflow-core`).

## Problem Statement
TrackFlow consolidates logistics operations across LA and Zaragoza. Teams need
a single, context-conformant platform for incident management, inventory
orders, supplier relationships, talent tracking, and commercial knowledge —
without conflicting duplicate implementations or stale contracts.
