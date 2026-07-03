from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.clinical import Prescription

class DispensationBase(BaseModel):
    prescription_id: int
    notes: Optional[str] = None

class DispensationCreate(DispensationBase):
    pass

class Dispensation(DispensationBase):
    id: int
    pharmacist_id: int
    dispensed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PrescriptionDetail(Prescription):
    """Extended prescription details for pharmacist view"""
    patient_mrn: Optional[str] = None
    clinician_name: Optional[str] = None


