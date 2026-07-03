"""Report schemas"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import date, datetime
from app.db.models import ReportType


class ReportBase(BaseModel):
    title: str
    report_type: ReportType
    country_id: Optional[int] = None
    disease_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    file_format: str = "pdf"
    report_metadata: Optional[Dict[str, Any]] = None


class ReportCreate(ReportBase):
    pass


class ReportResponse(ReportBase):
    id: int
    file_path: Optional[str] = None
    generated_by: int
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReportRequest(BaseModel):
    """Request to generate a report"""
    report_type: ReportType
    title: str
    country_id: Optional[int] = None
    disease_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    file_format: str = "pdf"  # pdf, docx, csv

