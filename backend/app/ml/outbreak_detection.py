"""
Outbreak Detection Engine
Implements multiple detection algorithms for early outbreak signal detection
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class OutbreakDetectionEngine:
    """
    Multi-layer outbreak detection system
    
    Implements:
    1. Baseline statistical thresholds (mean + SD)
    2. Seasonal anomaly detection
    3. Isolation Forest
    4. CUSUM change detection
    5. LSTM residual anomalies (placeholder for future implementation)
    """
    
    def __init__(self, window_size: int = 14):
        """
        Initialize detection engine
        
        Args:
            window_size: Number of days to use for baseline calculation
        """
        self.window_size = window_size
    
    def detect_outbreak(
        self,
        dates: List[date],
        daily_cases: List[int],
        country_name: str = "",
        disease_name: str = ""
    ) -> Dict[str, Any]:
        """
        Run all detection methods and return aggregated results
        
        Returns:
            Dictionary with detection results including:
            - alert_triggered: bool
            - severity: str (low/moderate/high)
            - probability_score: float (0-1)
            - detection_method: str
            - explanation: str
            - method_results: dict with individual method results
        """
        if len(daily_cases) < self.window_size * 2:
            return {
                "alert_triggered": False,
                "severity": None,
                "probability_score": 0.0,
                "detection_method": "insufficient_data",
                "explanation": "Insufficient historical data for detection",
                "method_results": {}
            }
        
        # Convert to numpy array for easier processing
        cases_array = np.array(daily_cases)
        
        # Run all detection methods
        method_results = {}
        
        # 1. Baseline statistical threshold
        baseline_result = self._baseline_threshold_detection(cases_array)
        method_results["baseline"] = baseline_result
        
        # 2. Isolation Forest
        isolation_result = self._isolation_forest_detection(cases_array)
        method_results["isolation_forest"] = isolation_result
        
        # 3. CUSUM change detection
        cusum_result = self._cusum_detection(cases_array)
        method_results["cusum"] = cusum_result
        
        # 4. Seasonal anomaly (if enough data)
        seasonal_result = None
        if len(cases_array) >= 30:
            seasonal_result = self._seasonal_anomaly_detection(cases_array)
            method_results["seasonal"] = seasonal_result
        
        # Aggregate results
        alerts = []
        if baseline_result["alert"]:
            alerts.append(("baseline", baseline_result))
        if isolation_result["alert"]:
            alerts.append(("isolation_forest", isolation_result))
        if cusum_result["alert"]:
            alerts.append(("cusum", cusum_result))
        if seasonal_result and seasonal_result["alert"]:
            alerts.append(("seasonal", seasonal_result))
        
        if not alerts:
            return {
                "alert_triggered": False,
                "severity": None,
                "probability_score": 0.0,
                "detection_method": "none",
                "explanation": "No outbreak signals detected",
                "method_results": method_results
            }
        
        # Determine severity and probability
        # Use the method with highest probability
        best_alert = max(alerts, key=lambda x: x[1]["probability"])
        method_name, result = best_alert
        
        # Calculate overall probability (average of all triggered methods)
        triggered_probs = [r["probability"] for _, r in alerts]
        overall_probability = np.mean(triggered_probs)
        
        # Determine severity based on probability and magnitude
        severity = self._determine_severity(overall_probability, cases_array[-1], cases_array[-self.window_size:].mean())
        
        explanation = self._generate_explanation(
            method_name, result, cases_array, country_name, disease_name
        )
        
        return {
            "alert_triggered": True,
            "severity": severity,
            "probability_score": float(overall_probability),
            "detection_method": method_name,
            "explanation": explanation,
            "method_results": method_results
        }
    
    def _baseline_threshold_detection(self, cases: np.ndarray) -> Dict[str, Any]:
        """
        Baseline statistical threshold detection
        
        Alert if current value exceeds mean + 2*SD of baseline window
        """
        if len(cases) < self.window_size:
            return {"alert": False, "probability": 0.0}
        
        baseline = cases[-self.window_size-1:-1]  # Exclude current day
        current = cases[-1]
        
        baseline_mean = np.mean(baseline)
        baseline_std = np.std(baseline)
        
        if baseline_std == 0:
            baseline_std = 1  # Avoid division by zero
        
        # Z-score
        z_score = (current - baseline_mean) / baseline_std
        
        # Alert if exceeds 2 standard deviations
        alert = z_score > 2.0
        
        # Probability based on z-score (sigmoid-like function)
        probability = min(1.0, max(0.0, 1 / (1 + np.exp(-(z_score - 2.0)))))
        
        return {
            "alert": alert,
            "probability": float(probability),
            "z_score": float(z_score),
            "baseline_mean": float(baseline_mean),
            "current_value": int(current)
        }
    
    def _isolation_forest_detection(self, cases: np.ndarray) -> Dict[str, Any]:
        """
        Isolation Forest anomaly detection
        
        Uses Isolation Forest to detect outliers in recent cases
        """
        if len(cases) < self.window_size * 2:
            return {"alert": False, "probability": 0.0}
        
        # Use recent window for detection
        recent_window = cases[-self.window_size:]
        
        # Reshape for sklearn
        X = recent_window.reshape(-1, 1)
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(X)
        
        # Check if latest point is an anomaly
        latest_anomaly = predictions[-1] == -1
        
        # Calculate anomaly score
        anomaly_scores = iso_forest.score_samples(X)
        latest_score = anomaly_scores[-1]
        
        # Convert score to probability (lower score = higher anomaly probability)
        # Normalize to 0-1 range
        min_score = anomaly_scores.min()
        max_score = anomaly_scores.max()
        if max_score != min_score:
            normalized_score = (latest_score - min_score) / (max_score - min_score)
            probability = 1 - normalized_score  # Invert: lower score = higher probability
        else:
            probability = 0.5
        
        return {
            "alert": latest_anomaly,
            "probability": float(probability),
            "anomaly_score": float(latest_score)
        }
    
    def _cusum_detection(self, cases: np.ndarray) -> Dict[str, Any]:
        """
        CUSUM (Cumulative Sum) change detection
        
        Detects sustained increases in case counts
        """
        if len(cases) < self.window_size * 2:
            return {"alert": False, "probability": 0.0}
        
        # Calculate baseline mean and std
        baseline = cases[-self.window_size*2:-self.window_size]
        baseline_mean = np.mean(baseline)
        baseline_std = np.std(baseline)
        
        if baseline_std == 0:
            baseline_std = 1
        
        # Recent window
        recent = cases[-self.window_size:]
        
        # CUSUM calculation
        # S_i = max(0, S_{i-1} + (x_i - mean - k*std))
        k = 0.5  # Detection threshold multiplier
        S = 0
        max_S = 0
        
        for value in recent:
            S = max(0, S + (value - baseline_mean - k * baseline_std))
            max_S = max(max_S, S)
        
        # Alert threshold
        threshold = 3 * baseline_std * self.window_size
        
        alert = max_S > threshold
        
        # Probability based on how much threshold is exceeded
        if threshold > 0:
            probability = min(1.0, max_S / (threshold * 1.5))
        else:
            probability = 0.0
        
        return {
            "alert": alert,
            "probability": float(probability),
            "cusum_value": float(max_S),
            "threshold": float(threshold)
        }
    
    def _seasonal_anomaly_detection(self, cases: np.ndarray) -> Dict[str, Any]:
        """
        Seasonal anomaly detection
        
        Compares current pattern to historical seasonal patterns
        """
        if len(cases) < 30:
            return {"alert": False, "probability": 0.0}
        
        # Simple implementation: compare to same period in previous cycles
        # For weekly patterns, compare to same day of week
        current = cases[-7:].mean()
        
        # Compare to previous weeks
        if len(cases) >= 21:
            previous_weeks = cases[-21:-7].mean()
            
            if previous_weeks > 0:
                increase_ratio = (current - previous_weeks) / previous_weeks
                alert = increase_ratio > 0.5  # 50% increase
                probability = min(1.0, increase_ratio)
            else:
                alert = current > 0
                probability = 0.5 if alert else 0.0
        else:
            return {"alert": False, "probability": 0.0}
        
        return {
            "alert": alert,
            "probability": float(probability),
            "increase_ratio": float((current - previous_weeks) / previous_weeks) if previous_weeks > 0 else 0.0
        }
    
    def _determine_severity(
        self,
        probability: float,
        current_value: float,
        baseline_mean: float
    ) -> str:
        """Determine alert severity"""
        if probability >= 0.8 or (current_value > baseline_mean * 3):
            return "high"
        elif probability >= 0.6 or (current_value > baseline_mean * 2):
            return "moderate"
        else:
            return "low"
    
    def _generate_explanation(
        self,
        method_name: str,
        result: Dict[str, Any],
        cases: np.ndarray,
        country_name: str,
        disease_name: str
    ) -> str:
        """Generate human-readable explanation"""
        current = int(cases[-1])
        baseline_mean = float(cases[-self.window_size:-1].mean())
        
        if method_name == "baseline":
            z_score = result.get("z_score", 0)
            return (
                f"Outbreak signal detected in {country_name} for {disease_name}. "
                f"Current daily cases ({current}) exceed baseline average ({baseline_mean:.1f}) "
                f"by {z_score:.2f} standard deviations."
            )
        elif method_name == "isolation_forest":
            return (
                f"Anomaly detected in {country_name} for {disease_name} using Isolation Forest. "
                f"Current daily cases ({current}) are significantly different from recent patterns."
            )
        elif method_name == "cusum":
            cusum_val = result.get("cusum_value", 0)
            return (
                f"Sustained increase detected in {country_name} for {disease_name} using CUSUM. "
                f"Cumulative sum of deviations ({cusum_val:.1f}) indicates ongoing upward trend."
            )
        elif method_name == "seasonal":
            ratio = result.get("increase_ratio", 0)
            return (
                f"Seasonal anomaly detected in {country_name} for {disease_name}. "
                f"Current cases ({current}) show {ratio*100:.1f}% increase compared to previous periods."
            )
        else:
            return f"Outbreak signal detected in {country_name} for {disease_name}."
