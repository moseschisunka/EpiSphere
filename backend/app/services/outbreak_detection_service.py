"""Service for running outbreak detection on case data"""

from typing import List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import Case, Country, Disease, Alert, AlertStatus, AlertSeverity
from app.ml.outbreak_detection import OutbreakDetectionEngine


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
        
        # Create alert if triggered
        if detection_result.get("alert_triggered"):
            # Check if alert already exists for today
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.country_id == country_id,
                    Alert.disease_id == disease_id,
                    Alert.triggered_at >= date.today()
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
                    explanation=detection_result["explanation"]
                )
                
                self.db.add(alert)
                self.db.commit()
                
                detection_result["alert_id"] = alert.id
        
        return detection_result
