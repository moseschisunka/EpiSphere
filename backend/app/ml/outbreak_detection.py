"""Outbreak Detection Engine

Transparent statistical surveillance methods for early outbreak signal detection.
The engine favors explainable methods before black-box anomaly detection.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import date

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


@dataclass(frozen=True)
class ThresholdProfile:
    min_cases: int = 3
    z_threshold: float = 2.5
    ewma_l: float = 3.0
    cusum_h_multiplier: float = 3.0
    increase_ratio_threshold: float = 0.5
    farrington_z: float = 2.58
    low_probability: float = 0.45
    moderate_probability: float = 0.65
    high_probability: float = 0.85


DISEASE_THRESHOLD_PROFILES = {
    "cholera": ThresholdProfile(min_cases=1, z_threshold=2.0, ewma_l=2.5, cusum_h_multiplier=2.5, increase_ratio_threshold=0.25),
    "measles": ThresholdProfile(min_cases=1, z_threshold=2.0, ewma_l=2.5, cusum_h_multiplier=2.5, increase_ratio_threshold=0.25),
    "dengue": ThresholdProfile(min_cases=5, z_threshold=2.5, ewma_l=3.0, cusum_h_multiplier=3.0, increase_ratio_threshold=0.5),
    "influenza": ThresholdProfile(min_cases=10, z_threshold=3.0, ewma_l=3.5, cusum_h_multiplier=3.5, increase_ratio_threshold=0.75),
    "malaria": ThresholdProfile(min_cases=10, z_threshold=3.0, ewma_l=3.5, cusum_h_multiplier=3.5, increase_ratio_threshold=0.75),
}


class OutbreakDetectionEngine:
    """Multi-layer outbreak detection system with explainable statistical methods."""

    def __init__(self, window_size: int = 14):
        self.window_size = window_size

    def detect_outbreak(
        self,
        dates: List[date],
        daily_cases: List[int],
        country_name: str = "",
        disease_name: str = "",
    ) -> Dict[str, Any]:
        profile = self._threshold_profile(disease_name)
        series, preprocessing = self._preprocess_series(dates, daily_cases)

        if len(series) < self.window_size * 2:
            return {
                "alert_triggered": False,
                "severity": None,
                "probability_score": 0.0,
                "detection_method": "insufficient_data",
                "explanation": "Insufficient historical data for detection after preprocessing",
                "method_results": {},
                "metadata": {"preprocessing": preprocessing, "threshold_profile": profile.__dict__},
            }

        cases_array = series.values.astype(float)
        method_results = {
            "baseline": self._baseline_threshold_detection(cases_array, profile),
            "ewma": self._ewma_detection(cases_array, profile),
            "cusum": self._cusum_detection(cases_array, profile),
            "farrington": self._farrington_style_detection(series, profile),
        }

        if len(cases_array) >= 30:
            method_results["seasonal"] = self._seasonal_anomaly_detection(cases_array, profile)
        if len(cases_array) >= self.window_size * 2 and len(np.unique(cases_array[-self.window_size:])) > 1:
            method_results["isolation_forest"] = self._isolation_forest_detection(cases_array)

        alerts = [(name, result) for name, result in method_results.items() if result.get("alert")]
        if not alerts:
            return {
                "alert_triggered": False,
                "severity": None,
                "probability_score": 0.0,
                "detection_method": "none",
                "explanation": "No outbreak signals detected",
                "method_results": method_results,
                "metadata": {"preprocessing": preprocessing, "threshold_profile": profile.__dict__},
            }

        best_method, best_result = max(alerts, key=lambda item: item[1].get("probability", 0.0))
        triggered_probs = [result.get("probability", 0.0) for _, result in alerts]
        overall_probability = float(np.mean(triggered_probs))
        severity = self._determine_severity(overall_probability, cases_array[-1], np.mean(cases_array[-self.window_size:]), profile)
        explanation = self._generate_explanation(best_method, best_result, cases_array, country_name, disease_name, preprocessing, profile)

        return {
            "alert_triggered": True,
            "severity": severity,
            "probability_score": overall_probability,
            "detection_method": best_method,
            "explanation": explanation,
            "method_results": method_results,
            "metadata": {
                "preprocessing": preprocessing,
                "threshold_profile": profile.__dict__,
                "triggered_methods": [name for name, _ in alerts],
                "latest_observation_date": series.index[-1].date().isoformat(),
            },
        }

    def _threshold_profile(self, disease_name: str) -> ThresholdProfile:
        key = (disease_name or "").strip().lower()
        for disease_key, profile in DISEASE_THRESHOLD_PROFILES.items():
            if disease_key in key:
                return profile
        return ThresholdProfile()

    def _preprocess_series(self, dates: List[date], daily_cases: List[int]) -> tuple[pd.Series, Dict[str, Any]]:
        if not dates or not daily_cases:
            return pd.Series(dtype=float), {"missing_days": 0, "excluded_recent_incomplete_days": 0}

        df = pd.DataFrame({"date": pd.to_datetime(dates), "cases": daily_cases})
        df = df.groupby("date", as_index=True)["cases"].sum().sort_index()
        full_index = pd.date_range(df.index.min(), df.index.max(), freq="D")
        missing_days = int(len(full_index.difference(df.index)))
        series = df.reindex(full_index).fillna(0.0)
        series = series.clip(lower=0)

        excluded = 0
        today = pd.Timestamp(date.today())
        if len(series) > self.window_size * 2 and series.index[-1] >= today:
            series = series.iloc[:-1]
            excluded = 1

        weekend_mean = float(series[series.index.dayofweek >= 5].mean()) if len(series) else 0.0
        weekday_mean = float(series[series.index.dayofweek < 5].mean()) if len(series) else 0.0
        weekend_effect_ratio = weekend_mean / weekday_mean if weekday_mean > 0 else None

        return series, {
            "missing_days": missing_days,
            "filled_missing_days_with_zero": missing_days,
            "excluded_recent_incomplete_days": excluded,
            "weekend_effect_ratio": weekend_effect_ratio,
        }

    def _baseline_threshold_detection(self, cases: np.ndarray, profile: ThresholdProfile) -> Dict[str, Any]:
        baseline = cases[-self.window_size - 1:-1]
        current = cases[-1]
        baseline_mean = float(np.mean(baseline))
        baseline_std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 0.0
        if baseline_std == 0:
            baseline_std = max(np.sqrt(max(baseline_mean, 1.0)), 1.0)
        z_score = (current - baseline_mean) / baseline_std
        alert = current >= profile.min_cases and z_score > profile.z_threshold
        probability = min(1.0, max(0.0, 1 / (1 + np.exp(-(z_score - profile.z_threshold)))))
        return {"alert": bool(alert), "probability": float(probability), "z_score": float(z_score), "baseline_mean": baseline_mean, "current_value": int(current), "threshold": profile.z_threshold}

    def _ewma_detection(self, cases: np.ndarray, profile: ThresholdProfile) -> Dict[str, Any]:
        baseline = cases[-self.window_size * 2:-self.window_size]
        recent = cases[-self.window_size:]
        baseline_mean = float(np.mean(baseline))
        baseline_std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 0.0
        if baseline_std == 0:
            baseline_std = max(np.sqrt(max(baseline_mean, 1.0)), 1.0)
        lam = 0.3
        z = baseline_mean
        max_z = z
        for value in recent:
            z = lam * value + (1 - lam) * z
            max_z = max(max_z, z)
        sigma_z = baseline_std * np.sqrt(lam / (2 - lam))
        upper = baseline_mean + profile.ewma_l * sigma_z
        latest = recent[-1]
        alert = latest >= profile.min_cases and max_z > upper
        probability = min(1.0, max(0.0, (max_z - baseline_mean) / max(upper - baseline_mean, 1.0)))
        return {"alert": bool(alert), "probability": float(probability), "ewma_value": float(max_z), "expected": baseline_mean, "upper_threshold": float(upper)}

    def _cusum_detection(self, cases: np.ndarray, profile: ThresholdProfile) -> Dict[str, Any]:
        baseline = cases[-self.window_size * 2:-self.window_size]
        baseline_mean = float(np.mean(baseline))
        baseline_std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 0.0
        if baseline_std == 0:
            baseline_std = max(np.sqrt(max(baseline_mean, 1.0)), 1.0)
        recent = cases[-self.window_size:]
        k = 0.5
        s_value = 0.0
        max_s = 0.0
        for value in recent:
            s_value = max(0.0, s_value + (value - baseline_mean - k * baseline_std))
            max_s = max(max_s, s_value)
        threshold = profile.cusum_h_multiplier * baseline_std * np.sqrt(self.window_size)
        alert = recent[-1] >= profile.min_cases and max_s > threshold
        probability = min(1.0, max_s / max(threshold * 1.5, 1.0))
        return {"alert": bool(alert), "probability": float(probability), "cusum_value": float(max_s), "threshold": float(threshold), "expected": baseline_mean}

    def _farrington_style_detection(self, series: pd.Series, profile: ThresholdProfile) -> Dict[str, Any]:
        current_date = series.index[-1]
        current = float(series.iloc[-1])
        baseline = series.iloc[:-7] if len(series) > 21 else series.iloc[:-1]
        same_dow = baseline[baseline.index.dayofweek == current_date.dayofweek]
        comparison = same_dow.tail(8) if len(same_dow) >= 4 else baseline.tail(max(self.window_size, 1))
        if len(comparison) < 4:
            return {"alert": False, "probability": 0.0, "reason": "insufficient_baseline"}
        expected = float(comparison.mean())
        variance = float(comparison.var(ddof=1)) if len(comparison) > 1 else expected
        upper = expected + profile.farrington_z * np.sqrt(max(variance, expected, 1.0))
        alert = current >= profile.min_cases and current > upper
        probability = min(1.0, max(0.0, (current - expected) / max(upper - expected, 1.0)))
        return {"alert": bool(alert), "probability": float(probability), "expected": expected, "upper_threshold": float(upper), "current_value": int(current), "baseline_points": int(len(comparison))}

    def _isolation_forest_detection(self, cases: np.ndarray) -> Dict[str, Any]:
        recent_window = cases[-self.window_size:]
        x_values = recent_window.reshape(-1, 1)
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(x_values)
        latest_anomaly = predictions[-1] == -1
        anomaly_scores = iso_forest.score_samples(x_values)
        latest_score = anomaly_scores[-1]
        min_score = anomaly_scores.min()
        max_score = anomaly_scores.max()
        probability = 1 - ((latest_score - min_score) / (max_score - min_score)) if max_score != min_score else 0.5
        return {"alert": bool(latest_anomaly), "probability": float(probability), "anomaly_score": float(latest_score), "caveat": "screening_only"}

    def _seasonal_anomaly_detection(self, cases: np.ndarray, profile: ThresholdProfile) -> Dict[str, Any]:
        current = float(cases[-7:].mean())
        previous_weeks = float(cases[-21:-7].mean()) if len(cases) >= 21 else 0.0
        if previous_weeks > 0:
            increase_ratio = (current - previous_weeks) / previous_weeks
            alert = current >= profile.min_cases and increase_ratio > profile.increase_ratio_threshold
            probability = min(1.0, max(0.0, increase_ratio))
        else:
            increase_ratio = 0.0
            alert = current >= profile.min_cases
            probability = 0.5 if alert else 0.0
        return {"alert": bool(alert), "probability": float(probability), "increase_ratio": float(increase_ratio), "threshold": profile.increase_ratio_threshold}

    def _determine_severity(self, probability: float, current_value: float, baseline_mean: float, profile: ThresholdProfile) -> str:
        if probability >= profile.high_probability or current_value > max(profile.min_cases, baseline_mean * 3):
            return "high"
        if probability >= profile.moderate_probability or current_value > max(profile.min_cases, baseline_mean * 2):
            return "moderate"
        return "low"

    def _generate_explanation(self, method_name: str, result: Dict[str, Any], cases: np.ndarray, country_name: str, disease_name: str, preprocessing: Dict[str, Any], profile: ThresholdProfile) -> str:
        current = int(cases[-1])
        baseline_mean = float(cases[-self.window_size:-1].mean())
        expected = result.get("expected", result.get("baseline_mean", baseline_mean))
        threshold = result.get("upper_threshold", result.get("threshold"))
        caveat = ""
        if preprocessing.get("missing_days"):
            caveat = f" Data caveat: {preprocessing['missing_days']} missing day(s) were filled before analysis."
        action = "Recommended action: epidemiologist review, verify reporting completeness, and assess need for field investigation."
        return (
            f"Outbreak signal detected in {country_name} for {disease_name} using {method_name}. "
            f"Observed cases are {current}; expected baseline is {expected:.1f}"
            f"{f' with threshold {threshold:.1f}' if isinstance(threshold, (int, float)) else ''}. "
            f"Minimum actionable count for this disease profile is {profile.min_cases}. "
            f"{action}{caveat}"
        )
