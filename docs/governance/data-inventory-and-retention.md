# EpiSphere data inventory and retention schedule

## Purpose

This is the implementation-facing inventory for the current EpiSphere modular
monolith. It translates the database models, API routes, disclosure controls,
and audit paths into retention decisions that can be approved by the pilot
partner. It is not a substitute for a signed data-sharing agreement or local
privacy review.

The periods below are proposed pilot defaults. A partner-approved schedule
takes precedence and must be recorded before identifiable clinical data is
loaded.

## Inventory

| Data class | Current examples | Permitted use | Default access boundary | Proposed pilot retention | Disposal or review action |
|---|---|---|---|---:|---|
| Public aggregate | `/public/stats`, `/public/provinces`, `/public/map`, public news | Public situational awareness | Anonymous/public; small cells suppressed | 24 months online, then archive or review | Reassess disclosure risk before publication and archive |
| Restricted aggregate | Country dashboards, forecasts, surveillance trends, DHIS2 extracts | Epidemiology and response planning | Country/facility scope plus role | 24 months online, then annual review | Aggregate or delete when no longer needed for the approved use |
| Identifiable clinical | `Patient.mrn`, `Patient.dob`, encounters, prescriptions | Direct care and facility operations | Assigned facility clinical roles only | 12 months after last care interaction, unless partner policy requires longer | Secure deletion or irreversible de-identification with an audit record |
| Credentials and security tokens | Password hashes, MFA secrets, verification/reset tokens, session version | Authentication and account security | Security/authentication services only | Tokens: 24 hours; disabled users: review within 30 days | Expired tokens are purged; revoke sessions on account/security events |
| Alert response evidence | Alerts, assignments, reviews, notification outbox | Public-health response and accountability | Scoped response roles; audit all privileged changes | 24 months after closure | Archive for approved evaluation or delete after review |
| Audit evidence | `AuditLog`, request IDs, ingestion lineage, quality checks | Security, integrity, and incident review | Security/admin investigators | 24 months minimum for pilot; partner may require longer | Restricted archive; deletion requires governance approval |
| Source and import metadata | `ImportBatch`, row errors, checksums, source systems, DHIS2 logs | Reproducibility and replay | Data officers and administrators | 24 months after final replay/reconciliation | Retain lineage without source payload where possible |

## Required implementation controls

1. Do not load identifiable clinical records until the facility, country, and
   partner scope has been approved and the signed retention schedule is stored
   with the pilot evidence.
2. Use the existing facility/country authorization functions for every new
   clinical or restricted aggregate endpoint. A frontend role check is never a
   substitute for server authorization.
3. Keep public disclosure threshold enforcement enabled. Any change to the
   threshold requires a privacy review and regression tests for small cells.
4. Run a scheduled purge/review job for expired security tokens and each
   approved retention class. The job must emit counts and an audit event; it
   must not log raw MRNs, emails, tokens, or clinical content.
5. Prefer de-identification or aggregation when the analytical purpose does
   not require direct identifiers. Preserve a reversible linkage only at the
   facility under an approved clinical workflow.
6. Record legal basis, data owner, processor, sharing recipients, and cross-
   border transfer decisions in the pilot data-sharing agreement.

## Evidence required before pilot go-live

- Signed retention periods and data owners.
- A tested purge/review job with dry-run output and rollback/backup evidence.
- Disclosure-control tests for public and restricted aggregates.
- Access review showing country and facility scope for every pilot account.
- Security review of backups, logs, exports, and notification recipients.
- Approved data-sharing agreement and privacy impact assessment.
