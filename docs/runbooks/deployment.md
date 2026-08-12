# Deployment runbook

## Preconditions

1. Use a reviewed commit from `main`; verify `git status` is clean.
2. Provide non-empty production values for `SECRET_KEY`, `NEWS_AGENT_API_KEY`,
   `DATASET_AGENT_API_KEY`, `N8N_ENCRYPTION_KEY`, and SMTP credentials through a
   secret manager. Set `ENVIRONMENT=production`,
   `EMAIL_VERIFICATION_REQUIRED=true`, and
   `MFA_REQUIRED_FOR_PRIVILEGED=true`.
3. Review `PUBLIC_DATASET_ALLOWED_HOSTS` and DHIS2 settings for the deployment.
4. Confirm the image tags in `docker-compose.yml` are approved and scanned.
5. Set resource ceilings for PostgreSQL, Redis, backend, ingestion worker,
   frontend, and n8n. The `.env.example` defaults are conservative starting
   points, not capacity commitments; tune them with staging load evidence.
6. Keep `POSTGRES_PORT_BIND` and `REDIS_PORT_BIND` loopback-only. Containers
   communicate over the internal Compose network; use a separately secured
   administrative tunnel or network path rather than exposing either service.

Before enabling the production MFA flag, enroll every privileged operator using
`POST /api/v1/auth/mfa/setup` and `POST /api/v1/auth/mfa/enable` in a protected
staging/bootstrap window. Production login fails closed for privileged accounts
that are not enrolled.

## Deploy

```powershell
docker compose config --quiet
docker compose pull
docker compose up -d
docker compose ps
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/ready
Invoke-WebRequest http://localhost:8000/ready/components
```

The backend entrypoint applies Alembic migrations before starting Gunicorn.
Frontend and n8n wait for the backend health condition in Compose.

`/ready/components` is the deployment readiness gate. In production it fails
closed when the durable ingestion worker has not written a fresh database
heartbeat within `WORKER_HEARTBEAT_MAX_AGE_SECONDS` (45 seconds by default),
or when it has left a job running beyond `WORKER_STALE_AFTER_MINUTES`. An idle
worker is therefore distinguishable from a stopped worker. Investigate the
worker logs and its database connectivity before restarting or replaying work.

The n8n service is configured to retain error executions for diagnosis while
pruning successful/manual execution payloads. Production concurrency is capped
by `N8N_CONCURRENCY_PRODUCTION_LIMIT`; adjust it only after load evidence. The
workflow templates keep manual execution storage disabled and contain no
credentials. Protect the n8n editor with authenticated TLS at the reverse
proxy; do not expose the raw `5678` port to the public internet. Run the n8n
security audit before activation (`n8n audit`) and record the result with the
pilot evidence.

Execution pruning and concurrency settings follow n8n's documented execution
data controls: https://docs.n8n.io/hosting/scaling/execution-data and
https://docs.n8n.io/hosting/scaling/concurrency-control/.

Run the notification worker on a scheduler or worker host after configuring
SMTP. It is intentionally bounded and safe to run repeatedly:

```powershell
python backend/scripts/deliver_notifications.py
```

## Rollback

1. Record the failed commit and request ID from logs.
2. Deploy the previous approved image/commit.
3. Do not downgrade the database automatically; use a reviewed migration
   rollback or forward-fix plan.
4. Re-run `/health`, `/ready`, core role journeys, and the ingestion dry run.
