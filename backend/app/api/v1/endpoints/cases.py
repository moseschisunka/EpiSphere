"""Case data endpoints"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.core.dependencies import (
    apply_country_scope,
    enforce_country_scope,
    get_current_active_user,
    get_user_country_scope,
    require_role,
)
from app.db.models import Case, Country, Disease, User, AuditLog, AuditAction, ImportBatch, ImportRowError, ImportStatus, SourceSystem
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate, CaseBulkUpload, CaseStats, CaseUploadResult
from app.schemas.operational import ImportBatchDetailResponse
from app.services.case_service import CaseService
from app.services.data_upload import DataUploadService
from app.services.ingestion_lineage import create_import_batch, get_or_create_source_system

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
    query = apply_country_scope(db.query(Case), Case, current_user)
    
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
    enforce_country_scope(current_user, case_data.country_id)
    country = db.query(Country).filter(Country.id == case_data.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    disease = db.query(Disease).filter(Disease.id == case_data.disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    source_system = None
    if case_data.source_system_id:
        source_system = db.query(SourceSystem).filter(SourceSystem.id == case_data.source_system_id).first()
        if not source_system:
            raise HTTPException(status_code=404, detail="Source system not found")
    else:
        source_system = get_or_create_source_system(
            db,
            code="manual_case_entry",
            name="Manual case entry",
            system_type="manual_entry",
        )

    source_record_id = case_data.source_record_id or (
        f"manual-case:{source_system.code}:{case_data.country_id}:"
        f"{case_data.disease_id}:{case_data.date.isoformat()}"
    )

    # Check idempotency before creating the batch envelope. Callers that need
    # multiple observations for the same date must supply distinct source IDs.
    existing = db.query(Case).filter(
        and_(
            Case.source_system_id == source_system.id,
            Case.source_record_id == source_record_id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case record already exists for this source record",
        )

    batch = create_import_batch(
        db,
        filename="manual_case_entry",
        dataset_type="case_timeseries",
        source_system=source_system,
        uploaded_by=current_user.id,
        country_id=case_data.country_id,
        disease_id=case_data.disease_id,
        rows_total=1,
        metadata={"entry_mode": "single_case", "source_record_id": source_record_id},
        status=ImportStatus.COMMITTED,
    )

    # Create case
    case_values = case_data.dict(exclude={"source_system_id", "source_record_id", "import_batch_id"})
    new_case = Case(
        **case_values,
        source_system_id=source_system.id,
        source_record_id=source_record_id,
        import_batch_id=batch.id,
    )
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


@router.post("/upload", response_model=CaseUploadResult, status_code=status.HTTP_201_CREATED)
async def upload_cases(
    file: UploadFile = File(...),
    country_id: int = Form(...),
    disease_id: int = Form(...),
    commit: bool = Form(True),
    source_system_code: str = Form("manual_upload"),
    current_user: User = Depends(require_role(["country_data_officer", "admin", "epidemiologist"])),
    db: Session = Depends(get_db)
):
    """Upload cases from CSV/Excel file"""
    enforce_country_scope(current_user, country_id)
    upload_service = DataUploadService(db)
    result = await upload_service.upload_file(
        file=file,
        country_id=country_id,
        disease_id=disease_id,
        user_id=current_user.id,
        commit=commit,
        source_system_code=source_system_code,
    )
    
    return result


@router.get("/imports/{batch_id}", response_model=ImportBatchDetailResponse)
async def get_import_batch(
    batch_id: int,
    current_user: User = Depends(require_role(["country_data_officer", "admin", "epidemiologist"])),
    db: Session = Depends(get_db),
):
    """Return import lineage, quality summary, and row-level issues for an upload batch."""
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    if batch.country_id is not None:
        enforce_country_scope(current_user, batch.country_id)

    issues = db.query(ImportRowError).filter(ImportRowError.batch_id == batch_id).order_by(ImportRowError.row_number).all()
    return {
        "id": batch.id,
        "filename": batch.filename,
        "dataset_type": batch.dataset_type,
        "status": batch.status.value if batch.status else None,
        "rows_total": batch.rows_total,
        "rows_valid": batch.rows_valid,
        "rows_committed": batch.rows_committed,
        "error_count": batch.error_count,
        "warning_count": batch.warning_count,
        "quality_score": batch.quality_score,
        "uploaded_at": batch.uploaded_at,
        "committed_at": batch.committed_at,
        "metadata": batch.batch_metadata or {},
        "issues": [
            {
                "row_number": issue.row_number,
                "field_name": issue.field_name,
                "severity": issue.severity.value if issue.severity else None,
                "message": issue.message,
                "raw_value": issue.raw_value,
            }
            for issue in issues
        ],
    }


@router.post("/imports/{batch_id}/commit", response_model=CaseUploadResult)
async def commit_validated_import_batch(
    batch_id: int,
    current_user: User = Depends(require_role(["country_data_officer", "admin", "epidemiologist"])),
    db: Session = Depends(get_db),
):
    """Commit a previously validated upload after the officer has reviewed its issues and checks."""
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    if batch.country_id is not None:
        enforce_country_scope(current_user, batch.country_id)
    return DataUploadService(db).commit_validated_batch(batch_id=batch_id, user_id=current_user.id)


@router.get("/stats", response_model=List[CaseStats])
async def get_case_stats(
    country_id: Optional[int] = None,
    disease_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get case statistics for dashboard"""
    scoped_country_id = get_user_country_scope(current_user)
    if scoped_country_id is not None:
        if country_id is not None:
            enforce_country_scope(current_user, country_id)
        country_id = scoped_country_id
    elif current_user.role and current_user.role.name in {"country_data_officer", "facility_admin", "clinician", "pharmacist"}:
        enforce_country_scope(current_user, 0)
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
    case = apply_country_scope(db.query(Case).filter(Case.id == case_id), Case, current_user).first()
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
    case = apply_country_scope(db.query(Case).filter(Case.id == case_id), Case, current_user).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Update fields
    update_data = case_update.dict(exclude_unset=True)
    if "country_id" in update_data:
        enforce_country_scope(current_user, update_data["country_id"])
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
