from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.privacy import hash_identifier, mask_identifier, normalize_identifier
from app.db.models import Base, Country, Encounter, Facility, FacilityType, Patient, Role, User
from app.services.public_health_service import PublicHealthService


def test_hash_identifier_is_stable_and_normalized(monkeypatch):
    first = hash_identifier(" mrn-001 ")
    second = hash_identifier("MRN-001")

    assert first == second
    assert first != "MRN-001"


def test_mask_identifier_hides_prefix():
    assert mask_identifier("PATIENT-12345") == "***2345"
    assert mask_identifier("123") == "***"
    assert mask_identifier(None) is None


def test_normalize_identifier_handles_blank_values():
    assert normalize_identifier("  abc   123 ") == "ABC 123"
    assert normalize_identifier("   ") is None


def test_public_provincial_aggregates_suppress_small_cells():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    role = Role(name="clinician", description="Clinical user")
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    db.add_all([role, country])
    db.flush()
    facility = Facility(
        name="Public Clinic",
        type=FacilityType.CLINIC,
        country_id=country.id,
        province="Lusaka",
        public_visible=True,
    )
    db.add(facility)
    db.flush()
    user = User(
        username="privacy-clinician",
        email="privacy@example.com",
        hashed_password="test-hash",
        role_id=role.id,
        facility_id=facility.id,
        country_id=country.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    patient = Patient(facility_id=facility.id, mrn_hash="a" * 64)
    db.add(patient)
    db.flush()
    db.add_all([
        Encounter(patient_id=patient.id, facility_id=facility.id, clinician_id=user.id),
        Encounter(patient_id=patient.id, facility_id=facility.id, clinician_id=user.id),
    ])
    db.commit()

    assert PublicHealthService.get_provincial_aggregates(db) == [{"province": "Lusaka", "visit_count": 0}]
    db.add_all([
        Encounter(patient_id=patient.id, facility_id=facility.id, clinician_id=user.id)
        for _ in range(3)
    ])
    db.commit()
    assert PublicHealthService.get_provincial_aggregates(db) == [{"province": "Lusaka", "visit_count": 5}]
    db.close()
