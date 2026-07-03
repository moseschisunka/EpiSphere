import asyncio
from io import BytesIO

from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Country, Disease, Role, User, DHIS2Mapping, InteropLog, ImportBatch, Case
from app.services.data_upload import DataUploadService
from app.services.interop_service import InteropService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def seed_core(db):
    role = Role(name="admin", description="Administrator")
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM", population=20000000)
    disease = Disease(name="Cholera", code="A00")
    db.add_all([role, country, disease])
    db.flush()
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password="test-hash",
        full_name="Admin User",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return country, disease, user


def upload_file_from_text(name, text):
    return UploadFile(filename=name, file=BytesIO(text.encode("utf-8")))


def test_upload_validate_only_creates_batch_without_cases():
    db = make_session()
    country, disease, user = seed_core(db)
    service = DataUploadService(db)
    file = upload_file_from_text(
        "cholera.csv",
        "date,daily_cases,cumulative_cases,daily_deaths,cumulative_deaths,confirmation_status\n"
        "2026-07-01,5,5,0,0,confirmed\n",
    )

    result = asyncio.run(service.upload_file(file, country.id, disease.id, user.id, commit=False))

    assert result["success"] is True
    assert result["committed"] is False
    assert result["rows_valid"] == 1
    assert db.query(ImportBatch).count() == 1
    assert db.query(Case).count() == 0


def test_upload_rejects_invalid_rows_and_records_errors():
    db = make_session()
    country, disease, user = seed_core(db)
    service = DataUploadService(db)
    file = upload_file_from_text(
        "bad.csv",
        "date,daily_cases,daily_deaths\n"
        "2026-07-01,2,5\n",
    )

    result = asyncio.run(service.upload_file(file, country.id, disease.id, user.id, commit=True))

    assert result["success"] is False
    assert result["error_count"] == 1
    assert "Daily deaths cannot exceed daily cases" in result["errors"][0]
    assert db.query(Case).count() == 0


def test_dhis2_sync_validates_payload_before_dry_run():
    db = make_session()
    _country, _disease, user = seed_core(db)
    db.add(DHIS2Mapping(
        dataset="aggregate/dataValueSets",
        endpoint_path="api/dataValueSets",
        payload_type="aggregate",
        required_fields=["dataValues"],
        is_active=True,
    ))
    db.commit()

    invalid = InteropService.sync_to_dhis2(db, user, {"wrong": []}, "aggregate/dataValueSets", dry_run=True)
    valid = InteropService.sync_to_dhis2(db, user, {"dataValues": []}, "aggregate/dataValueSets", dry_run=True)

    assert invalid["success"] is False
    assert "Missing required DHIS2 field: dataValues" in invalid["errors"]
    assert valid["success"] is True
    assert db.query(InteropLog).count() == 2
