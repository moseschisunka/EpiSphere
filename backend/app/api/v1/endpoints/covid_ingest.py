from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import IngestionJob, IngestionJobStatus, User
from app.services.seed_countries import seed_countries_and_regions
from app.services.ingestion_jobs import enqueue_job

router = APIRouter()

@router.post("/seed-countries", status_code=status.HTTP_200_OK)
async def seed_countries_endpoint(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Seed countries and WHO regions."""
    try:
        result = await seed_countries_and_regions(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def trigger_covid_ingest(
    current_user: User = Depends(require_role(["admin", "epidemiologist", "country_data_officer"])),
    db: Session = Depends(get_db),
):
    """Queue durable COVID-19 ingestion for the worker process."""
    active = db.query(IngestionJob).filter(
        IngestionJob.job_type == "owid_covid19",
        IngestionJob.status.in_([
            IngestionJobStatus.QUEUED,
            IngestionJobStatus.RUNNING,
            IngestionJobStatus.CANCEL_REQUESTED,
        ]),
    ).first()
    if active:
        return {"message": "Ingestion already queued", "job_id": active.id, "status": active.status.value}
    job = enqueue_job(
        db,
        job_type="owid_covid19",
        payload={"user_id": current_user.id},
        created_by=current_user.id,
    )
    return {"message": "COVID-19 ingestion queued", "job_id": job.id, "status": job.status.value}

@router.get("/status")
async def get_covid_ingest_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the latest durable COVID-19 ingestion job."""
    job = db.query(IngestionJob).filter(
        IngestionJob.job_type == "owid_covid19",
    ).order_by(IngestionJob.created_at.desc()).first()
    if not job:
        return {"status": "idle", "job_id": None, "result": None}
    return {
        "status": job.status.value,
        "job_id": job.id,
        "attempts": job.attempts,
        "last_run": job.completed_at,
        "result": job.result,
        "error": job.error,
    }
