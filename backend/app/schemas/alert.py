"""Alert schemas"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime
from app.db.models import AlertSeverity, AlertStatus, NotificationStatus, ReviewStatus


class AlertBase(BaseModel):
    country_id: int
    disease_id: int
    severity: AlertSeverity
    probability_score: float
    detection_method: str
    explanation: str
    detection_metadata: Optional[dict[str, Any]] = None


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    triggered_at: datetime
    investigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    investigated_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    assigned_to: Optional[int] = None
    escalated_at: Optional[datetime] = None
    escalated_by: Optional[int] = None
    reopened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    review_status: ReviewStatus
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    investigation_notes: Optional[str] = None
    evidence_references: Optional[list[str]] = None
    resolution_notes: Optional[str] = None
    country_name: Optional[str] = None
    disease_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    assigned_to: Optional[int] = Field(default=None, gt=0)
    investigation_notes: Optional[str] = Field(default=None, max_length=2000)
    evidence_references: Optional[list[str]] = Field(default=None, max_length=20)
    resolution_notes: Optional[str] = Field(default=None, max_length=2000)


class AlertReviewUpdate(BaseModel):
    review_status: ReviewStatus
    review_notes: Optional[str] = Field(default=None, max_length=2000)


class AlertFilter(BaseModel):
    """Filter parameters for alert queries"""
    country_id: Optional[int] = None
    disease_id: Optional[int] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AlertNotificationResponse(BaseModel):
    id: int
    alert_id: int
    recipient_user_id: Optional[int] = None
    recipient_email: str
    channel: str
    event_type: str
    status: NotificationStatus
    attempts: int
    subject: str
    payload: dict[str, Any]
    error: Optional[str] = None
    created_at: datetime
    next_attempt_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

