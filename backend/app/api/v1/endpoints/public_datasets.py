from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_agent_or_admin
from app.db.models import User
from app.schemas.public_datasets import CsvIngestRequest, WhoGhoIngestRequest, IngestResponse
from app.services.public_dataset_service import PublicDatasetService

router = APIRouter()

@router.post("/ingest-csv", response_model=IngestResponse)
async def ingest_csv_dataset(
    request: CsvIngestRequest,
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
            url=request.url,
            mapping=request.mapping,
            disease_id=request.disease_id,
            dry_run=request.dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/ingest-who", response_model=IngestResponse)
async def ingest_who_gho_dataset(
    request: WhoGhoIngestRequest,
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
            indicator_code=request.indicator_code,
            disease_id=request.disease_id,
            dry_run=request.dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
