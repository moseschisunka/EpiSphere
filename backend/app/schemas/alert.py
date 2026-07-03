"""Alert schemas"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.db.models import AlertSeverity, AlertStatus


class AlertBase(BaseModel):
    country_id: int
    disease_id: int
    severity: AlertSeverity
    probability_score: float
    detection_method: str
    explanation: str


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    triggered_at: datetime
    investigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    investigated_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    country_name: Optional[str] = None
    disease_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    resolution_notes: Optional[str] = None


class AlertFilter(BaseModel):
    """Filter parameters for alert queries"""
    country_id: Optional[int] = None
    disease_id: Optional[int] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

