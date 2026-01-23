"""Forecast endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import Forecast, User
from app.schemas.forecast import ForecastResponse, ForecastRequest
from app.services.forecast_service import ForecastService

router = APIRouter()


@router.post("/generate", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def generate_forecast(
    forecast_request: ForecastRequest,
    current_user: User = Depends(require_role(["epidemiologist", "admin"])),
    db: Session = Depends(get_db)
):
    """Generate a forecast for a country and disease"""
    service = ForecastService(db)
    
    try:
        forecast = await service.generate_forecast(
            country_id=forecast_request.country_id,
            disease_id=forecast_request.disease_id,
            horizon_days=forecast_request.horizon_days,
            model_type=forecast_request.model_type
        )
        
        forecast_dict = {
            **{c.name: getattr(forecast, c.name) for c in forecast.__table__.columns},
            "country_name": forecast.country.name if forecast.country else None,
            "disease_name": forecast.disease.name if forecast.disease else None
        }
        return ForecastResponse(**forecast_dict)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}"
        )


@router.get("/", response_model=List[ForecastResponse])
async def list_forecasts(
    country_id: int = None,
    disease_id: int = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List forecasts"""
    query = db.query(Forecast)
    
    if country_id:
        query = query.filter(Forecast.country_id == country_id)
    if disease_id:
        query = query.filter(Forecast.disease_id == disease_id)
    
    forecasts = query.order_by(Forecast.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for forecast in forecasts:
        forecast_dict = {
            **{c.name: getattr(forecast, c.name) for c in forecast.__table__.columns},
            "country_name": forecast.country.name if forecast.country else None,
            "disease_name": forecast.disease.name if forecast.disease else None
        }
        result.append(ForecastResponse(**forecast_dict))
    
    return result


@router.get("/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(
    forecast_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get forecast by ID"""
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    forecast_dict = {
        **{c.name: getattr(forecast, c.name) for c in forecast.__table__.columns},
        "country_name": forecast.country.name if forecast.country else None,
        "disease_name": forecast.disease.name if forecast.disease else None
    }
    return ForecastResponse(**forecast_dict)
