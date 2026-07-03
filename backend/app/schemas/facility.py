from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.db.models import FacilityType

class FacilityBase(BaseModel):
    name: str
    type: FacilityType
    country_id: int
    location: Optional[str] = None
    facility_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    province: Optional[str] = None
    district: Optional[str] = None
    admin1_code: Optional[str] = None
    admin2_code: Optional[str] = None
    parent_id: Optional[int] = None

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(FacilityBase):
    name: Optional[str] = None
    type: Optional[FacilityType] = None
    country_id: Optional[int] = None

class Facility(FacilityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


