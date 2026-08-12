"""Forecast generation service"""

from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta
import hashlib
import json
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

        # Persist a deterministic, queryable description of the exact input
        # population. This lets a reviewer reproduce a forecast even after a
        # later ingestion batch adds newer observations.
        accuracy_metrics = forecast_result.get("accuracy_metrics") or {}
        accuracy_metrics["input_provenance"] = self._input_provenance(cases)
        accuracy_metrics["evaluation_context"] = self._evaluation_context(
            country_id=country_id,
            disease_id=disease_id,
            preprocessing=accuracy_metrics.get("preprocessing") or {},
        )
        
        # Create forecast record
        forecast = Forecast(
            country_id=country_id,
            disease_id=disease_id,
            forecast_date=date.today(),
            model_type=forecast_result["model_type"],
            horizon_days=horizon_days,
            forecast_data=forecast_result["forecast_data"],
            accuracy_metrics=accuracy_metrics
        )
        
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)
        
        return forecast

    @staticmethod
    def _input_provenance(cases: list[Case]) -> Dict[str, Any]:
        """Return a stable fingerprint and lineage references for forecast inputs."""
        observations = [
            {
                "case_id": case.id,
                "date": case.date.isoformat(),
                "daily_cases": case.daily_cases,
                "source_system_id": case.source_system_id,
                "source_record_id": case.source_record_id,
                "import_batch_id": case.import_batch_id,
            }
            for case in cases
        ]
        canonical = json.dumps(observations, sort_keys=True, separators=(",", ":"), default=str)
        return {
            "observation_count": len(observations),
            "case_ids": [item["case_id"] for item in observations],
            "import_batch_ids": sorted({item["import_batch_id"] for item in observations if item["import_batch_id"] is not None}),
            "source_system_ids": sorted({item["source_system_id"] for item in observations if item["source_system_id"] is not None}),
            "history_start": observations[0]["date"],
            "history_end": observations[-1]["date"],
            "observations_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }

    @staticmethod
    def _evaluation_context(
        country_id: int,
        disease_id: int,
        preprocessing: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist the strata needed to compare forecast performance safely."""
        history_points = int(preprocessing.get("history_points") or 0)
        missing_days = int(preprocessing.get("missing_days") or 0)
        expected_days = history_points + missing_days
        completeness = history_points / expected_days if expected_days else None
        return {
            "country_id": country_id,
            "disease_id": disease_id,
            "data_volume_observations": history_points,
            "reporting_completeness": completeness,
            "missing_days": missing_days,
        }
