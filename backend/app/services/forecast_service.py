"""Forecast generation service"""

from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import Forecast, Case, Country, Disease
from app.ml.forecasting import ForecastingPipeline


class ForecastService:
    """Service for generating forecasts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.forecasting_pipeline = ForecastingPipeline()
    
    async def generate_forecast(
        self,
        country_id: int,
        disease_id: int,
        horizon_days: int = 30,
        model_type: Optional[str] = None
    ) -> Forecast:
        """Generate a forecast"""
        
        # Verify country and disease exist
        country = self.db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise ValueError("Country not found")
        
        disease = self.db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            raise ValueError("Disease not found")
        
        # Get historical case data
        cases = self.db.query(Case).filter(
            and_(
                Case.country_id == country_id,
                Case.disease_id == disease_id
            )
        ).order_by(Case.date).all()
        
        if len(cases) < 30:  # Need at least 30 days of data
            raise ValueError("Insufficient historical data. Need at least 30 days.")
        
        # Prepare data for forecasting
        dates = [c.date for c in cases]
        values = [c.daily_cases for c in cases]
        
        # Generate forecast
        forecast_result = await self.forecasting_pipeline.generate_forecast(
            dates=dates,
            values=values,
            horizon_days=horizon_days,
            model_type=model_type
        )
        
        # Create forecast record
        forecast = Forecast(
            country_id=country_id,
            disease_id=disease_id,
            forecast_date=date.today(),
            model_type=forecast_result["model_type"],
            horizon_days=horizon_days,
            forecast_data=forecast_result["forecast_data"],
            accuracy_metrics=forecast_result.get("accuracy_metrics")
        )
        
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)
        
        return forecast
