# Backup and restore drill

The pilot is not production-ready until this runbook has been executed against
the deployed PostgreSQL environment.

## Backup

```powershell
pg_dump --format=custom --file=episphere-$(Get-Date -Format yyyyMMddHHmmss).dump $env:DATABASE_URL
```

Store encrypted backups outside the application host with a documented
retention policy. Uploads/reports must use private durable object storage before
real patient-level deployment; the current Compose volume is not a substitute.

## Restore drill

1. Provision an isolated PostgreSQL target.
2. Restore the dump with `pg_restore`.
3. Run `alembic current` and verify the expected head revision.
4. Start the backend and verify `/ready`, dashboard queries, alert retrieval,
   and a dry-run ingestion.
5. Record elapsed restore time (RTO), backup age/data loss (RPO), failures, and
   corrective actions.
