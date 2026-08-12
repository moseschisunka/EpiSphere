import pytest
import socket
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.services.public_dataset_service import PublicDatasetService
from app.db.models import Case, Country, DataQualityCheck, Disease, ImportBatch, ImportStagedCase, ImportStatus, SourceSystem
from app.core.config import settings
from app.services.data_upload import DataUploadService

@pytest.fixture
def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_ingest_csv_url_success(make_session):
    db = make_session
    
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([country, disease])
    db.commit()

    mock_csv_content = """Country,Date,Cases,Deaths
ZMB,2023-01-01,50,2
ZMB,2023-01-02,30,1
UNKNOWN,2023-01-03,10,0
"""
    
    mapping = {
        "country_iso": "Country",
        "date": "Date",
        "daily_cases": "Cases",
        "daily_deaths": "Deaths"
    }

    with patch.object(
        PublicDatasetService,
        "_download_public_url",
        return_value=(
            mock_csv_content.encode(),
            "http://test.com/data.csv",
            {"content-type": "text/csv", "last-modified": "Wed, 21 Oct 2015 07:28:00 GMT"},
        ),
    ), patch.object(settings, "PUBLIC_DATASET_ALLOWED_HOSTS", ["test.com"]), patch(
        "socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))],
    ):

        result = PublicDatasetService.ingest_csv_url(
            db=db,
            url="http://test.com/data.csv",
            mapping=mapping,
            disease_id=disease.id,
            mapping_version="zambia-cholera-v2",
            dry_run=False
        )

        assert result["success"] is True
        assert result["records_imported"] == 2 # 1 unknown country skipped

        assert result["records_staged"] == 2
        assert db.query(Case).filter(Case.disease_id == disease.id).count() == 0
        assert db.query(ImportStagedCase).count() == 2

        batch = db.query(ImportBatch).one()
        assert batch.status == ImportStatus.VALIDATED
        assert batch.rows_total == 3
        assert batch.rows_valid == 2
        assert batch.rows_committed == 0
        assert batch.batch_metadata["approval_scope"] == "admin"
        assert batch.source_system_id == db.query(SourceSystem).one().id
        assert batch.batch_metadata["mapping_version"] == "zambia-cholera-v2"
        assert batch.batch_metadata["mapping_sha256"]
        assert batch.batch_metadata["source_last_modified"] == "Wed, 21 Oct 2015 07:28:00 GMT"
        checks = {check.check_name: check for check in db.query(DataQualityCheck).filter(DataQualityCheck.batch_id == batch.id)}
        assert checks["row_validity_rate"].passed is False
        assert checks["duplicate_source_rows"].metric_value == 0.0
        assert checks["timeliness"].threshold == 14.0
        assert db.query(ImportStagedCase).filter(ImportStagedCase.batch_id == batch.id).count() == 2

