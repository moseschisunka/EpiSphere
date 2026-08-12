"""Dashboard schemas"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date


class GlobalStats(BaseModel):
    """Global statistics for dashboard"""
    total_cases: int
    total_deaths: int
    total_countries: int
    active_diseases: int
    active_alerts: int
    date_range_start: date
    date_range_end: date
    latest_data_date: Optional[date] = None
    data_completeness: Optional[float] = None
    median_reporting_lag_days: Optional[float] = None


class CountryStats(BaseModel):
    """Country-level statistics"""
    country_id: int
    country_name: str
    iso_code: str
    disease_id: int
    disease_name: str
    total_cases: int
    total_deaths: int
    total_recovered: Optional[int] = None
    incidence_per_100k: Optional[float] = None
    cfr: Optional[float] = None
    latest_date: date
    daily_cases_7day_avg: Optional[float] = None
    growth_rate: Optional[float] = None
    reporting_lag_days: Optional[int] = None
    data_quality_score: Optional[float] = None
    data_freshness_status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TimeSeriesPoint(BaseModel):
    """Single time-series data point"""
    date: date
    value: float
    label: Optional[str] = None


class DashboardResponse(BaseModel):
    """Complete dashboard data"""
    global_stats: GlobalStats
    country_stats: List[CountryStats]
    time_series: List[TimeSeriesPoint]
    alerts_summary: Dict[str, int]  # Count by severity
    top_countries: List[CountryStats]  # Top N by cases


class CountryDashboardRequest(BaseModel):
    """Request for country dashboard"""
    country_id: int
    disease_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CountryDashboardCountry(BaseModel):
    id: int
    name: str
    iso_code: str
    population: int | None = None


class CountryDashboardSeriesPoint(BaseModel):
    date: date
    daily_cases: int
    cumulative_cases: int
    daily_deaths: int
    cumulative_deaths: int
    data_quality_score: float | None = None


class CountryDashboardMovingAverage(BaseModel):
    date: date
    value: float


class CountryDashboardQuality(BaseModel):
    date_range_start: date
    date_range_end: date
    latest_data_date: date | None = None
    reporting_lag_days: int | None = None
    completeness: float
    freshness_status: str


class CountryDashboardLatestStats(BaseModel):
    date: date
    daily_cases: int
    cumulative_cases: int
    daily_deaths: int
    cumulative_deaths: int


class CountryDashboardResponse(BaseModel):
    country: CountryDashboardCountry
    time_series: list[CountryDashboardSeriesPoint]
    moving_averages: list[CountryDashboardMovingAverage]
    data_quality: CountryDashboardQuality
    latest_stats: CountryDashboardLatestStats | None = None
