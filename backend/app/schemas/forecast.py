"""Forecast schemas"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional, Dict, Any
from datetime import date, datetime


class ForecastBase(BaseModel):
    country_id: int = Field(..., gt=0)
    disease_id: int = Field(..., gt=0)
    forecast_date: date
    model_type: str
    horizon_days: int
    forecast_data: Dict[str, Any]
    accuracy_metrics: Optional[Dict[str, Any]] = None


class ForecastCreate(ForecastBase):
    pass


class ForecastResponse(ForecastBase):
    id: int
    created_at: datetime
    country_name: Optional[str] = None
    disease_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ForecastRequest(BaseModel):
    """Request to generate a forecast"""
    country_id: int = Field(..., gt=0)
    disease_id: int = Field(..., gt=0)
    horizon_days: int = Field(default=30, ge=1, le=90)
    model_type: Optional[Literal["seasonal_naive", "simple_trend", "exp_smoothing", "arima", "prophet"]] = None

