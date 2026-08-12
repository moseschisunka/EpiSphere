from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import allow_admin, allow_facility_admin, get_current_active_user
from app.core.database import get_db
from app.core.dependencies import apply_facility_scope, enforce_facility_scope, require_role
from app.db.models import User, Facility
from app.schemas import facility as schemas
from app.schemas.operational import FacilityConsentResponse
from app.schemas.user import UserResponse

router = APIRouter()

@router.post("/", response_model=schemas.Facility)
def create_facility(
    facility_in: schemas.FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """Create a new health facility"""
    facility = Facility(**facility_in.dict())
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility

@router.get("/", response_model=List[schemas.Facility])
def list_facilities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "facility_admin"]))
):
    """List only facilities within the administrator's authorized scope."""
    query = apply_facility_scope(db.query(Facility), Facility, current_user)
    return query.offset(skip).limit(min(limit, 100)).all()


@router.get("/{facility_id}/staff", response_model=List[UserResponse])
def list_facility_staff(
    facility_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "facility_admin"])),
):
    """List staff assigned to an authorized facility without exposing passwords."""
    enforce_facility_scope(current_user, facility_id)
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return db.query(User).filter(User.facility_id == facility_id).order_by(User.full_name, User.username).all()

@router.get("/{facility_id}", response_model=schemas.Facility)
def get_facility(
    facility_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "facility_admin"]))
):
    """Get facility details"""
    enforce_facility_scope(current_user, facility_id)
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@router.put("/{facility_id}/consent", response_model=FacilityConsentResponse)
def update_facility_consent(
    facility_id: int,
    public_visible: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_facility_admin)
):
    """
    Update facility public data sharing consent.
    Facility Admin only.
    """
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
        
    # Check if user belongs to this facility
    if current_user.facility_id != facility.id and current_user.role.name != "admin":
         raise HTTPException(status_code=403, detail="Not authorized for this facility")
         
    facility.public_visible = public_visible
    db.commit()
    return {"status": "success", "public_visible": facility.public_visible}
