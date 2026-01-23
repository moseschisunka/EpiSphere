from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.api.v1.deps import allow_admin
from app.core.database import get_db
from app.db.models import User, InteropLog
from app.services.interop_service import InteropService

router = APIRouter()

@router.post("/dhis2/sync")
def trigger_dhis2_sync(
    dataset: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """Trigger manual sync to DHIS2"""
    success = InteropService.sync_to_dhis2(db, current_user, payload, dataset)
    if not success:
         raise HTTPException(status_code=500, detail="Sync failed. Check logs.")
    return {"status": "success", "message": "Synced to DHIS2"}

@router.get("/logs")
def get_interop_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """View interop logs"""
    return db.query(InteropLog).order_by(InteropLog.timestamp.desc()).offset(skip).limit(limit).all()
