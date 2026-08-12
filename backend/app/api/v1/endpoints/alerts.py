"""Alert endpoints"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.db.models import Alert, AlertNotification, NotificationStatus, AlertStatus, User, AuditLog, AuditAction
from app.schemas.alert import AlertNotificationResponse, AlertResponse, AlertReviewUpdate, AlertUpdate, AlertFilter
from app.services.notification_service import AlertNotificationService

router = APIRouter()
allow_alert_response = require_role(["admin", "epidemiologist", "facility_admin"])


@router.get("/notifications", response_model=List[AlertNotificationResponse])
async def list_alert_notifications(
    status_filter: Optional[NotificationStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(allow_alert_response),
    db: Session = Depends(get_db),
):
    """List durable response-notification deliveries for operators."""
    query = db.query(AlertNotification).order_by(AlertNotification.created_at.desc())
    if status_filter:
        query = query.filter(AlertNotification.status == status_filter)
    return query.offset(skip).limit(min(limit, 500)).all()


@router.post("/notifications/{notification_id}/retry", response_model=AlertNotificationResponse)
async def retry_alert_notification(
    notification_id: int,
    current_user: User = Depends(allow_alert_response),
    db: Session = Depends(get_db),
):
    """Requeue a failed delivery without changing the alert lifecycle."""
    notification = db.query(AlertNotification).filter(AlertNotification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.status != NotificationStatus.FAILED:
        raise HTTPException(status_code=409, detail="Only failed notifications can be retried")
    notification.status = NotificationStatus.PENDING
    notification.error = None
    notification.next_attempt_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="alert_notification",
        resource_id=notification.id,
        details={"action": "retry", "alert_id": notification.alert_id},
    ))
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    country_id: Optional[int] = None,
    disease_id: Optional[int] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(allow_alert_response),
    db: Session = Depends(get_db)
):
    """List alerts with filters"""
    query = db.query(Alert)
    
    if country_id:
        query = query.filter(Alert.country_id == country_id)
    if disease_id:
        query = query.filter(Alert.disease_id == disease_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    
    alerts = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit).all()
    
    # Add country and disease names
    result = []
    for alert in alerts:
        alert_dict = {
            **{c.name: getattr(alert, c.name) for c in alert.__table__.columns},
            "country_name": alert.country.name if alert.country else None,
            "disease_name": alert.disease.name if alert.disease else None
        }
        result.append(AlertResponse(**alert_dict))
    
    return result


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(allow_alert_response),
    db: Session = Depends(get_db)
):
    """Get alert by ID"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert_dict = {
        **{c.name: getattr(alert, c.name) for c in alert.__table__.columns},
        "country_name": alert.country.name if alert.country else None,
        "disease_name": alert.disease.name if alert.disease else None
    }
    return AlertResponse(**alert_dict)


@router.post("/{alert_id}/review", response_model=AlertResponse)
async def review_alert(
    alert_id: int,
    review_update: AlertReviewUpdate,
    current_user: User = Depends(allow_alert_response),
    db: Session = Depends(get_db),
):
    """Record an epidemiologist or administrator's human review decision."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.review_status = review_update.review_status
    alert.reviewed_by = current_user.id
    alert.reviewed_at = datetime.utcnow()
    alert.review_notes = review_update.review_notes
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="alert_review",
        resource_id=alert_id,
        details={
            "review_status": review_update.review_status.value,
            "review_notes_updated": review_update.review_notes is not None,
        },
    ))
    db.commit()
    db.refresh(alert)
    alert_dict = {
        **{c.name: getattr(alert, c.name) for c in alert.__table__.columns},
        "country_name": alert.country.name if alert.country else None,
        "disease_name": alert.disease.name if alert.disease else None,
    }
    return AlertResponse(**alert_dict)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user: User = Depends(allow_alert_response),
    db: Session = Depends(get_db)
):
    """Resolve or update alert status"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    previous_status = alert.status
    allowed_transitions = {
        AlertStatus.TRIGGERED: {
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.INVESTIGATING,
            AlertStatus.ESCALATED,
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
        },
        AlertStatus.ACKNOWLEDGED: {
            AlertStatus.INVESTIGATING,
            AlertStatus.ESCALATED,
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
        },
        AlertStatus.INVESTIGATING: {
            AlertStatus.ESCALATED,
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
        },
        AlertStatus.ESCALATED: {AlertStatus.INVESTIGATING, AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE},
        AlertStatus.RESOLVED: {AlertStatus.INVESTIGATING, AlertStatus.CLOSED},
        AlertStatus.FALSE_POSITIVE: {AlertStatus.INVESTIGATING, AlertStatus.CLOSED},
        AlertStatus.CLOSED: set(),
    }
    if alert_update.status:
        if alert_update.status != previous_status and alert_update.status not in allowed_transitions.get(previous_status, set()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Alert status cannot transition from {previous_status.value} to {alert_update.status.value}",
            )
        alert.status = alert_update.status

        if alert_update.status == AlertStatus.ACKNOWLEDGED:
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = current_user.id
        elif alert_update.status == AlertStatus.INVESTIGATING:
            if previous_status in {AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE}:
                alert.reopened_at = datetime.utcnow()
            alert.investigated_at = datetime.utcnow()
            alert.investigated_by = current_user.id
        elif alert_update.status == AlertStatus.ESCALATED:
            alert.escalated_at = datetime.utcnow()
            alert.escalated_by = current_user.id
            AlertNotificationService.enqueue_escalation(db, alert)
        elif alert_update.status in [AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE]:
            alert.resolved_at = datetime.utcnow()
        elif alert_update.status == AlertStatus.CLOSED:
            alert.closed_at = datetime.utcnow()

    if alert_update.assigned_to is not None:
        assignee = db.query(User).filter(User.id == alert_update.assigned_to, User.is_active.is_(True)).first()
        if not assignee:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user is not active or does not exist")
        alert.assigned_to = assignee.id
    
    if alert_update.resolution_notes:
        alert.resolution_notes = alert_update.resolution_notes
    
    db.commit()
    db.refresh(alert)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="alert",
        resource_id=alert_id,
        details={
            "previous_status": previous_status.value if previous_status else None,
            "status": alert.status.value if alert.status else None,
            "assigned_to": alert.assigned_to,
            "resolution_notes_updated": alert_update.resolution_notes is not None,
        }
    )
    db.add(audit_log)
    db.commit()
    
    alert_dict = {
        **{c.name: getattr(alert, c.name) for c in alert.__table__.columns},
        "country_name": alert.country.name if alert.country else None,
        "disease_name": alert.disease.name if alert.disease else None
    }
    return AlertResponse(**alert_dict)
