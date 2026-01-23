"""Case data endpoints"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import Case, Country, Disease, User, AuditLog, AuditAction
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate, CaseBulkUpload, CaseStats
from app.services.case_service import CaseService
from app.services.data_upload import DataUploadService

router = APIRouter()


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    country_id: Optional[int] = None,
    disease_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 1000,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List cases with filters"""
    query = db.query(Case)
    
    if country_id:
        query = query.filter(Case.country_id == country_id)
    if disease_id:
        query = query.filter(Case.disease_id == disease_id)
    if start_date:
        query = query.filter(Case.date >= start_date)
    if end_date:
        query = query.filter(Case.date <= end_date)
    
    cases = query.order_by(Case.date.desc()).offset(skip).limit(limit).all()
    return cases


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new case record"""
    # Verify country and disease exist
    country = db.query(Country).filter(Country.id == case_data.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    disease = db.query(Disease).filter(Disease.id == case_data.disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    # Check if case already exists for this date
    existing = db.query(Case).filter(
        and_(
            Case.country_id == case_data.country_id,
            Case.disease_id == case_data.disease_id,
            Case.date == case_data.date
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case record already exists for this date"
        )
    
    # Create case
    new_case = Case(**case_data.dict())
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="case",
        resource_id=new_case.id,
        details={"country_id": case_data.country_id, "disease_id": case_data.disease_id}
    )
    db.add(audit_log)
    db.commit()
    
    return new_case


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_cases(
    file: UploadFile = File(...),
    country_id: int = None,
    disease_id: int = None,
    current_user: User = Depends(require_role(["country_data_officer", "admin", "epidemiologist"])),
    db: Session = Depends(get_db)
):
    """Upload cases from CSV/Excel file"""
    if not country_id or not disease_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="country_id and disease_id are required"
        )
    
    upload_service = DataUploadService(db)
    result = await upload_service.upload_file(
        file=file,
        country_id=country_id,
        disease_id=disease_id,
        user_id=current_user.id
    )
    
    return result


@router.get("/stats", response_model=List[CaseStats])
async def get_case_stats(
    country_id: Optional[int] = None,
    disease_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get case statistics for dashboard"""
    service = CaseService(db)
    stats = service.get_case_stats(
        country_id=country_id,
        disease_id=disease_id,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get case by ID"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_update: CaseUpdate,
    current_user: User = Depends(require_role(["country_data_officer", "admin", "epidemiologist"])),
    db: Session = Depends(get_db)
):
    """Update case record"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Update fields
    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="case",
        resource_id=case_id,
        details=update_data
    )
    db.add(audit_log)
    db.commit()
    
    return case
