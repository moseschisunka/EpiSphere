from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Country, Disease, Case
from app.schemas.interop_extract import AggregateCaseMetric, DataExtractResponse

def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def test_interop_deidentified_metric_schema():
    metric = AggregateCaseMetric(
        disease_name="COVID-19",
        country_name="Zambia",
        iso_code="ZMB",
        date="2026-08-01",
        daily_cases=45,
        daily_deaths=1,
        daily_recovered=40,
        cumulative_cases=1200,
        cumulative_deaths=15,
        subnational_region="Lusaka",
        source="Ministry of Health"
    )
    response = DataExtractResponse(
        status="success",
        total_records=1,
        extracted_at="2026-08-07T00:00:00",
        metrics=[metric]
    )

    assert response.status == "success"
    assert response.total_records == 1
    assert response.metrics[0].disease_name == "COVID-19"
    assert response.metrics[0].iso_code == "ZMB"

def test_database_interop_data_query():
    db = make_session()
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM", population=20_000_000)
    disease = Disease(name="COVID-19", code="U07.1")
    db.add_all([country, disease])
    db.flush()

    case_record = Case(
        country_id=country.id,
        disease_id=disease.id,
        date=date.today(),
        daily_cases=100,
        daily_deaths=2,
        daily_recovered=90,
        cumulative_cases=5000,
        cumulative_deaths=50,
        source="CDC Interop"
    )
    db.add(case_record)
    db.commit()

    cases = db.query(Case).join(Country).join(Disease).filter(Country.iso_code == "ZMB").all()
    assert len(cases) == 1
    assert cases[0].daily_cases == 100
    assert cases[0].disease.name == "COVID-19"


import pytest
from unittest.mock import patch, MagicMock
from app.services.interop_service import InteropService
from app.api.v1.endpoints.interop import receive_webhook
from app.db.models import User, InteropLog, ImportBatch
from app.core.config import settings
from app.core.dependencies import ServicePrincipal
from app.schemas.interop_extract import WebhookPayload

def test_pull_from_dhis2_mocked_success():
    db = make_session()
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Malaria", code="B50")
    user = User(username="admin", email="admin@test.com", hashed_password="pw", role_id=1)
    db.add_all([country, disease, user])
    db.commit()
    
    mock_dhis2_response = {
        "dataValues": [
            {"dataElement": "de_malaria_1", "period": "202301", "orgUnit": "ou_zambia", "value": "250"},
            {"dataElement": "de_unknown", "period": "202301", "orgUnit": "ou_zambia", "value": "10"}
        ]
    }
    
    mapping = {"de_malaria_1": disease.id}
    
    with patch("httpx.get") as mock_get, patch.object(settings, "DHIS2_URL", "https://dhis2.example"):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_dhis2_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the pull
        result = InteropService.pull_from_dhis2(
            db=db,
            user=user,
            dataset_id="ds_123",
            org_unit="ou_zambia",
            period="202301",
            mapping=mapping,
            country_id=country.id,
            dry_run=False
        )
        
        assert result["success"] is True
        assert result["records_imported"] == 1
        
        # Check DB
        cases = db.query(Case).filter(Case.disease_id == disease.id).all()
        assert len(cases) == 1
        assert cases[0].daily_cases == 250
        
        # Check Log
        logs = db.query(InteropLog).all()
        assert len(logs) == 1
        assert logs[0].direction.value == "inbound"
        assert logs[0].status.value == "success"


def test_webhook_records_schema_compatible_privacy_preserving_log():
    db = make_session()
    payload = WebhookPayload(
        event_type="aggregate_update",
        source_system="DHIS2",
        data={"country": "ZMB", "daily_cases": 12},
    )

    response = receive_webhook(payload, db, ServicePrincipal(name="n8n", auth_method="x-api-key"))

    assert response["status"] == "received"
    log = db.query(InteropLog).one()
    assert log.system_name == "DHIS2"
    assert log.dataset_type == "aggregate_update"
    assert "payload_hash" in log.details
    assert "daily_cases" not in log.details


def test_webhook_rejects_oversized_payload():
    with pytest.raises(ValueError, match="1 MB or smaller"):
        WebhookPayload(
            event_type="aggregate_update",
            source_system="DHIS2",
            data={"blob": "x" * 1_000_001},
        )


def test_dhis2_invalid_period_fails_without_using_today():
    db = make_session()
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Malaria", code="B50")
    user = User(username="admin", email="admin@test.com", hashed_password="pw", role_id=1)
    db.add_all([country, disease, user])
    db.commit()

    result = InteropService.pull_from_dhis2(
        db=db,
        user=user,
        dataset_id="ds_123",
        org_unit="ou_zambia",
        period="not-a-period",
        mapping={"de_malaria_1": disease.id},
        country_id=country.id,
        dry_run=False,
    )

    assert result["success"] is False
    assert "YYYYMM" in result["errors"][0]
    assert db.query(Case).count() == 0
    assert db.query(InteropLog).one().status.value == "failure"


def test_repeating_dhis2_pull_is_idempotent():
    db = make_session()
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Malaria", code="B50")
    user = User(username="admin", email="admin@test.com", hashed_password="pw", role_id=1)
    db.add_all([country, disease, user])
    db.commit()
    mock_dhis2_response = {"dataValues": [{"dataElement": "de_malaria_1", "value": "250"}]}

    with patch("httpx.get") as mock_get, patch.object(settings, "DHIS2_URL", "https://dhis2.example"):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_dhis2_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        kwargs = {
            "db": db,
            "user": user,
            "dataset_id": "ds_123",
            "org_unit": "ou_zambia",
            "period": "202301",
            "mapping": {"de_malaria_1": disease.id},
            "country_id": country.id,
            "dry_run": False,
        }
        first = InteropService.pull_from_dhis2(**kwargs)
        second = InteropService.pull_from_dhis2(**kwargs)

    assert first["records_imported"] == second["records_imported"] == 1
    assert db.query(Case).count() == 1
    assert db.query(ImportBatch).count() == 2


def test_dhis2_push_replay_returns_previous_success_without_resending():
    db = make_session()
    user = User(username="admin", email="admin@test.com", hashed_password="pw", role_id=1)
    db.add(user)
    db.commit()
    response = MagicMock(status_code=201, text="created", headers={"X-Request-ID": "req-1"})
    response.raise_for_status.return_value = None

    with patch("httpx.post", return_value=response) as mock_post, patch.object(settings, "DHIS2_URL", "https://dhis2.example"):
        first = InteropService.sync_to_dhis2(db, user, {"dataValues": []}, "aggregate/dataValueSets")
        second = InteropService.sync_to_dhis2(db, user, {"dataValues": []}, "aggregate/dataValueSets")

    assert first["success"] is True
    assert second["replayed"] is True
    assert mock_post.call_count == 1
