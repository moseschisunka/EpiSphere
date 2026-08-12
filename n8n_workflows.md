# n8n Autonomous Agent Workflows

These workflows call EpiSphere through the `X-API-Key` header. Set
`NEWS_AGENT_API_KEY`, `DATASET_AGENT_API_KEY`, and `INTEROP_AGENT_API_KEY` in
the backend environment and store each value in its matching encrypted n8n credential. Never commit a key
in a workflow export or this repository. Importable templates live in
`n8n/workflows/`.

## Deployment boundary

Compose binds the n8n editor to `127.0.0.1:5678` by default. Do not change
`N8N_PORT_BIND` to a public interface. For remote production access, place an
authenticated TLS reverse proxy in front of n8n and configure `N8N_HOST`,
`N8N_PROTOCOL`, and `WEBHOOK_URL` for that public hostname.

## Global health news scraper

1. Add a daily Schedule Trigger.
2. Add an RSS Read node using a trusted WHO, CDC, or equivalent public-health feed.
3. Limit the items to the five newest articles.
4. Add an HTTP Request node:
   - Method: `POST`
   - URL: `http://backend:8000/api/v1/news`
   - Header: `X-API-Key` from the n8n credential
   - Body: `title`, `summary`, `content`, `source`, and `is_public: true`

## Universal public dataset scraper

1. Add a daily Schedule Trigger.
2. Check the source metadata and continue only when the dataset changed.
3. Add an HTTP Request node:
   - Method: `POST`
   - URL: `http://backend:8000/api/v1/datasets/ingest-csv`
   - Header: `X-API-Key` from the n8n credential
   - Body: `url`, `disease_id`, `mapping`, `dry_run: false`, and `enqueue: true`
4. For WHO GHO data, use `/api/v1/datasets/ingest-who` with `indicator_code`
   instead of `url`.
5. Store the returned `job_id` and poll `GET /api/v1/ingestion/jobs/{job_id}`
   before reporting the import as complete.

Start with `dry_run: true` and confirm the returned job result before enabling
production writes. The backend remains authoritative for authentication,
validation, lineage, retries, and database writes; n8n only schedules and
observes the job.

## Interoperability webhooks

Use `INTEROP_AGENT_API_KEY` only for n8n workflows that call
`POST /api/v1/interop/webhook`. It cannot authenticate news or dataset
ingestion. Record the returned correlation data in the workflow execution and
rotate this credential independently if the workflow is disabled or exposed.
