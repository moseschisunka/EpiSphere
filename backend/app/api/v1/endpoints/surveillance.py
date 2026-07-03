from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.v1.deps import allow_clinician, allow_admin
from app.core.database import get_db
from app.db.models import User
from app.services.syndromic_service import SyndromicService
from app.services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/syndromes/trends")
def get_syndromic_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Get national syndromic trends"""
    if days < 1:
        raise HTTPException(status_code=400, detail="Days must be greater than 0")
    
    try:
        # Ideally should be scoped by facility for Clinician, National for Admin/Epi
        # For MVP, returning national trends
        return SyndromicService.get_national_trends(db, days)
    except Exception as e:
        # Log the error here in a real app
        raise HTTPException(status_code=500, detail="Failed to fetch syndromic trends")

@router.get("/heatmap")
def get_facility_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Get facility heatmap data"""
    # Privacy: Aggregated counts only.
    return DashboardService.get_facility_heatmap(db)
