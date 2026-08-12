# Model card: Outbreak detection engine v2

## Intended use

Screen aggregate surveillance time series for signals that require human review.
The engine combines baseline threshold, EWMA, CUSUM, Farrington-style, seasonal,
and optional isolation-forest screening methods.

## Human-review boundary

An engine signal creates a `TRIGGERED` alert with `review_status=PENDING`; it is
not an accepted outbreak declaration. A permitted epidemiologist or administrator
must record an `ACCEPTED`, `REJECTED`, or `INCONCLUSIVE` review decision and notes.

## Limitations

- Missing dates are filled with zero and reported in detection metadata.
- Threshold profiles are configurable by disease but require validation against
  local reporting practice and seasonality.
- Isolation Forest is marked `screening_only` when used.
- Reporting delays, denominator changes, case-definition changes, and small-cell
  instability can produce false signals.

## Reproducibility

Alerts persist method results, threshold profile, preprocessing metadata,
triggered methods, latest observation date, and model-version metadata. Review
decisions and later lifecycle changes are audit logged.
