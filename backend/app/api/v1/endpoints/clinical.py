from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import allow_clinician, get_current_facility_user
from app.core.database import get_db
from app.db.models import User, Patient, Encounter, Diagnosis, Prescription, AuditLog, AuditAction
from app.schemas import clinical as schemas

router = APIRouter()

# Outbreak Integration Signal (Simple implementation)
def process_outbreak_signal(db: Session, encounter: Encounter):
    # This would aggregate data or trigger immediate alerts
    # For now, we'll just print/log. Real implementation involves updating aggregated 'Case' tables.
    for diagnosis in encounter.diagnoses:
        if diagnosis.diagnosis_type == "confirmed":
             pass
             # Logic to increment daily case count for (Country, Disease, Date)
             # This forms the "Primary Input" for outbreak detection

@router.post("/patients", response_model=schemas.Patient)
def create_patient(
    patient_in: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Register a new patient"""
    # Check permission (clinician must have facility)
    if not current_user.facility_id:
         raise HTTPException(status_code=403, detail="User not in facility")

    patient = Patient(
        **patient_in.dict(), 
        facility_id=current_user.facility_id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@router.get("/patients", response_model=List[schemas.Patient])
def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """List patients (Scoped to Facility)"""
    if not current_user.facility_id:
         raise HTTPException(status_code=403, detail="User not in facility")
         
    return db.query(Patient).filter(Patient.facility_id == current_user.facility_id).offset(skip).limit(limit).all()

@router.post("/encounters", response_model=schemas.Encounter)
def create_encounter(
    encounter_in: schemas.EncounterCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Record a clinical encounter"""
    if not current_user.facility_id:
         raise HTTPException(status_code=403, detail="User not in facility")
    
    # Verify patient belongs to facility
    patient = db.query(Patient).filter(Patient.id == encounter_in.patient_id, Patient.facility_id == current_user.facility_id).first()
    if not patient:
         raise HTTPException(status_code=404, detail="Patient not found in this facility")

    # Create Encounter
    encounter = Encounter(
        patient_id=encounter_in.patient_id,
        facility_id=current_user.facility_id,
        clinician_id=current_user.id,
        symptoms=encounter_in.symptoms,
        notes=encounter_in.notes
    )
    db.add(encounter)
    db.flush() # Get ID

    # Add Diagnoses
    for diag_in in encounter_in.diagnoses:
        diag = Diagnosis(
            encounter_id=encounter.id,
            comments=diag_in.comments,
            diagnosis_type=diag_in.diagnosis_type,
            icd10_code=diag_in.icd10_code,
            disease_id=diag_in.disease_id
        )
        db.add(diag)
    
    # Add Prescriptions
    for rx_in in encounter_in.prescriptions:
        rx = Prescription(
            encounter_id=encounter.id,
            drug_name=rx_in.drug_name,
            dosage=rx_in.dosage,
            quantity=rx_in.quantity
        )
        db.add(rx)
    
    # Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CLINICAL_ENTRY,
        resource_type="encounter",
        resource_id=encounter.id,
        details={"facility_id": current_user.facility_id}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(encounter)
    
    # Background processing for surveillance
    # background_tasks.add_task(process_outbreak_signal, db, encounter) 
    # Note: passing db session to background task can be tricky with closing. 
    # Ideally use a separate session or service.
    
    return encounter
