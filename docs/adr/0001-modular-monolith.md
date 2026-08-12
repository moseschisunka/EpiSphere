# ADR 0001: Retain the modular monolith as the current architecture

## Status

Accepted for the pilot and pre-production stages.

## Decision

Keep FastAPI, SQLAlchemy, Alembic, and the Next.js application in the current repository. Enforce domain boundaries through endpoint, schema, service, model, and test ownership. Do not extract microservices until measured load, team ownership, or isolation requirements justify the operational cost.

## Consequences

This keeps local development, deployment, transactions, and debugging simple. It requires disciplined module boundaries, explicit interfaces, and focused tests to prevent cross-domain coupling. Future extraction remains possible around ingestion, analytics, or notifications.
