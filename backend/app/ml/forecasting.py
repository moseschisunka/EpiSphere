"""Forecasting Engine

Implements transparent forecasting methods with rolling-origin validation.
Complex models are used only when available and validated against simpler baselines.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class ForecastingPipeline:
    """Multi-model forecasting pipeline with transparent baselines and backtesting."""

    MODEL_VERSION = "forecasting_pipeline_v2"

    async def generate_forecast(
        self,
        dates: List[date],
        values: List[float],
        horizon_days: int = 30,
        model_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        series, preprocessing = self._preprocess_series(dates, values)
        if len(series) < 30:
            raise ValueError("Need at least 30 days of historical data after preprocessing")

        future_dates = [series.index[-1].date() + timedelta(days=i + 1) for i in range(horizon_days)]

        if model_type:
            forecast_result = await self._forecast_with_model(model_type, series, future_dates, horizon_days)
            backtest = await self._rolling_backtest(series, [forecast_result["model_type"]])
        else:
            candidates = self._candidate_models()
            backtest = await self._rolling_backtest(series, candidates)
            selected = self._select_model(backtest, candidates)
            forecast_result = await self._forecast_with_model(selected, series, future_dates, horizon_days)

        forecast_result["accuracy_metrics"] = {
            "model_version": self.MODEL_VERSION,
            "rolling_backtest": backtest,
            "selected_model": forecast_result["model_type"],
            "preprocessing": preprocessing,
            "candidate_models": self._candidate_models(),
            "validation_method": "rolling_origin",
            "drift_monitoring": self._drift_summary(series),
            "retraining_triggers": {
                "interval_coverage_below": 0.8,
                "recent_mean_shift_ratio_above": 1.5,
                "missing_days_above": 7,
            },
        }
        return forecast_result

    def _candidate_models(self) -> List[str]:
        models = ["seasonal_naive", "simple_trend", "exp_smoothing"]
        if ARIMA_AVAILABLE:
            models.append("arima")
        if PROPHET_AVAILABLE:
            models.append("prophet")
        return models

    def _preprocess_series(self, dates: List[date], values: List[float]) -> tuple[pd.Series, Dict[str, Any]]:
        df = pd.DataFrame({"date": pd.to_datetime(dates), "value": values})
        df = df.groupby("date", as_index=True)["value"].sum().sort_index()
        full_index = pd.date_range(df.index.min(), df.index.max(), freq="D")
        missing_days = int(len(full_index.difference(df.index)))
        series = df.reindex(full_index).fillna(0.0).clip(lower=0)

        excluded = 0
        today = pd.Timestamp(date.today())
        if len(series) > 30 and series.index[-1] >= today:
            series = series.iloc[:-1]
            excluded = 1

        return series, {
            "missing_days": missing_days,
            "filled_missing_days_with_zero": missing_days,
            "excluded_recent_incomplete_days": excluded,
            "history_start": series.index[0].date().isoformat(),
            "history_end": series.index[-1].date().isoformat(),
            "history_points": int(len(series)),
        }

    async def _rolling_backtest(self, series: pd.Series, models: List[str]) -> Dict[str, Any]:
        horizon = min(7, max(1, len(series) // 10))
        min_train = max(30, int(len(series) * 0.5))
        cutoffs = list(range(min_train, len(series) - horizon + 1, horizon))[-4:]
        results: Dict[str, Any] = {}

        for model_name in models:
            fold_metrics = []
            for cutoff in cutoffs:
                train = series.iloc[:cutoff]
                actual = series.iloc[cutoff:cutoff + horizon]
                future_dates = [d.date() for d in actual.index]
                try:
                    forecast = await self._forecast_with_model(model_name, train, future_dates, horizon)
                    predicted = np.array(forecast["forecast_data"]["values"], dtype=float)
                    lower = np.array(forecast["forecast_data"].get("lower_bound", predicted), dtype=float)
                    upper = np.array(forecast["forecast_data"].get("upper_bound", predicted), dtype=float)
                    observed = actual.values.astype(float)
                    errors = predicted - observed
                    denominator = np.maximum(np.abs(observed), 1.0)
                    interval_coverage = float(np.mean((observed >= lower) & (observed <= upper)))
                    fold_metrics.append({
                        "cutoff_date": train.index[-1].date().isoformat(),
                        "mae": float(np.mean(np.abs(errors))),
                        "rmse": float(np.sqrt(np.mean(errors ** 2))),
                        "mean_bias": float(np.mean(errors)),
                        "smape": float(np.mean(2 * np.abs(errors) / np.maximum(np.abs(predicted) + np.abs(observed), 1.0))),
                        "mape_guarded": float(np.mean(np.abs(errors) / denominator)),
                        "interval_coverage": interval_coverage,
                    })
                except Exception as exc:
                    fold_metrics.append({"cutoff_date": train.index[-1].date().isoformat(), "error": str(exc)})

            valid = [m for m in fold_metrics if "mae" in m]
            results[model_name] = {
                "folds": fold_metrics,
                "mean_mae": float(np.mean([m["mae"] for m in valid])) if valid else None,
                "mean_rmse": float(np.mean([m["rmse"] for m in valid])) if valid else None,
                "mean_bias": float(np.mean([m["mean_bias"] for m in valid])) if valid else None,
                "mean_smape": float(np.mean([m["smape"] for m in valid])) if valid else None,
                "mean_interval_coverage": float(np.mean([m["interval_coverage"] for m in valid])) if valid else None,
                "mae_stability": float(np.std([m["mae"] for m in valid])) if len(valid) > 1 else 0.0,
                "valid_folds": len(valid),
            }
        return results

    def _select_model(self, backtest: Dict[str, Any], candidates: List[str]) -> str:
        valid = [name for name in candidates if backtest.get(name, {}).get("mean_mae") is not None]
        if not valid:
            return "simple_trend"
        return min(valid, key=lambda name: (backtest[name]["mean_mae"], -1 * (backtest[name].get("mean_interval_coverage") or 0)))


    def _drift_summary(self, series: pd.Series) -> Dict[str, Any]:
        recent = series.tail(14)
        baseline = series.iloc[:-14] if len(series) > 28 else series
        baseline_mean = float(baseline.mean()) if len(baseline) else 0.0
        recent_mean = float(recent.mean()) if len(recent) else 0.0
        mean_shift_ratio = recent_mean / baseline_mean if baseline_mean > 0 else None
        baseline_std = float(baseline.std()) if len(baseline) > 1 else 0.0
        recent_std = float(recent.std()) if len(recent) > 1 else 0.0
        return {
            "recent_window_days": int(len(recent)),
            "baseline_mean": baseline_mean,
            "recent_mean": recent_mean,
            "mean_shift_ratio": mean_shift_ratio,
            "baseline_std": baseline_std,
            "recent_std": recent_std,
            "shift_flag": bool(mean_shift_ratio is not None and (mean_shift_ratio >= 1.5 or mean_shift_ratio <= 0.5)),
        }

    async def _forecast_with_model(self, model_type: str, series: pd.Series, future_dates: List[date], horizon_days: int) -> Dict[str, Any]:
        if model_type == "prophet" and PROPHET_AVAILABLE:
            return await self._prophet_forecast(series, future_dates, horizon_days)
        if model_type == "arima" and ARIMA_AVAILABLE:
            return await self._arima_forecast(series, future_dates, horizon_days)
        if model_type == "seasonal_naive":
            return await self._seasonal_naive_forecast(series, future_dates, horizon_days)
        if model_type == "exp_smoothing":
            return await self._exp_smoothing_forecast(series, future_dates, horizon_days)
        if model_type == "lstm":
            result = await self._simple_forecast(series, future_dates, horizon_days)
            result["model_type"] = "simple_trend"
            result["model_note"] = "lstm_placeholder_disabled_simple_trend_used"
            return result
        return await self._simple_forecast(series, future_dates, horizon_days)

    async def _prophet_forecast(self, series: pd.Series, future_dates: List[date], horizon_days: int) -> Dict[str, Any]:
        df = pd.DataFrame({"ds": series.index, "y": series.values})
        model = Prophet(yearly_seasonality=len(series) >= 365, weekly_seasonality=True, daily_seasonality=False)
        model.fit(df)
        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)
        return {
            "model_type": "prophet",
            "forecast_data": {
                "dates": [d.isoformat() for d in future_dates],
                "values": [max(0.0, float(v)) for v in forecast["yhat"].tail(horizon_days).values],
                "lower_bound": [max(0.0, float(v)) for v in forecast["yhat_lower"].tail(horizon_days).values],
                "upper_bound": [max(0.0, float(v)) for v in forecast["yhat_upper"].tail(horizon_days).values],
            },
        }

    async def _arima_forecast(self, series: pd.Series, future_dates: List[date], horizon_days: int) -> Dict[str, Any]:
        try:
            model = ARIMA(series, order=(1, 1, 1))
            fitted_model = model.fit()
            forecast_result = fitted_model.forecast(steps=horizon_days)
            forecast_ci = fitted_model.get_forecast(steps=horizon_days).conf_int()
            values = forecast_result.values.tolist()
            lower = forecast_ci.iloc[:, 0].values.tolist()
            upper = forecast_ci.iloc[:, 1].values.tolist()
            return {
                "model_type": "arima",
                "forecast_data": {
                    "dates": [d.isoformat() for d in future_dates],
                    "values": [max(0.0, float(v)) for v in values],
                    "lower_bound": [max(0.0, float(v)) for v in lower],
                    "upper_bound": [max(0.0, float(v)) for v in upper],
                },
            }
        except Exception:
            return await self._simple_forecast(series, future_dates, horizon_days)

    async def _seasonal_naive_forecast(self, series: pd.Series, future_dates: List[date], horizon_days: int) -> Dict[str, Any]:
        values = []
        for d in future_dates:
            same_dow = series[series.index.dayofweek == pd.Timestamp(d).dayofweek].tail(4)
            values.append(float(same_dow.mean()) if len(same_dow) else float(series.tail(7).mean()))
        residuals = series.diff(7).dropna().tail(30)
        std = float(residuals.std()) if len(residuals) else float(series.tail(30).std())
        std = max(std, 1.0)
        return {
            "model_type": "seasonal_naive",
            "forecast_data": {
                "dates": [d.isoformat() for d in future_dates],
                "values": [max(0.0, float(v)) for v in values],
                "lower_bound": [max(0.0, float(v - 1.96 * std)) for v in values],
                "upper_bound": [max(0.0, float(v + 1.96 * std)) for v in values],
            },
        }

    async def _exp_smoothing_forecast(self, series: pd.Series, future_dates: List[date], horizon_days: int) -> Dict[str, Any]:
        ewm_series = series.ewm(span=7, adjust=False).mean()
        last_ewm = float(ewm_series.iloc[-1])
        diffs = ewm_series.diff().dropna().tail(14)
        trend = float(diffs.mean()) if len(diffs) else 0.0
        values = [max(0.0, last_ewm + trend * (i + 1)) for i in range(horizon_days)]
        std = max(float(series.tail(30).std()), 1.0)
        return {
            "model_type": "exp_smoothing",
            "forecast_data": {
                "dates": [d.isoformat() for d in future_dates],
                "values": [float(v) for v in values],
                "lower_bound": [max(0.0, float(v - 1.96 * std)) for v in values],
                "upper_bound": [float(v + 1.96 * std) for v in values],
            },
        }

    async def _simple_forecast(self, series: pd.Series, future_dates: List[date], horizon_days: int) -> Dict[str, Any]:
        recent = series.tail(7).values.astype(float)
        trend = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
        last_value = float(series.iloc[-1])
        forecast_values = [max(0.0, last_value + trend * (i + 1)) for i in range(horizon_days)]
        std = max(float(series.tail(30).std()), 1.0)
        return {
            "model_type": "simple_trend",
            "forecast_data": {
                "dates": [d.isoformat() for d in future_dates],
                "values": [float(v) for v in forecast_values],
                "lower_bound": [max(0.0, float(v - 1.96 * std)) for v in forecast_values],
                "upper_bound": [float(v + 1.96 * std) for v in forecast_values],
            },
        }
