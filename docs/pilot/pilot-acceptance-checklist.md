# Pilot acceptance checklist

| Area | Evidence required | Owner | Status |
|---|---|---|---|
| Governance | Scope, partner, data-sharing agreement |  | Pending |
| Privacy | Classification, retention, disclosure-control review |  | Pending |
| Security | Scoped keys, role matrix, revocation test |  | Pending |
| Ingestion | Dry run, quality thresholds, lineage, replay test |  | Pending |
| Operations | `/ready`, metrics, backup/restore drill, rollback test |  | Pending |
| Response | Alert acknowledge/assign/escalate/review/close evidence |  | Pending |
| Interoperability | DHIS2 sandbox exchange and n8n failure/retry evidence |  | Pending |
| Training | Data officer and epidemiologist UAT sign-off |  | Pending |
| Evaluation | Completeness, timeliness, false positives, uptime, adoption |  | Pending |

## Go/no-go rule

Go only when no critical security, privacy, data-integrity, or recovery item is
Pending and the governance owner signs the decision. Any high-impact model
signal must have a recorded human review decision.
