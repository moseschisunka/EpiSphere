"""Country endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.db.models import Country

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_countries(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """List all countries (public endpoint)"""
    countries = db.query(Country).offset(skip).limit(limit).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "iso_code": c.iso_code,
            "iso_code_2": c.iso_code_2,
            "region_id": c.region_id,
            "population": c.population,
            "latitude": c.latitude,
            "longitude": c.longitude
        }
        for c in countries
    ]


@router.get("/{country_id}", response_model=dict)
async def get_country(
    country_id: int,
    db: Session = Depends(get_db)
):
    """Get country by ID (public endpoint)"""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Country not found"
        )
    
    return {
        "id": country.id,
        "name": country.name,
        "iso_code": country.iso_code,
        "iso_code_2": country.iso_code_2,
        "region_id": country.region_id,
        "population": country.population,
        "latitude": country.latitude,
        "longitude": country.longitude
    }
