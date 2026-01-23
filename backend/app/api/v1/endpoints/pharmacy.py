from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.deps import allow_pharmacist, get_current_facility_user
from app.core.database import get_db
from app.db.models import User, Prescription, Dispensation, AuditLog, AuditAction, Encounter, Patient
from app.schemas import pharmacy as schemas

router = APIRouter()

@router.get("/prescriptions", response_model=List[schemas.PrescriptionDetail])
def list_pending_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_pharmacist)
):
    """
    List pending prescriptions for the pharmacist's facility.
    Joins: Prescription -> Encounter -> Facility check
    """
    if not current_user.facility_id:
         raise HTTPException(status_code=403, detail="User not in facility")

    # This query is a bit complex in pure ORM without precise join syntax handy, 
    # but logically: Get prescriptions where encounter.facility_id == current_user.facility_id AND is_dispensed == False
    prescriptions = (
        db.query(Prescription)
        .join(Encounter)
        .filter(Encounter.facility_id == current_user.facility_id)
        .filter(Prescription.is_dispensed == False)
        .all()
    )
    
    # Enrich with details (MRN, Clinician Name) - simplistic approach
    results = []
    for rx in prescriptions:
        # Pydantic schema expects enriched fields. We need to populate them.
        # Ideally simpler to do DTO projection here
        detail = schemas.PrescriptionDetail.from_orm(rx)
        detail.patient_mrn = rx.encounter.patient.mrn
        detail.clinician_name = rx.encounter.clinician.full_name
        results.append(detail)
        
    return results

@router.post("/dispense", response_model=schemas.Dispensation)
def dispense_medication(
    dispense_in: schemas.DispensationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_pharmacist)
):
    """Dispense a medication"""
    # Get RX
    rx = db.query(Prescription).join(Encounter).filter(Prescription.id == dispense_in.prescription_id).first()
    if not rx:
         raise HTTPException(status_code=404, detail="Prescription not found")
         
    # Check facility scope
    if rx.encounter.facility_id != current_user.facility_id:
         raise HTTPException(status_code=403, detail="Prescription from different facility")
    
    if rx.is_dispensed:
         raise HTTPException(status_code=400, detail="Already dispensed")

    # Create Dispensation
    dispensation = Dispensation(
        prescription_id=rx.id,
        pharmacist_id=current_user.id,
        notes=dispense_in.notes
    )
    
    rx.is_dispensed = True
    
    db.add(dispensation)
    
    # Audit
    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.RX_DISPENSE,
        resource_type="prescription",
        resource_id=rx.id,
        details={"facility_id": current_user.facility_id}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(dispensation)
    return dispensation
