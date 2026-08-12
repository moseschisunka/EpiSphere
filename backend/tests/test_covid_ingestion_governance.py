import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import (
    Base,
    Case,
    Country,
    DataQualityCheck,
    Disease,
    ImportBatch,
    ImportRowError,
    ImportStagedCase,
    ImportStatus,
    Role,
    User,
)
from app.services.covid_data_service import CovidDataService
from app.services.data_upload import DataUploadService


class FakeResponse:
    headers = {"last-modified": "Wed, 21 Oct 2015 07:28:00 GMT"}

    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class FakeAsyncClient:
    def __init__(self, text: str, **_kwargs):
        self.response = FakeResponse(text)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, _url: str):
        return self.response


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_owid_ingestion_stages_reviewable_batch_and_replays_idempotently(monkeypatch):
    db = make_session()
    role = Role(name="admin", description="Administrator")
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    db.add_all([role, country])
    db.flush()
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="test-hash",
        full_name="Admin",
        role_id=role.id,
    )
    db.add(user)
    db.commit()

    csv_text = (
        "location,iso_code,date,new_cases,total_cases,new_deaths,total_deaths\n"
        "Zambia,ZMB,2026-08-01,10,100,1,2\n"
    )
    monkeypatch.setattr(
        "app.services.covid_data_service.httpx.AsyncClient",
        lambda **kwargs: FakeAsyncClient(csv_text, **kwargs),
    )

    first = asyncio.run(CovidDataService(db).ingest_owid_data(user_id=user.id))

    assert first["records_validated"] == 1
    assert first["records_staged"] == 1
    batch = db.query(ImportBatch).filter(ImportBatch.id == first["batch_id"]).one()
    assert batch.status == ImportStatus.VALIDATED
    assert batch.rows_committed == 0
    assert batch.batch_metadata["mapping_version"] == "owid-covid-v1"
    assert batch.batch_metadata["approval_scope"] == "admin"
    assert db.query(Case).count() == 0
    assert db.query(ImportStagedCase).filter(ImportStagedCase.batch_id == batch.id).count() == 1
    assert db.query(ImportRowError).filter(ImportRowError.batch_id == batch.id).count() == 0
    assert db.query(DataQualityCheck).filter(DataQualityCheck.batch_id == batch.id).count() == 3

    DataUploadService(db).commit_validated_batch(batch.id, user.id)
    second = asyncio.run(CovidDataService(db).ingest_owid_data(user_id=user.id))
    DataUploadService(db).commit_validated_batch(second["batch_id"], user.id)

    assert db.query(Case).filter(Case.disease.has(Disease.code == "U07.1")).count() == 1
