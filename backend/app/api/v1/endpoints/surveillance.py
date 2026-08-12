from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import allow_clinician, allow_admin
from app.core.database import get_db
from app.db.models import User
from app.services.syndromic_service import SyndromicService
from app.services.dashboard_service import DashboardService
from app.schemas.operational import FacilityHeatmapPointResponse, SyndromicTrendResponse

router = APIRouter()

@router.get("/syndromes/trends", response_model=List[SyndromicTrendResponse])
def get_syndromic_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Get national syndromic trends"""
    if days < 1:
        raise HTTPException(status_code=400, detail="Days must be greater than 0")
    
    try:
        role = (current_user.role.name if current_user.role else "").lower()
        facility_id = None
        if role != "admin":
            if not current_user.facility_id:
                raise HTTPException(status_code=403, detail="User is not assigned to a facility")
            facility_id = current_user.facility_id
        return SyndromicService.get_national_trends(db, days, facility_id=facility_id)
    except Exception as e:
        # Log the error here in a real app
        raise HTTPException(status_code=500, detail="Failed to fetch syndromic trends")

@router.get("/heatmap", response_model=List[FacilityHeatmapPointResponse])
def get_facility_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Get facility heatmap data"""
    role = (current_user.role.name if current_user.role else "").lower()
    facility_id = None
    if role != "admin":
        if not current_user.facility_id:
            raise HTTPException(status_code=403, detail="User is not assigned to a facility")
        facility_id = current_user.facility_id
    # Privacy: aggregated counts only, scoped to the operator's facility.
    return DashboardService.get_facility_heatmap(db, facility_id=facility_id)