def test_ingest_who_gho_success(make_session):
    db = make_session
    
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([country, disease])
    db.commit()

    mock_who_data = {
        "value": [
            {"SpatialDim": "ZMB", "TimeDim": "2023", "NumericValue": "1000"},
            {"SpatialDim": "ZMB", "TimeDim": "2024", "NumericValue": "500"},
            {"SpatialDim": "XYZ", "TimeDim": "2024", "NumericValue": "10"} # skipped
        ]
    }

    with patch.object(
        PublicDatasetService,
        "_download_public_url",
        return_value=(
            b'{"value": [{"SpatialDim": "ZMB", "TimeDim": "2023", "NumericValue": "1000"}, {"SpatialDim": "ZMB", "TimeDim": "2024", "NumericValue": "500"}, {"SpatialDim": "XYZ", "TimeDim": "2024", "NumericValue": "10"}]}',
            "https://ghoapi.azureedge.net/api/CHOLERA_TEST",
            {"content-type": "application/json"},
        ),
    ), patch.object(settings, "PUBLIC_DATASET_ALLOWED_HOSTS", ["ghoapi.azureedge.net"]), patch(
        "socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    ):

        result = PublicDatasetService.ingest_who_gho(
            db=db,
            indicator_code="CHOLERA_TEST",
            disease_id=disease.id,
            dry_run=False
        )

        assert result["success"] is True
        assert result["records_imported"] == 2

        assert result["records_staged"] == 2
        assert db.query(Case).filter(Case.disease_id == disease.id).count() == 0
        assert db.query(ImportStagedCase).count() == 2
        batch = db.query(ImportBatch).one()
        assert batch.status == ImportStatus.VALIDATED
        assert batch.batch_metadata["indicator_code"] == "CHOLERA_TEST"
        assert batch.batch_metadata["mapping_version"] == "who-gho-v1"
        assert batch.batch_metadata["dataset_contract_version"] == "case_timeseries/v1"
        assert db.query(DataQualityCheck).filter(DataQualityCheck.batch_id == batch.id).count() == 3


def test_reprocessing_same_public_source_is_idempotent(make_session):
    db = make_session
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([country, disease])
    db.commit()
    csv_content = b"Country,Date,Cases\nZMB,2023-01-01,50\n"
    mapping = {"country_iso": "Country", "date": "Date", "daily_cases": "Cases"}

    with patch.object(
        PublicDatasetService,
        "_download_public_url",
        return_value=(csv_content, "https://test.com/data.csv", {"content-type": "text/csv"}),
    ), patch.object(settings, "PUBLIC_DATASET_ALLOWED_HOSTS", ["test.com"]), patch(
        "socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    ):
        first = PublicDatasetService.ingest_csv_url(db, "https://test.com/data.csv", mapping, disease.id)
        second = PublicDatasetService.ingest_csv_url(db, "https://test.com/data.csv", mapping, disease.id)

    assert first["records_imported"] == second["records_imported"] == 1
    DataUploadService(db).commit_validated_batch(first["batch_id"], user_id=1)
    DataUploadService(db).commit_validated_batch(second["batch_id"], user_id=1)
    cases = db.query(Case).filter(Case.disease_id == disease.id).all()
    assert len(cases) == 1
    assert db.query(ImportBatch).count() == 2


def test_ingest_csv_requires_core_mapping(make_session):
    with pytest.raises(ValueError, match="missing required keys"):
        PublicDatasetService._validate_csv_mapping({"country_iso": "Country"})


def test_public_dataset_rejects_unapproved_host(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_DATASET_ALLOWED_HOSTS", ["raw.githubusercontent.com"])

    with pytest.raises(ValueError, match="approved public-source allowlist"):
        PublicDatasetService._validate_public_url("https://example.com/data.csv")


class FakeStreamResponse:
    def __init__(self, *, status_code=200, headers=None, chunks=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = chunks or []

    @property
    def is_redirect(self):
        return 300 <= self.status_code < 400

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError("HTTP failure")

    def iter_bytes(self, _chunk_size):
        yield from self._chunks

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeStreamClient:
    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def stream(self, *_args, **_kwargs):
        return self.response


def test_download_revalidates_redirect_targets(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_DATASET_ALLOWED_HOSTS", ["raw.githubusercontent.com"])
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )
    redirect = FakeStreamResponse(status_code=302, headers={"location": "http://127.0.0.1/private"})
    monkeypatch.setattr("app.services.public_dataset_service.httpx.Client", lambda **_kwargs: FakeStreamClient(redirect))

    with pytest.raises(ValueError):
        PublicDatasetService._download_public_url("https://raw.githubusercontent.com/org/data.csv")


def test_download_stops_when_stream_exceeds_byte_limit(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_DATASET_ALLOWED_HOSTS", ["raw.githubusercontent.com"])
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )
    response = FakeStreamResponse(chunks=[b"x" * (PublicDatasetService.MAX_DOWNLOAD_BYTES + 1)])
    monkeypatch.setattr("app.services.public_dataset_service.httpx.Client", lambda **_kwargs: FakeStreamClient(response))

    with pytest.raises(ValueError, match="25 MB download limit"):
        PublicDatasetService._download_public_url("https://raw.githubusercontent.com/org/data.csv")
