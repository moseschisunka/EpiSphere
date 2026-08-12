"""Report generation endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import apply_country_scope, enforce_country_scope, is_admin_user, require_role
from app.db.models import Report, User
from app.schemas.report import ReportRequest, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    report_request: ReportRequest,
    current_user: User = Depends(require_role(["epidemiologist", "admin", "country_data_officer"])),
    db: Session = Depends(get_db)
):
    """Generate a report"""
    if report_request.country_id is None and not is_admin_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Country-scoped reports require a country")
    if report_request.country_id is not None:
        enforce_country_scope(current_user, report_request.country_id)
    service = ReportService(db)
    
    try:
        report = await service.generate_report(
            report_type=report_request.report_type,
            title=report_request.title,
            country_id=report_request.country_id,
            disease_id=report_request.disease_id,
            start_date=report_request.start_date,
            end_date=report_request.end_date,
            file_format=report_request.file_format,
            user_id=current_user.id
        )
        
        return ReportResponse(
            id=report.id,
            title=report.title,
            report_type=report.report_type,
            country_id=report.country_id,
            disease_id=report.disease_id,
            start_date=report.start_date,
            end_date=report.end_date,
            file_path=report.file_path,
            file_format=report.file_format,
            generated_by=report.generated_by,
            generated_at=report.generated_at,
            report_metadata=report.report_metadata
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["epidemiologist", "admin", "country_data_officer"])),
    db: Session = Depends(get_db)
):
    """List reports"""
    reports = apply_country_scope(db.query(Report), Report, current_user).order_by(Report.generated_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ReportResponse(
            id=r.id,
            title=r.title,
            report_type=r.report_type,
            country_id=r.country_id,
            disease_id=r.disease_id,
            start_date=r.start_date,
            end_date=r.end_date,
            file_path=r.file_path,
            file_format=r.file_format,
            generated_by=r.generated_by,
            generated_at=r.generated_at,
            report_metadata=r.report_metadata
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(require_role(["epidemiologist", "admin", "country_data_officer"])),
    db: Session = Depends(get_db)
):
    """Get report by ID"""
    report = apply_country_scope(
        db.query(Report).filter(Report.id == report_id), Report, current_user
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(
        id=report.id,
        title=report.title,
        report_type=report.report_type,
        country_id=report.country_id,
        disease_id=report.disease_id,
        start_date=report.start_date,
        end_date=report.end_date,
        file_path=report.file_path,
        file_format=report.file_format,
        generated_by=report.generated_by,
        generated_at=report.generated_at,
        report_metadata=report.report_metadata
    )
