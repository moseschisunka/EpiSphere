# n8n Autonomous Agent Workflows

These workflows call EpiSphere through the `X-API-Key` header. Set
`NEWS_AGENT_API_KEY` and `DATASET_AGENT_API_KEY` in the backend environment and
store each value in its matching encrypted n8n credential. Never commit a key
in a workflow export or this repository. Importable templates live in
`n8n/workflows/`.

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
   - Body: `url`, `disease_id`, `mapping`, and `dry_run: false`
4. For WHO GHO data, use `/api/v1/datasets/ingest-who` with `indicator_code`
   instead of `url`.

Start with `dry_run: true` and confirm the returned record count before enabling
production writes. The backend remains authoritative for authentication,
validation, and database writes.
