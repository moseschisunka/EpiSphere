"""Alert endpoints"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import Alert, AlertStatus, User, AuditLog, AuditAction
from app.schemas.alert import AlertResponse, AlertUpdate, AlertFilter

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    country_id: Optional[int] = None,
    disease_id: Optional[int] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
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


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resolve or update alert status"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update status
    if alert_update.status:
        alert.status = alert_update.status
        
        if alert_update.status == AlertStatus.INVESTIGATING:
            alert.investigated_at = datetime.utcnow()
            alert.investigated_by = current_user.id
        elif alert_update.status in [AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE]:
            alert.resolved_at = datetime.utcnow()
    
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
        details={"status": alert.status.value if alert.status else None}
    )
    db.add(audit_log)
    db.commit()
    
    alert_dict = {
        **{c.name: getattr(alert, c.name) for c in alert.__table__.columns},
        "country_name": alert.country.name if alert.country else None,
        "disease_name": alert.disease.name if alert.disease else None
    }
    return AlertResponse(**alert_dict)
