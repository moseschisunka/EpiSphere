"""Dashboard endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.schemas.dashboard import CountryDashboardResponse, DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/global", response_model=DashboardResponse)
async def get_global_dashboard(
    disease_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get global surveillance dashboard data"""
    service = DashboardService(db)
    dashboard_data = service.get_global_dashboard(
        disease_id=disease_id,
        start_date=start_date,
        end_date=end_date
    )
    return dashboard_data


@router.get("/country/{country_id}", response_model=CountryDashboardResponse)
async def get_country_dashboard(
    country_id: int,
    disease_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get country-level dashboard data"""
    service = DashboardService(db)
    dashboard_data = service.get_country_dashboard(
        country_id=country_id,
        disease_id=disease_id,
        start_date=start_date,
        end_date=end_date
    )
    return dashboard_data
