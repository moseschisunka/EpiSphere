# ADR 0003: Classify public-health data before expanding deployment

## Status

Accepted; implementation required before identifiable-data pilot use.

## Decision

Classify data as public aggregate, restricted aggregate, identifiable clinical, credentials, or audit evidence. Apply least-privilege access, retention, logging, disclosure control, and storage rules by class. Public endpoints may expose only approved aggregates and must protect small cells and sensitive subnational results.

## Consequences

This supports Ministry of Health and NPHI governance while preserving public dashboards. It requires a data inventory, privacy impact assessment, retention policy, and API-level disclosure tests.
