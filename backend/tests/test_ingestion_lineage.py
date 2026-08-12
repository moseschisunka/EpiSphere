from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, ImportBatch, ImportStatus
from app.services.ingestion_lineage import create_import_batch, get_or_create_source_system


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_source_system_identity_is_reused():
    db = make_session()
    first = get_or_create_source_system(
        db,
        code="clinical_encounter",
        name="Clinical encounters",
        system_type="clinical_aggregation",
    )
    second = get_or_create_source_system(
        db,
        code=" CLINICAL_ENCOUNTER ",
        name="Different display name",
        system_type="other",
    )

    assert first.id == second.id
    assert db.query(type(first)).count() == 1
    db.close()


def test_committed_batch_records_lineage_and_counts():
    db = make_session()
    source = get_or_create_source_system(
        db,
        code="who_gho",
        name="WHO GHO",
        system_type="api_ingestion",
    )
    batch = create_import_batch(
        db,
        filename="who.csv",
        dataset_type="case_timeseries",
        source_system=source,
        disease_id=4,
        rows_total=12,
        metadata={"mapping_version": "who-v1", "source_timestamp": "2026-08-12T00:00:00Z"},
        status=ImportStatus.COMMITTED,
    )

    assert batch.source_system_id == source.id
    assert batch.rows_total == 12
    assert batch.rows_valid == 12
    assert batch.rows_committed == 12
    assert batch.committed_at is not None
    assert batch.batch_metadata["mapping_version"] == "who-v1"
    db.close()
