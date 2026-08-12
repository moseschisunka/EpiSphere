from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import enforce_country_scope, get_current_active_user, require_role
from app.db.models import User
from app.services.ingestion_jobs import get_job, replay_job, request_cancel
from app.schemas.operational import IngestionJobResponse

router = APIRouter()
OPERATORS = ["admin", "epidemiologist", "country_data_officer"]


def _authorize_job(job, current_user: User):
    if job.import_batch and job.import_batch.country_id is not None:
        enforce_country_scope(current_user, job.import_batch.country_id)


def _serialize(job) -> dict:
    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status.value,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "available_at": job.available_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error": job.error,
        "result": job.result,
        "import_batch_id": job.import_batch_id,
    }


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_ingestion_job(
    job_id: int,
    current_user: User = Depends(require_role(OPERATORS)),
    db: Session = Depends(get_db),
):
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    _authorize_job(job, current_user)
    return _serialize(job)


@router.post("/{job_id}/cancel", response_model=IngestionJobResponse)
def cancel_ingestion_job(
    job_id: int,
    current_user: User = Depends(require_role(OPERATORS)),
    db: Session = Depends(get_db),
):
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    _authorize_job(job, current_user)
    return _serialize(request_cancel(db, job))


@router.post("/{job_id}/replay", response_model=IngestionJobResponse)
def replay_ingestion_job(
    job_id: int,
    current_user: User = Depends(require_role(["admin", "epidemiologist"])),
    db: Session = Depends(get_db),
):
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    _authorize_job(job, current_user)
    try:
        return _serialize(replay_job(db, job))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
