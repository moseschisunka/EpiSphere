# Versioned n8n workflow templates

Import these templates into n8n, then attach credentials in the n8n editor.
The exports intentionally contain no API keys. Configure the `X-API-Key`
header from an encrypted n8n credential using the dedicated `NEWS_AGENT_API_KEY`
or `DATASET_AGENT_API_KEY` value; never replace the placeholder with a key in
source control.

Run each workflow with `dry_run: true` first. Confirm the returned `batch_id`,
record counts, warnings, and audit entries before enabling writes. The templates
retry backend calls three times with a five-second delay. The dataset workflow
queues a durable ingestion job, waits 30 seconds, then reads the job status;
operators must not treat a queued or running job as a completed import.

Import `workflow-failure-notification.json` as n8n's error workflow and attach
the separately revocable interop credential. It records only workflow metadata
in EpiSphere's interoperability audit ledger. Do not add execution payloads,
API keys, or patient data to failure notifications.
