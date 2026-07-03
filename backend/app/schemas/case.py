"""Case schemas"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import date, datetime


class CaseBase(BaseModel):
    country_id: int
    disease_id: int
    date: date
    daily_cases: int = 0
    cumulative_cases: int = 0
    daily_deaths: int = 0
    cumulative_deaths: int = 0
    daily_recovered: Optional[int] = None
    cumulative_recovered: Optional[int] = None
    subnational_region: Optional[str] = None
    source: Optional[str] = None
    source_system_id: Optional[int] = None
    import_batch_id: Optional[int] = None
    reporting_period_start: Optional[date] = None
    reporting_period_end: Optional[date] = None
    reporting_level: Optional[str] = None
    case_definition: Optional[str] = None
    confirmation_status: Optional[str] = None
    data_quality_score: Optional[float] = None
    notes: Optional[str] = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    daily_cases: Optional[int] = None
    cumulative_cases: Optional[int] = None
    daily_deaths: Optional[int] = None
    cumulative_deaths: Optional[int] = None
    daily_recovered: Optional[int] = None
    cumulative_recovered: Optional[int] = None
    notes: Optional[str] = None


class CaseResponse(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CaseBulkUpload(BaseModel):
    """Schema for bulk case upload"""
    country_id: int
    disease_id: int
    cases: list[CaseCreate]


class CaseStats(BaseModel):
    """Case statistics for dashboard"""
    country_id: int
    country_name: str
    disease_id: int
    disease_name: str
    date: date
    daily_cases: int
    cumulative_cases: int
    daily_deaths: int
    cumulative_deaths: int
    incidence_per_100k: Optional[float] = None
    cfr: Optional[float] = None  # Case Fatality Rate
    growth_rate: Optional[float] = None  # 7-day growth rate



class UploadRowIssue(BaseModel):
    row_number: int
    field_name: Optional[str] = None
    severity: str
    message: str
    raw_value: Optional[str] = None


class UploadQualityCheck(BaseModel):
    check_name: str
    severity: str
    passed: bool
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    message: Optional[str] = None


class CaseUploadResult(BaseModel):
    success: bool
    committed: bool
    batch_id: int
    status: str
    rows_total: int
    rows_valid: int
    rows_committed: int
    error_count: int
    warning_count: int
    quality_score: Optional[float] = None
    errors: list[str] = []
    issues: list[UploadRowIssue] = []
    quality_checks: list[UploadQualityCheck] = []
    message: str
    metadata: dict[str, Any] = {}
