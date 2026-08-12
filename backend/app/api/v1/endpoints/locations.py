from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.db.models import Region, Country, Facility
from app.schemas.operational import DistrictsResponse, LocationHierarchyResponse, ProvincesResponse

router = APIRouter()


@router.get("/hierarchy", response_model=List[LocationHierarchyResponse])
def get_location_hierarchy(
    region_id: Optional[int] = None,
    country_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get full location hierarchy (Region -> Country -> Province -> District -> Facility).
    Useful for cascading dropdown selectors in surveillance filters.
    """
    regions_query = db.query(Region)
    if region_id:
        regions_query = regions_query.filter(Region.id == region_id)
    regions = regions_query.all()

    result = []
    for r in regions:
        countries_query = db.query(Country).filter(Country.region_id == r.id)
        if country_id:
            countries_query = countries_query.filter(Country.id == country_id)
        countries = countries_query.all()

        c_list = []
        for c in countries:
            facilities = db.query(Facility).filter(Facility.country_id == c.id).all()
            provinces_set = set(f.province for f in facilities if f.province)
            districts_set = set(f.district for f in facilities if f.district)

            c_list.append({
                "id": c.id,
                "name": c.name,
                "iso_code": c.iso_code,
                "provinces": sorted(list(provinces_set)),
                "districts": sorted(list(districts_set)),
                "facility_count": len(facilities),
                "facilities": [
                    {
                        "id": f.id,
                        "name": f.name,
                        "type": f.type,
                        "province": f.province,
                        "district": f.district,
                        "latitude": f.latitude,
                        "longitude": f.longitude,
                    }
                    for f in facilities
                ]
            })

        result.append({
            "region_id": r.id,
            "region_name": r.name,
            "region_code": r.code,
            "countries": c_list
        })

    return result


@router.get("/provinces", response_model=ProvincesResponse)
def get_provinces_by_country(country_id: int, db: Session = Depends(get_db)):
    """List unique provinces/states for a given country."""
    facilities = db.query(Facility).filter(Facility.country_id == country_id).all()
    provinces = sorted(list(set(f.province for f in facilities if f.province)))
    return {"country_id": country_id, "provinces": provinces}


@router.get("/districts", response_model=DistrictsResponse)
def get_districts_by_province(country_id: int, province: str, db: Session = Depends(get_db)):
    """List districts in a specific province."""
    facilities = db.query(Facility).filter(
        Facility.country_id == country_id,
        Facility.province == province
    ).all()
    districts = sorted(list(set(f.district for f in facilities if f.district)))
    return {"country_id": country_id, "province": province, "districts": districts}
