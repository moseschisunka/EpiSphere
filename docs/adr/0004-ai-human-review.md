# ADR 0004: Keep AI assistive and human-reviewed

## Status

Accepted.

## Decision

Forecasts, anomaly scores, and outbreak signals are decision support. A qualified epidemiologist or authorized public-health officer must review evidence, uncertainty, data quality, and context before an alert becomes a high-impact operational action. The system must record model version, input lineage, output, reviewer, and disposition.

## Consequences

This limits autonomous harm and supports accountability. It requires model metadata, reviewer workflows, calibration/drift monitoring, baseline fallbacks, and audit-ready records before advanced models are promoted.
