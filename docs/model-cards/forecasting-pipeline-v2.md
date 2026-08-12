# Model card: Forecasting pipeline v2

## Intended use

Generate short-horizon surveillance forecasts for an epidemiologist reviewing
country/disease time series. The output is decision support, not an automatic
intervention or public-health determination.

## Methods

The pipeline preprocesses duplicate dates, fills missing dates explicitly, clips
negative counts, excludes an incomplete current day, and compares seasonal
naive, simple trend, exponential smoothing, ARIMA, and Prophet when available.
Automatic selection is based on rolling-origin mean absolute error with interval
coverage as a tie-breaker.

## Limitations and safeguards

- At least 30 historical daily points are required.
- Missing days are filled with zero and reported in `accuracy_metrics.preprocessing`.
- Forecast intervals and rolling-origin metrics are persisted with each result.
- Drift summaries and retraining trigger thresholds are persisted with each result.
- The public API bounds the horizon to 90 days and does not expose the LSTM placeholder.
- An epidemiologist must review material signals before operational action.

## Review evidence

Every forecast stores the selected model, model version, candidate models,
validation method, fold metrics, preprocessing assumptions, and drift summary in
`accuracy_metrics`. Any pilot approval must attach country/disease-specific
coverage, bias, stability, and false-alarm evidence before deployment.
