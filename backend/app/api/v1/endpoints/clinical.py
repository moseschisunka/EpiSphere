from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import allow_clinician
from app.core.database import get_db
from app.core.privacy import hash_identifier
from app.db.models import (
    AuditAction,
    AuditLog,
    Case,
    Diagnosis,
    DiagnosisType,
    Encounter,
    Patient,
    Prescription,
    User,
)
from app.schemas import clinical as schemas

router = APIRouter()


def process_outbreak_signal(db: Session, encounter: Encounter) -> int:
    """Aggregate confirmed diagnoses into daily surveillance case counts."""
    created_or_updated = 0
    encounter_date = encounter.date.date() if encounter.date else datetime.utcnow().date()

    for diagnosis in encounter.diagnoses:
        if diagnosis.diagnosis_type != DiagnosisType.CONFIRMED or not diagnosis.disease_id:
            continue

        case = db.query(Case).filter(
            Case.country_id == encounter.facility.country_id,
            Case.disease_id == diagnosis.disease_id,
            Case.date == encounter_date,
            Case.subnational_region == encounter.facility.district,
            Case.source == "clinical_encounter",
        ).first()

        if case:
            case.daily_cases += 1
            case.cumulative_cases += 1
            case.updated_at = datetime.utcnow()
        else:
            case = Case(
                country_id=encounter.facility.country_id,
                disease_id=diagnosis.disease_id,
                date=encounter_date,
                daily_cases=1,
                cumulative_cases=1,
                daily_deaths=0,
                cumulative_deaths=0,
                subnational_region=encounter.facility.district,
                source="clinical_encounter",
                notes=f"Aggregated from encounter {encounter.id}",
            )
            db.add(case)
        created_or_updated += 1

    return created_or_updated


@router.post("/patients", response_model=schemas.Patient)
def create_patient(
    patient_in: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Register a new patient scoped to the clinician's facility."""
    if not current_user.facility_id:
        raise HTTPException(status_code=403, detail="User not in facility")

    mrn_hash = hash_identifier(patient_in.mrn)
    if mrn_hash:
        existing = db.query(Patient).filter(
            Patient.facility_id == current_user.facility_id,
            Patient.mrn_hash == mrn_hash,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient identifier already exists for this facility",
            )

    patient = Patient(
        mrn=patient_in.mrn,
        mrn_hash=mrn_hash,
        dob=patient_in.dob,
        gender=patient_in.gender,
        facility_id=current_user.facility_id,
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
    """List patients scoped to the current user's facility."""
    if not current_user.facility_id:
        raise HTTPException(status_code=403, detail="User not in facility")

    return db.query(Patient).filter(Patient.facility_id == current_user.facility_id).offset(skip).limit(limit).all()


@router.post("/encounters", response_model=schemas.Encounter)
def create_encounter(
    encounter_in: schemas.EncounterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_clinician)
):
    """Record a clinical encounter and aggregate confirmed diagnoses."""
    if not current_user.facility_id:
        raise HTTPException(status_code=403, detail="User not in facility")

    patient = db.query(Patient).filter(
        Patient.id == encounter_in.patient_id,
        Patient.facility_id == current_user.facility_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in this facility")

    encounter = Encounter(
        patient_id=encounter_in.patient_id,
        facility_id=current_user.facility_id,
        clinician_id=current_user.id,
        symptoms=encounter_in.symptoms,
        notes=encounter_in.notes,
    )
    db.add(encounter)
    db.flush()

    for diag_in in encounter_in.diagnoses:
        db.add(Diagnosis(
            encounter_id=encounter.id,
            comments=diag_in.comments,
            diagnosis_type=diag_in.diagnosis_type,
            icd10_code=diag_in.icd10_code,
            disease_id=diag_in.disease_id,
        ))

    for rx_in in encounter_in.prescriptions:
        db.add(Prescription(
            encounter_id=encounter.id,
            drug_name=rx_in.drug_name,
            dosage=rx_in.dosage,
            quantity=rx_in.quantity,
        ))

    db.flush()
    db.refresh(encounter)
    aggregated_cases = process_outbreak_signal(db, encounter)

    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CLINICAL_ENTRY,
        resource_type="encounter",
        resource_id=encounter.id,
        details={
            "facility_id": current_user.facility_id,
            "aggregated_confirmed_diagnoses": aggregated_cases,
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(encounter)
    return encounter
