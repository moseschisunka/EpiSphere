# ADR 0002: Use n8n for orchestration and backend workers for processing

## Status

Accepted for the pilot and pre-production stages.

## Decision

Use n8n for schedules, external feed coordination, and partner-facing workflow visibility. Use a durable backend worker/queue for long-running downloads, validation, ingestion, forecasting, report generation, and retries. n8n must not become the system of record or bypass backend authorization and data-quality controls.

## Consequences

The boundary keeps public-health data rules in EpiSphere and makes jobs replayable. A queue and worker introduce operational complexity, so the first implementation may use a single worker process and Redis-backed job state before scaling horizontally.
