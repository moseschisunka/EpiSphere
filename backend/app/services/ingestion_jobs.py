"""Database-backed ingestion queue with explicit retry and replay semantics."""

from datetime import datetime, timedelta
import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import IngestionJob, IngestionJobStatus

logger = logging.getLogger(__name__)


def enqueue_job(
    db: Session,
    *,
    job_type: str,
    payload: dict,
    created_by: int | None = None,
    import_batch_id: int | None = None,
    max_attempts: int = 3,
) -> IngestionJob:
    if not job_type.strip():
        raise ValueError("job_type is required")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    job = IngestionJob(
        job_type=job_type.strip(),
        status=IngestionJobStatus.QUEUED,
        payload=payload,
        created_by=created_by,
        import_batch_id=import_batch_id,
        max_attempts=max_attempts,
        available_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> IngestionJob | None:
    return db.query(IngestionJob).filter(IngestionJob.id == job_id).first()


def claim_next_job(db: Session, *, worker_id: str | None = None) -> IngestionJob | None:
    """Claim one ready job; row locking prevents duplicate PostgreSQL claims."""

    now = datetime.utcnow()
    query = (
        db.query(IngestionJob)
        .filter(
            IngestionJob.status == IngestionJobStatus.QUEUED,
            IngestionJob.available_at <= now,
        )
        .order_by(IngestionJob.created_at.asc(), IngestionJob.id.asc())
    )
    # SQLite does not support SKIP LOCKED; its test/runtime path remains
    # single-worker. PostgreSQL gets the concurrent-safe row lock.
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        query = query.with_for_update(skip_locked=True)
    job = query.first()
    if not job:
        return None
    job.status = IngestionJobStatus.RUNNING
    job.attempts += 1
    job.started_at = now
    job.worker_id = worker_id or f"worker-{uuid4()}"
    job.updated_at = now
    db.commit()
    db.refresh(job)
    return job


def complete_job(db: Session, job: IngestionJob, result: dict | None = None) -> IngestionJob:
    # A cancellation request can arrive while the handler is running. Refresh
    # the row before finalizing so a completed handler is never reported as a
    # successful job after an operator requested cancellation.
    db.refresh(job)
    if job.status == IngestionJobStatus.CANCEL_REQUESTED:
        job.status = IngestionJobStatus.CANCELLED
        job.result = {
            "cancelled": True,
            "completed_after_cancel_request": True,
            "handler_result": result or {},
        }
        job.error = None
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
    job.status = IngestionJobStatus.SUCCEEDED
    job.result = result or {}
    job.error = None
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


def fail_job(db: Session, job: IngestionJob, error: str) -> IngestionJob:
    safe_error = error[:2000]
    now = datetime.utcnow()
    if job.attempts < job.max_attempts:
        job.status = IngestionJobStatus.QUEUED
        job.available_at = now + timedelta(seconds=min(300, 2 ** job.attempts))
    else:
        job.status = IngestionJobStatus.DEAD_LETTER
        job.completed_at = now
    job.error = safe_error
    job.updated_at = now
    db.commit()
    db.refresh(job)
    logger.warning(
        "ingestion job failed",
        extra={"job_id": job.id, "job_type": job.job_type, "status": job.status.value},
    )
    return job


def request_cancel(db: Session, job: IngestionJob) -> IngestionJob:
    now = datetime.utcnow()
    if job.status == IngestionJobStatus.QUEUED:
        job.status = IngestionJobStatus.CANCELLED
        job.completed_at = now
    elif job.status == IngestionJobStatus.RUNNING:
        job.status = IngestionJobStatus.CANCEL_REQUESTED
        job.cancel_requested_at = now
    else:
        return job
    job.updated_at = now
    db.commit()
    db.refresh(job)
    return job


def replay_job(db: Session, job: IngestionJob) -> IngestionJob:
    if job.status not in {IngestionJobStatus.DEAD_LETTER, IngestionJobStatus.FAILED}:
        raise ValueError("Only failed or dead-letter jobs can be replayed")
    job.status = IngestionJobStatus.QUEUED
    job.attempts = 0
    job.available_at = datetime.utcnow()
    job.started_at = None
    job.completed_at = None
    job.cancel_requested_at = None
    job.worker_id = None
    job.error = None
    job.result = None
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job
