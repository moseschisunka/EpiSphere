# Incident-response runbook

## First 15 minutes

1. Record start time, reporter, affected tenant/source, and the latest deploy.
2. Capture `X-Request-ID`, endpoint, status code, and relevant structured logs.
3. Check `/health`, `/ready`, `/metrics`, database, Redis, storage, and n8n
   execution status.
4. If ingestion is unsafe, disable the affected n8n workflow and revoke its
   scoped API key; do not delete batches or cases.

## Public-health data incident

1. Set the source or workflow to validation-only/dry-run.
2. Preserve the `ImportBatch`, quality checks, row errors, source checksum, and
   audit records.
3. Identify affected country/disease/date/source-record identities.
4. Notify the governance owner and document whether dashboards or alerts were
   affected.

## Closure

Record root cause, scope, containment, correction, user communication, and a
follow-up test or control. Attach the evidence to the incident record.
