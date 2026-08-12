# EpiSphere privacy impact assessment (pilot draft)

## Decision status

Draft for partner and institutional privacy review. This document does not
authorize production processing of identifiable clinical data. The pilot is a
no-go until the governance owner records approval, the data-sharing agreement
is signed, and all critical privacy findings are closed.

## 1. Processing purpose

EpiSphere combines disease surveillance, facility-level clinical operations,
public-health alerts, forecasting, and DHIS2/n8n data exchange. The pilot must
limit processing to the approved diseases, facilities, countries, users, and
evaluation measures. Secondary use, public release, or model training outside
that scope requires a new review.

## 2. Data flows derived from the current codebase

| Flow | Data involved | Trust boundary | Primary controls |
|---|---|---|---|
| Facility clinical entry | Patients, encounters, diagnoses, prescriptions | Browser -> API -> facility-scoped database | HTTPS deployment, authenticated role, facility scope, audit trail |
| Surveillance ingestion | Case aggregates, import metadata, quality checks | Upload/API/DHIS2/n8n -> ingestion services | Source allowlist, validation, idempotency, lineage, scoped agent keys |
| Alert response | Alert signal, assignments, review decisions, notification email | Detection -> durable outbox -> approved recipients | Human review, response lifecycle, recipient audit, retry/DLQ controls |
| Public disclosure | Provincial/country aggregates, news, public alerts | Internal services -> public endpoints | Privacy threshold suppression, public visibility consent, no identifiers |
| Authentication | Password hash, MFA secret, reset/verification tokens, sessions | Browser -> auth API -> database/SMTP | Hashed single-use tokens, token version revocation, MFA, no token logging |

## 3. Data-subject and harm assessment

| Risk | Potential harm | Mitigation in code/process | Residual evidence required |
|---|---|---|---|
| Re-identification from small cells | Identification of patients or small facilities | Public threshold suppression and restricted scope | Test results across each pilot geography and disease |
| Excess facility access | Unauthorised viewing or modification of clinical records | Server-side country/facility authorization matrix | Seeded cross-scope integration tests and access review |
| Credential compromise | Account takeover or prolonged access | MFA, hashed expiring tokens, logout/session revocation, scoped keys | Production secret rotation and incident drill |
| Incorrect alert or forecast | Misallocation of scarce response resources | Human review, model cards, quality checks, visible uncertainty | Signed review SOP, false-positive/negative evaluation |
| Ingestion replay/duplication | Inflated counts and incorrect decisions | Source record IDs, checksums, idempotency, lineage | Replay test with before/after count reconciliation |
| Uncontrolled export or backup | Persistent disclosure outside the platform | Export review, private storage, retention schedule | Backup access review, restore drill, deletion verification |
| Third-party transmission | Disclosure to SMTP, DHIS2, or n8n recipients | Explicit endpoint/source configuration and audit logging | Data-processing and recipient approvals |

## 4. Necessity and minimisation decisions

- Use aggregate case records for surveillance whenever patient-level data is
  not necessary.
- Return protected MRN display values rather than raw MRNs in API responses.
- Do not put identifiers, tokens, or clinical payloads in logs, URLs, alert
  subjects, or analytics events.
- Make public visibility an explicit facility consent/configuration decision;
  a facility must not become public solely because it was ingested.
- Restrict AI/forecast inputs to approved, de-identified or aggregated data
  and retain model-card and human-review evidence for consequential outputs.

## 5. Required approvals and operating evidence

Before pilot go-live, the governance owner must attach:

1. Named data controller/owner and processor responsibilities.
2. Approved purpose, disease, geography, facility, user, and recipient scope.
3. Signed data-sharing agreement, retention schedule, and breach escalation
   contacts.
4. Access matrix review, privacy regression results, and purge dry-run output.
5. Backup/restore and key-rotation evidence.
6. UAT sign-off from the facility, epidemiology, and platform-admin roles.

Any change to processing purpose, identifiable fields, recipients, public
disclosure threshold, or model use reopens this assessment.
