# Versioned n8n workflow templates

Import these templates into n8n, then attach credentials in the n8n editor.
The exports intentionally contain no API keys. Configure the `X-API-Key`
header from an encrypted n8n credential using the dedicated `NEWS_AGENT_API_KEY`
or `DATASET_AGENT_API_KEY` value; never replace the placeholder with a key in
source control.

Run each workflow with `dry_run: true` first. Confirm the returned `batch_id`,
record counts, warnings, and audit entries before enabling writes.
