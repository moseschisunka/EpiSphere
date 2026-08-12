"""Service for running outbreak detection on case data"""

from typing import List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import Case, Country, Disease, Alert, AlertStatus, AlertSeverity, Forecast
from app.ml.outbreak_detection import OutbreakDetectionEngine
from app.core.config import settings


class OutbreakDetectionService:
    """Service for automated outbreak detection"""
    
    def __init__(self, db: Session):
        self.db = db
        self.detection_engine = OutbreakDetectionEngine(window_size=14)
    
    def run_detection_for_all_countries(self) -> List[dict]:
        """Run outbreak detection for all country-disease combinations"""
        results = []
        
        # Get all active diseases
        diseases = self.db.query(Disease).filter(Disease.is_active == True).all()
        
        # Get all countries
        countries = self.db.query(Country).all()
        
        for disease in diseases:
            for country in countries:
                try:
                    result = self.run_detection(country.id, disease.id)
                    if result and result.get("alert_triggered"):
                        results.append(result)
                except Exception as e:
                    # Log error but continue
                    print(f"Error detecting outbreak for {country.name} - {disease.name}: {str(e)}")
                    continue
        
        return results
    
    def run_detection(self, country_id: int, disease_id: int) -> dict:
        """Run outbreak detection for a specific country-disease combination"""
        # Get recent case data (last 60 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=60)
        
        cases = self.db.query(Case).filter(
            and_(
                Case.country_id == country_id,
                Case.disease_id == disease_id,
                Case.date >= start_date,
                Case.date <= end_date
            )
        ).order_by(Case.date).all()
        
        if len(cases) < 30:
            return {"alert_triggered": False, "reason": "insufficient_data"}
        
        # Extract dates and values
        dates = [c.date for c in cases]
        daily_cases = [c.daily_cases for c in cases]
        
        # Get country and disease names
        country = self.db.query(Country).filter(Country.id == country_id).first()
        disease = self.db.query(Disease).filter(Disease.id == disease_id).first()
        
        country_name = country.name if country else ""
        disease_name = disease.name if disease else ""
        
        # Run detection
        detection_result = self.detection_engine.detect_outbreak(
            dates=dates,
            daily_cases=daily_cases,
            country_name=country_name,
            disease_name=disease_name
        )
        
        interval_alert = self._forecast_interval_exceedance(country_id, disease_id, cases)
        if interval_alert:
            detection_result = self._merge_interval_alert(detection_result, interval_alert)

        # Create alert if triggered
        if detection_result.get("alert_triggered"):
            # Check if alert already exists for today
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.country_id == country_id,
                    Alert.disease_id == disease_id,
                    Alert.triggered_at >= datetime.utcnow() - timedelta(hours=settings.ALERT_SUPPRESSION_HOURS)
                )
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    country_id=country_id,
                    disease_id=disease_id,
                    severity=AlertSeverity(detection_result["severity"]),
                    status=AlertStatus.TRIGGERED,
                    probability_score=detection_result["probability_score"],
                    detection_method=detection_result["detection_method"],
                    explanation=detection_result["explanation"],
                    detection_metadata={
                        "method_results": detection_result.get("method_results", {}),
                        "metadata": detection_result.get("metadata", {}),
                        "model_version": detection_result.get("metadata", {}).get("model_version", "outbreak_detection_engine_v2"),
                    }
                )
                
                self.db.add(alert)
                self.db.commit()
                
                detection_result["alert_id"] = alert.id
        
        return detection_result

    def _forecast_interval_exceedance(self, country_id: int, disease_id: int, cases: List[Case]) -> dict | None:
        """Detect observed case counts repeatedly exceeding the latest forecast interval."""
        latest_forecast = self.db.query(Forecast).filter(
            Forecast.country_id == country_id,
            Forecast.disease_id == disease_id,
        ).order_by(Forecast.created_at.desc()).first()
        if not latest_forecast or not latest_forecast.forecast_data:
            return None

        forecast_data = latest_forecast.forecast_data
        dates = forecast_data.get("dates", [])
        upper = forecast_data.get("upper_bound", [])
        if not dates or not upper:
            return None

        upper_by_date = dict(zip(dates, upper))
        exceedances = []
        for case in cases[-14:]:
            key = case.date.isoformat()
            if key in upper_by_date and case.daily_cases > upper_by_date[key]:
                exceedances.append({
                    "date": key,
                    "observed": case.daily_cases,
                    "upper_bound": upper_by_date[key],
                })

        if len(exceedances) < 2:
            return None

        probability = min(1.0, 0.45 + 0.15 * len(exceedances))
        severity = "high" if len(exceedances) >= 4 else "moderate"
        return {
            "alert_triggered": True,
            "severity": severity,
            "probability_score": probability,
            "detection_method": "forecast_interval_exceedance",
            "explanation": f"Observed cases exceeded the forecast upper prediction interval on {len(exceedances)} recent day(s). Recommended action: review reporting quality and investigate whether transmission is accelerating.",
            "method_results": {
                "forecast_interval_exceedance": {
                    "alert": True,
                    "probability": probability,
                    "exceedance_count": len(exceedances),
                    "forecast_id": latest_forecast.id,
                }
            },
            "metadata": {
                "forecast_id": latest_forecast.id,
                "exceedances": exceedances,
                "model_version": "forecast_interval_monitor_v1",
            },
        }

    def _merge_interval_alert(self, detection_result: dict, interval_alert: dict) -> dict:
        if not detection_result.get("alert_triggered"):
            return interval_alert
        detection_result.setdefault("method_results", {}).update(interval_alert.get("method_results", {}))
        detection_result.setdefault("metadata", {}).setdefault("forecast_interval_monitor", interval_alert.get("metadata", {}))
        detection_result["probability_score"] = max(detection_result.get("probability_score", 0.0), interval_alert["probability_score"])
        if detection_result.get("severity") != "high":
            detection_result["severity"] = interval_alert["severity"]
        detection_result["explanation"] = detection_result["explanation"] + " " + interval_alert["explanation"]
        return detection_result

