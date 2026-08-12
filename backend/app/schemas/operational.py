"""Stable response contracts for reference, operational, and public endpoints."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CountryResponse(BaseModel):
    id: int
    name: str
    iso_code: str
    iso_code_2: str | None = None
    region_id: int | None = None
    population: int | None = None
    latitude: float | None = None
    longitude: float | None = None


class DiseaseResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None = None
    biosafety_level: str | None = None
    is_active: bool


class LocationFacilityResponse(BaseModel):
    id: int
    name: str
    type: str
    province: str | None = None
    district: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class LocationCountryResponse(BaseModel):
    id: int
    name: str
    iso_code: str
    provinces: list[str]
    districts: list[str]
    facility_count: int
    facilities: list[LocationFacilityResponse]


class LocationHierarchyResponse(BaseModel):
    region_id: int
    region_name: str
    region_code: str
    countries: list[LocationCountryResponse]


class ProvincesResponse(BaseModel):
    country_id: int
    provinces: list[str]


class DistrictsResponse(BaseModel):
    country_id: int
    province: str
    districts: list[str]


class ImportRowIssueResponse(BaseModel):
    row_number: int
    field_name: str | None = None
    severity: str | None = None
    message: str
    raw_value: str | None = None


class ImportBatchDetailResponse(BaseModel):
    id: int
    filename: str
    dataset_type: str
    status: str | None = None
    rows_total: int
    rows_valid: int
    rows_committed: int
    error_count: int
    warning_count: int
    quality_score: float | None = None
    uploaded_at: datetime
    committed_at: datetime | None = None
    metadata: dict[str, Any]
    issues: list[ImportRowIssueResponse]


class IngestionJobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    available_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: Any | None = None
    import_batch_id: int | None = None


class InteropLogResponse(BaseModel):
    id: int
    system_name: str
    direction: str
    status: str
    dataset_type: str
    timestamp: datetime
    external_id: str | None = None
    mapping_id: int | None = None
    details: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class PublicStatsResponse(BaseModel):
    total_visits_recorded: int
    participating_facilities: int
    alert_level: str


class ProvincialStatResponse(BaseModel):
    province: str
    visit_count: int


class PublicMapPointResponse(BaseModel):
    type: str
    name: str
    lat: float
    lon: float
    count: int


class PublicAlertResponse(BaseModel):
    severity: str
    message: str


class SyndromicTrendResponse(BaseModel):
    date: date
    febrile_illness: int = 0
    acute_respiratory: int = 0
    gastrointestinal: int = 0
    neurological: int = 0


class FacilityHeatmapPointResponse(BaseModel):
    name: str
    type: str
    facility_code: str | None = None
    admin1_code: str | None = None
    admin2_code: str | None = None
    lat: float
    lon: float
    count: int


class FacilityConsentResponse(BaseModel):
    status: str
    public_visible: bool
