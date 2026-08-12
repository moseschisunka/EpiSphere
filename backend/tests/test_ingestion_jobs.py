from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import AuditLog, Base, ImportBatch, IngestionJobStatus, ImportStatus
from app.services.ingestion_jobs import (
    claim_next_job,
    complete_job,
    enqueue_job,
    fail_job,
    replay_job,
    record_worker_heartbeat,
    request_cancel,
)


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_job_retry_then_dead_letters_and_can_replay():
    db = make_session()
    job = enqueue_job(db, job_type="test", payload={"source": "fixture"}, max_attempts=2)

    claimed = claim_next_job(db, worker_id="worker-a")
    assert claimed.id == job.id
    assert claimed.status is IngestionJobStatus.RUNNING
    failed = fail_job(db, claimed, "first failure")
    assert failed.status is IngestionJobStatus.QUEUED
    failed.available_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    claimed_again = claim_next_job(db, worker_id="worker-a")
    dead = fail_job(db, claimed_again, "second failure")
    assert dead.status is IngestionJobStatus.DEAD_LETTER
    replayed = replay_job(db, dead)
    assert replayed.status is IngestionJobStatus.QUEUED
    assert replayed.attempts == 0
    db.close()


def test_queued_job_can_be_cancelled_without_execution():
    db = make_session()
    job = enqueue_job(db, job_type="test", payload={})
    cancelled = request_cancel(db, job)
    assert cancelled.status is IngestionJobStatus.CANCELLED
    assert claim_next_job(db, worker_id="worker-a") is None
    db.close()


def test_successful_job_records_result():
    db = make_session()
    job = enqueue_job(db, job_type="test", payload={})
    claimed = claim_next_job(db, worker_id="worker-a")
    complete_job(db, claimed, {"rows": 4})
    assert claimed.status is IngestionJobStatus.SUCCEEDED
    assert claimed.result == {"rows": 4}
    db.close()


def test_completed_originating_job_links_its_batch_and_audit_context():
    db = make_session()
    batch = ImportBatch(filename="source.csv", dataset_type="case_timeseries", status=ImportStatus.VALIDATED)
    db.add(batch)
    db.commit()
    job = enqueue_job(
        db,
        job_type="public_csv",
        payload={"_origin": {"workflow_identity": "n8n-datasets", "request_id": "req-123", "source": "n8n_dataset_csv"}},
    )
    claimed = claim_next_job(db, worker_id="worker-a")

    completed = complete_job(db, claimed, {"batch_id": batch.id, "records_staged": 4})

    assert completed.import_batch_id == batch.id
    audit = db.query(AuditLog).filter(AuditLog.resource_type == "import_batch").one()
    assert audit.resource_id == batch.id
    assert audit.details["workflow_identity"] == "n8n-datasets"
    assert audit.details["request_id"] == "req-123"
    db.close()


def test_cancel_requested_during_execution_finalizes_as_cancelled():
    db = make_session()
    job = enqueue_job(db, job_type="test", payload={})
    claimed = claim_next_job(db, worker_id="worker-a")

    request_cancel(db, claimed)
    finalized = complete_job(db, claimed, {"rows": 4})

    assert finalized.status is IngestionJobStatus.CANCELLED
    assert finalized.result == {
        "cancelled": True,
        "completed_after_cancel_request": True,
        "handler_result": {"rows": 4},
    }
    db.close()


def test_replay_rejects_queued_job():
    db = make_session()
    job = enqueue_job(db, job_type="test", payload={})
    with pytest.raises(ValueError, match="failed or dead-letter"):
        replay_job(db, job)
    db.close()


def test_worker_heartbeat_is_upserted_with_latest_job_state():
    db = make_session()
    job = enqueue_job(db, job_type="test", payload={})

    first = record_worker_heartbeat(db, worker_id="worker-a", last_job_id=job.id)
    updated = record_worker_heartbeat(db, worker_id="worker-a", last_error="temporary upstream failure")

    assert first.worker_id == updated.worker_id == "worker-a"
    assert updated.last_job_id == job.id
    assert updated.last_error == "temporary upstream failure"
    db.close()
