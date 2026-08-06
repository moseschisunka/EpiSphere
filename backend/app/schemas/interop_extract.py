from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class DataExtractFilter(BaseModel):
    disease_id: Optional[int] = None
    disease_name: Optional[str] = None
    country_id: Optional[int] = None
    iso_code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: Optional[str] = "json"  # json, fhir_aggregate


class AggregateCaseMetric(BaseModel):
    disease_name: str
    country_name: str
    iso_code: str
    date: str
    daily_cases: int
    daily_deaths: int
    daily_recovered: int
    cumulative_cases: int
    cumulative_deaths: int
    subnational_region: Optional[str] = None
    source: Optional[str] = None


class DataExtractResponse(BaseModel):
    status: str
    de_identified: bool = True
    total_records: int
    extracted_at: str
    metrics: List[AggregateCaseMetric]


class WebhookPayload(BaseModel):
    event_type: str
    source_system: str
    data: dict
