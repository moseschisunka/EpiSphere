from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import User
from app.services.seed_countries import seed_countries_and_regions
from app.services.covid_data_service import CovidDataService

router = APIRouter()

ingest_status = {
    "status": "idle",
    "last_run": None,
    "result": None
}

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

async def run_covid_ingest(user_id: int):
    global ingest_status
    ingest_status["status"] = "running"
    db_session = SessionLocal()
    try:
        service = CovidDataService(db_session)
        result = await service.ingest_owid_data(user_id=user_id)
        ingest_status["status"] = "completed"
        ingest_status["result"] = result
    except Exception as e:
        ingest_status["status"] = "failed"
        ingest_status["result"] = str(e)
    finally:
        ingest_status["last_run"] = datetime.utcnow().isoformat()
        db_session.close()

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def trigger_covid_ingest(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["admin", "epidemiologist", "country_data_officer"]))
):
    """Trigger background ingestion of COVID-19 data from OWID"""
    global ingest_status
    if ingest_status["status"] == "running":
        return {"message": "Ingestion already running"}
    
    background_tasks.add_task(run_covid_ingest, current_user.id)
    return {"message": "COVID-19 data ingestion started"}

@router.get("/status")
async def get_covid_ingest_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get the status of the last or ongoing ingestion"""
    return ingest_status
