# EpiSphere AI

EpiSphere AI is a pre-production public-health surveillance and outbreak-intelligence platform for collecting, validating, analysing, and sharing disease surveillance data.

The current repository is suitable for controlled development and pilot work. It is not yet approved for national production or identifiable patient-data deployment. Review the release roadmap and complete the security, privacy, operational, and user-acceptance gates before production use.

## Current architecture

- Backend: FastAPI, SQLAlchemy, Alembic, Python
- Frontend: Next.js 14, React, TypeScript, TailwindCSS
- Data: PostgreSQL/TimescaleDB for deployment, SQLite for local tests, Redis for caching
- Analytics: statistical outbreak detection, ARIMA/Prophet-style forecasting, DHS analytics
- Interoperability: DHIS2 contracts, public dataset ingestion, n8n orchestration
- Deployment: Docker Compose for local environments

The application is currently a modular monolith. Keep domain logic separated inside the existing backend modules until real load, ownership, or reliability requirements justify extracting a service.

## Implemented domains

- Authentication, JWT sessions, RBAC, audit logging, and rate limiting
- Cases, countries, diseases, facilities, clinical encounters, pharmacy workflows, and alerts
- Global and country dashboard APIs
- CSV/Excel upload validation and data-quality lineage structures
- Outbreak detection and forecast generation with stored model metadata
- PDF, DOCX, and CSV report generation
- DHIS2 outbound validation, inbound pull scaffolding, and interoperability logs
- Public WHO/CSV ingestion with agent-key protection and URL safety checks
- n8n workflow guidance for news and dataset ingestion

## Quick start with Docker

1. Copy `.env.example` to `.env` and replace development secrets.
2. Validate the Compose file:

   ```powershell
   docker compose config --quiet
   ```

3. Start the services:

   ```powershell
   docker compose up -d
   ```

4. Initialize the database:

   ```powershell
   docker compose exec backend python scripts/init_db.py
   ```

5. Open:

   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - n8n: http://localhost:5678 (local development only)

See [SETUP.md](SETUP.md) for manual development setup and [n8n_workflows.md](n8n_workflows.md) for the autonomous-agent workflows.

## Local verification

Backend:

```powershell
cd backend
python -m pytest -q
python -m alembic upgrade head
```

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run lint
npm run build
```

## Roles and safety boundary

The platform supports public users, country data officers, epidemiologists, facility administrators, clinicians, pharmacists, and platform administrators. The frontend hides role-inappropriate navigation, but backend authorization remains authoritative.

AI outputs are assistive signals. Forecasts and outbreak alerts require epidemiological review before high-impact public-health action. The system must not be represented as an autonomous clinical or outbreak-decision authority.

## Release status

The merged n8n ingestion work passed repository CI. Remaining release gates include replacing synthetic dashboard data, completing unfinished facility workflows, expanding API/security tests, unifying ingestion lineage, adding observability and recovery testing, and completing privacy governance.

## Documentation

- [SETUP.md](SETUP.md) — environment and local setup
- [QUICK_START.md](QUICK_START.md) — rapid development start
- [DOCUMENTATION.md](DOCUMENTATION.md) — detailed technical documentation
- [n8n_workflows.md](n8n_workflows.md) — n8n integration setup
- [docs/adr](docs/adr) — architecture decisions

## License

EpiSphere is released under the Apache License 2.0. See [LICENSE](LICENSE).
