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

## Remaining Phase 3 work

The current service calls are synchronous or FastAPI background tasks. Before
pilot scale, move long imports behind a durable worker queue with explicit
retry, cancellation, dead-letter, and replay endpoints. A failed batch must
remain inspectable and must never leave a partial production update.
