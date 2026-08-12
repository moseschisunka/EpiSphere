from datetime import date, datetime
from app.schemas.operational import (
    CountryResponse,
    ImportBatchDetailResponse,
    IngestionJobResponse,
    SyndromicTrendResponse,
)
from app.services.syndromic_service import SyndromicService


def test_reference_and_ingestion_contracts_validate_serialized_endpoint_shapes():
    country = CountryResponse(
        id=1,
        name="Zambia",
        iso_code="ZMB",
        population=20_000_000,
    )
    batch = ImportBatchDetailResponse(
        id=9,
        filename="cholera.csv",
        dataset_type="case_timeseries",
        status="committed",
        rows_total=1,
        rows_valid=1,
        rows_committed=1,
        error_count=0,
        warning_count=0,
        uploaded_at="2026-08-12T00:00:00",
        metadata={"mapping_version": "v1"},
        issues=[],
    )
    job = IngestionJobResponse(
        id=3,
        job_type="public_csv_ingest",
        status="succeeded",
        attempts=1,
        max_attempts=3,
        available_at="2026-08-12T00:00:00",
        result={"batch_id": batch.id},
    )

    assert country.iso_code == "ZMB"
    assert batch.metadata["mapping_version"] == "v1"
    assert job.result == {"batch_id": 9}


def test_syndromic_trends_use_stable_machine_readable_keys():
    encounter = type("EncounterFixture", (), {"date": datetime.combine(date.today(), datetime.min.time()), "symptoms": ["fever", "cough"]})()

    class QueryFixture:
        def filter(self, *_args):
            return self

        def all(self):
            return [encounter]

    class DatabaseFixture:
        def query(self, *_args):
            return QueryFixture()

    trend = SyndromicService.get_national_trends(DatabaseFixture(), days=1)[-1]
    response = SyndromicTrendResponse.model_validate(trend)

    assert response.febrile_illness == 1
    assert response.acute_respiratory == 1
    assert "Febrile Illness" not in trend
