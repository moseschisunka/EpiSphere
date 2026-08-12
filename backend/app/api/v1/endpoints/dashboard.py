"""Dashboard endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.schemas.dashboard import CountryDashboardResponse, DashboardResponse, OperationsDashboardResponse
from app.services.dashboard_service import DashboardService
from app.core.dependencies import enforce_country_scope, get_current_active_user, get_user_country_scope, is_admin_user, require_role
from app.db.models import User

router = APIRouter()


@router.get("/global", response_model=DashboardResponse)
async def get_global_dashboard(
    disease_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require_role(["epidemiologist", "admin", "country_data_officer"])),
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
    current_user: User = Depends(require_role(["epidemiologist", "admin", "country_data_officer"])),
    db: Session = Depends(get_db)
):
    """Get country-level dashboard data"""
    enforce_country_scope(current_user, country_id)
    service = DashboardService(db)
    dashboard_data = service.get_country_dashboard(
        country_id=country_id,
        disease_id=disease_id,
        start_date=start_date,
        end_date=end_date
    )
    return dashboard_data


@router.get("/operations", response_model=OperationsDashboardResponse)
async def get_operations_dashboard(
    country_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Operational Ministry/EOC queue, reporting delays, and response SLA status."""
    scoped_country = country_id
    if not is_admin_user(current_user):
        scoped_country = get_user_country_scope(current_user)
        if scoped_country is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operational user is not assigned to a country or facility")
    return DashboardService(db).get_operations_dashboard(country_id=scoped_country)
