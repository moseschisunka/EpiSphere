# Ingestion lineage and replay contract

Every surveillance `Case` written by an approved ingestion path must carry:

- `source_system_id` — stable source identity;
- `source_record_id` — deterministic source key used for idempotency; and
- `import_batch_id` — the validation and commit envelope.

## Current source coverage

| Source | Entry point | Batch envelope | Idempotency key |
|---|---|---|---|
| Manual file upload | `POST /api/v1/cases/upload` | `DataUploadService` | source code + file + country + disease + date + subnational region |
| Manual single case | `POST /api/v1/cases` | shared lineage helper | source system + country + disease + date, or caller-supplied source ID |
| Clinical aggregation | `POST /api/v1/clinical/encounters` | shared lineage helper | country + disease + date + reporting region aggregate key |
| WHO/public CSV | `POST /api/v1/datasets/ingest-*` | `PublicDatasetService` | source URL/indicator + row identity |
| DHIS2 pull | `POST /api/v1/interop/dhis2/pull` | `InteropService` | DHIS2 dataset + org unit + period + mapped element |
| OWID COVID | `POST /api/v1/covid19/ingest` | `CovidDataService` | OWID + country + disease + date |

## Commit rules

1. Validate and record row-level failures before committing accepted rows.
2. Do not overwrite a different source's record; source identity is part of the
   uniqueness boundary.
3. Reprocessing a source record updates the same lineage-linked observation or
   returns an explicit duplicate result; it must not silently add a second
   observation.
4. Batch metadata must contain source timestamps, mapping/contract version, and
   transformation context without raw credentials or patient identifiers.
5. Operators must reconcile `rows_total`, `rows_valid`, and `rows_committed`
   before treating a batch as complete.

## Durable worker operation

The OWID COVID ingestion path is queued in `ingestion_jobs` and processed by
the explicit worker handler. Public CSV, WHO GHO, and DHIS2 sync/pull requests
can also opt into the same queue by setting `enqueue: true`; the API returns a
job identifier with HTTP 202 and operators track it through the job endpoints.

```powershell
python -m scripts.run_ingestion_worker --once
python -m scripts.run_ingestion_worker --poll-seconds 10
```

Operators can inspect, cancel, and replay jobs through `/api/v1/ingestion/jobs`.
Retries use bounded exponential backoff and exhausted jobs enter
`dead_letter`; replay resets the attempt counter without changing the original
payload. Unknown job types are dead-lettered rather than dynamically executed.

Remaining Phase 3 work is to make queued execution the default for production
integrations, move manual file uploads behind the same worker contract, and add
durable source payload/object storage plus transactional batch commit so a
failed job cannot leave a partial production update.
