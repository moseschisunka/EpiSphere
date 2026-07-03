from pydantic import BaseModel, Field, computed_field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from app.db.models import DiagnosisType
from app.core.privacy import mask_identifier

# Patient Schemas
class PatientBase(BaseModel):
    mrn: Optional[str] = Field(default=None, exclude=True)
    dob: Optional[date] = None
    gender: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    facility_id: int
    created_at: datetime

    @computed_field
    @property
    def mrn_display(self) -> Optional[str]:
        return mask_identifier(self.mrn)

    model_config = ConfigDict(from_attributes=True)

# Diagnosis Schemas
class DiagnosisBase(BaseModel):
    disease_id: Optional[int] = None
    icd10_code: Optional[str] = None
    diagnosis_type: DiagnosisType = DiagnosisType.SUSPECTED
    comments: Optional[str] = None

class DiagnosisCreate(DiagnosisBase):
    pass

class Diagnosis(DiagnosisBase):
    id: int
    encounter_id: int

    model_config = ConfigDict(from_attributes=True)

# Prescription Schemas (Embed in Encounter for Creation)
class PrescriptionBase(BaseModel):
    drug_name: str
    dosage: Optional[str] = None
    quantity: int

class PrescriptionCreate(PrescriptionBase):
    pass

class Prescription(PrescriptionBase):
    id: int
    encounter_id: int
    issued_at: datetime
    is_dispensed: bool

    model_config = ConfigDict(from_attributes=True)

# Encounter Schemas
class EncounterBase(BaseModel):
    patient_id: int
    symptoms: Optional[List[str]] = None
    notes: Optional[str] = None

class EncounterCreate(EncounterBase):
    diagnoses: List[DiagnosisCreate] = []
    prescriptions: List[PrescriptionCreate] = []

class Encounter(EncounterBase):
    id: int
    facility_id: int
    clinician_id: int
    date: datetime
    diagnoses: List[Diagnosis] = []
    prescriptions: List[Prescription] = []

    model_config = ConfigDict(from_attributes=True)

