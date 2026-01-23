from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime
from app.db.models import DiagnosisType

# Patient Schemas
class PatientBase(BaseModel):
    mrn: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    facility_id: int
    created_at: datetime

    class Config:
        orm_mode = True

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

    class Config:
        orm_mode = True

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

    class Config:
        orm_mode = True

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

    class Config:
        orm_mode = True
