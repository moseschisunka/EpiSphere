from pydantic import BaseModel
from typing import Optional
from app.db.models import BiosafetyLevel

class DiseaseBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    biosafety_level: Optional[BiosafetyLevel] = BiosafetyLevel.BSL2
    is_active: bool = True

class DiseaseCreate(DiseaseBase):
    pass

class DiseaseResponse(DiseaseBase):
    id: int

    class Config:
        from_attributes = True
