"""Forecast schemas"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, datetime


class ForecastBase(BaseModel):
    country_id: int
    disease_id: int
    forecast_date: date
    model_type: str
    horizon_days: int
    forecast_data: Dict[str, Any]
    accuracy_metrics: Optional[Dict[str, float]] = None


class ForecastCreate(ForecastBase):
    pass


class ForecastResponse(ForecastBase):
    id: int
    created_at: datetime
    country_name: Optional[str] = None
    disease_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ForecastRequest(BaseModel):
    """Request to generate a forecast"""
    country_id: int
    disease_id: int
    horizon_days: int = 30
    model_type: Optional[str] = None  # If None, auto-select best model
