from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import allow_admin
from app.core.database import get_db
from app.db.models import User, InteropLog
from app.schemas.interop import DHIS2SyncRequest, DHIS2SyncResponse
from app.services.interop_service import InteropService

router = APIRouter()


@router.post("/dhis2/sync", response_model=DHIS2SyncResponse)
def trigger_dhis2_sync(
    sync_request: DHIS2SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """Validate and optionally sync a mapped payload to DHIS2."""
    result = InteropService.sync_to_dhis2(
        db=db,
        user=current_user,
        payload=sync_request.payload,
        dataset=sync_request.dataset,
        mapping_id=sync_request.mapping_id,
        dry_run=sync_request.dry_run,
    )
    if not result["success"]:
        raise HTTPException(status_code=400 if result["dry_run"] else 502, detail=result)
    return result


@router.get("/logs")
def get_interop_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """View interop logs."""
    return db.query(InteropLog).order_by(InteropLog.timestamp.desc()).offset(skip).limit(limit).all()
