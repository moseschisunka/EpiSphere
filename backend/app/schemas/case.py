"""Case schemas"""

from pydantic import BaseModel
from typing import Optional
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
    
    class Config:
        from_attributes = True


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
