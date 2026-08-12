from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_agent_or_admin
from app.db.models import User
from app.schemas.public_datasets import CsvIngestRequest, WhoGhoIngestRequest, IngestResponse
from app.services.public_dataset_service import PublicDatasetService
from app.core.limiter import limiter

router = APIRouter()

@router.post("/ingest-csv", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest_csv_dataset(
    request: Request,
    payload: CsvIngestRequest,
    db: Session = Depends(get_db),
    agent_or_admin = Depends(get_agent_or_admin)
):
    """
    Ingest a public CSV dataset from a URL dynamically.
    Requires admin privileges or Agent API Key.
    """
    try:
        result = PublicDatasetService.ingest_csv_url(
            db=db,
            url=payload.url,
            mapping=payload.mapping,
            disease_id=payload.disease_id,
            dry_run=payload.dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/ingest-who", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest_who_gho_dataset(
    request: Request,
    payload: WhoGhoIngestRequest,
    db: Session = Depends(get_db),
    agent_or_admin = Depends(get_agent_or_admin)
):
    """
    Ingest a dataset from WHO Global Health Observatory API.
    Requires admin privileges or Agent API Key.
    """
    try:
        result = PublicDatasetService.ingest_who_gho(
            db=db,
            indicator_code=payload.indicator_code,
            disease_id=payload.disease_id,
            dry_run=payload.dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
