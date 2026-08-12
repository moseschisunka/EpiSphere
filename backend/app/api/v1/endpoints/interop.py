import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.api.v1.deps import allow_admin
from app.core.dependencies import get_agent_or_admin
from app.core.database import get_db
from app.db.models import User, InteropLog, Case, Disease, Country, InteropDirection, InteropStatus, SourceSystem
from app.schemas.interop import DHIS2SyncRequest, DHIS2SyncResponse, DHIS2PullRequest, DHIS2PullResponse
from app.schemas.interop_extract import DataExtractResponse, AggregateCaseMetric, WebhookPayload
from app.services.interop_service import InteropService

router = APIRouter()


@router.get("/source-systems")
def list_source_systems(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin),
):
    """List configured source identities and their active state."""
    return [
        {
            "id": source.id,
            "name": source.name,
            "code": source.code,
            "system_type": source.system_type,
            "owner": source.owner,
            "is_active": source.is_active,
        }
        for source in db.query(SourceSystem).order_by(SourceSystem.name).all()
    ]


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


@router.post("/dhis2/pull", response_model=DHIS2PullResponse)
def trigger_dhis2_pull(
    pull_request: DHIS2PullRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """Fetch data from DHIS2 and store it as Cases in EpiSphere."""
    result = InteropService.pull_from_dhis2(
        db=db,
        user=current_user,
        dataset_id=pull_request.dataset_id,
        org_unit=pull_request.org_unit,
        period=pull_request.period,
        mapping=pull_request.mapping,
        country_id=pull_request.country_id,
        dry_run=pull_request.dry_run,
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


@router.get("/extract", response_model=DataExtractResponse)
def extract_deidentified_data(
    disease_id: Optional[int] = Query(None, description="Filter by disease ID"),
    disease_name: Optional[str] = Query(None, description="Filter by disease name (e.g., COVID-19)"),
    country_id: Optional[int] = Query(None, description="Filter by country ID"),
    iso_code: Optional[str] = Query(None, description="Filter by ISO 3-letter code"),
    start_date: Optional[date] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="Filter by end date YYYY-MM-DD"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """
    Export de-identified aggregate surveillance case records for clinical registrars & EHR systems.
    Guarantees strict privacy standards: returns zero personal health identifiers or MRNs.
    """
    query = db.query(Case).join(Country).join(Disease)

    if disease_id:
        query = query.filter(Case.disease_id == disease_id)
    elif disease_name:
        query = query.filter(Disease.name.ilike(f"%{disease_name}%"))

    if country_id:
        query = query.filter(Case.country_id == country_id)
    elif iso_code:
        query = query.filter(Country.iso_code == iso_code.upper())

    if start_date:
        query = query.filter(Case.date >= start_date)
    if end_date:
        query = query.filter(Case.date <= end_date)

    records = query.order_by(Case.date.desc()).limit(limit).all()

    metrics = [
        AggregateCaseMetric(
            disease_name=c.disease.name,
            country_name=c.country.name,
            iso_code=c.country.iso_code,
            date=c.date.isoformat(),
            daily_cases=c.daily_cases or 0,
            daily_deaths=c.daily_deaths or 0,
            daily_recovered=c.daily_recovered or 0,
            cumulative_cases=c.cumulative_cases or 0,
            cumulative_deaths=c.cumulative_deaths or 0,
            subnational_region=c.subnational_region,
            source=c.source or "EpiSphere Surveillance Network",
        )
        for c in records
    ]

    return DataExtractResponse(
        status="success",
        de_identified=True,
        total_records=len(metrics),
        extracted_at=datetime.utcnow().isoformat(),
        metrics=metrics,
    )


@router.post("/webhook")
def receive_webhook(
    payload: WebhookPayload,
    db: Session = Depends(get_db),
    agent_or_admin = Depends(get_agent_or_admin),
):
    """
    Receive inbound webhook events from external EHR, LIMS, or DHIS2 systems.
    Logs event into InteropLog audit ledger.
    """
    payload_hash = hashlib.sha256(
        json.dumps(payload.data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
    actor = agent_or_admin.name if hasattr(agent_or_admin, "name") else "admin"
    log_entry = InteropLog(
        system_name=payload.source_system[:50],
        direction=InteropDirection.INBOUND,
        status=InteropStatus.SUCCESS,
        dataset_type=payload.event_type[:50],
        details={
            "event_type": payload.event_type,
            "payload_hash": payload_hash,
            "payload_keys": sorted(payload.data.keys()),
            "received_by": actor,
        },
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "status": "received",
        "log_id": log_entry.id,
        "event_type": payload.event_type,
        "timestamp": log_entry.timestamp.isoformat()
    }

