from pydantic import BaseModel
from typing import Optional
from app.db.models import FacilityType

class FacilityBase(BaseModel):
    name: str
    type: FacilityType
    country_id: int
    location: Optional[str] = None
    parent_id: Optional[int] = None

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(FacilityBase):
    name: Optional[str] = None
    type: Optional[FacilityType] = None
    country_id: Optional[int] = None

class Facility(FacilityBase):
    id: int

    class Config:
        orm_mode = True
