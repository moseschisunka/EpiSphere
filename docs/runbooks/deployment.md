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
```

The backend entrypoint applies Alembic migrations before starting Gunicorn.
Frontend and n8n wait for the backend health condition in Compose.

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
