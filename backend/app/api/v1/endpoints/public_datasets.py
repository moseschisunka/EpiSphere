from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_dataset_agent_or_admin
from app.db.models import AuditAction, AuditLog, User
from app.schemas.public_datasets import CsvIngestRequest, WhoGhoIngestRequest, IngestResponse
from app.services.public_dataset_service import PublicDatasetService
from app.services.ingestion_jobs import enqueue_job
from app.core.limiter import limiter

router = APIRouter()

@router.post("/ingest-csv", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest_csv_dataset(
    request: Request,
    response: Response,
    payload: CsvIngestRequest,
    db: Session = Depends(get_db),
    agent_or_admin = Depends(get_dataset_agent_or_admin)
):
    """
    Ingest a public CSV dataset from a URL dynamically.
    Requires admin privileges or Agent API Key.
    """
    try:
        if payload.enqueue or not payload.dry_run:
            job = enqueue_job(
                db,
                job_type="public_csv",
                payload={
                    "url": payload.url,
                    "mapping": payload.mapping,
                    "mapping_version": payload.mapping_version,
                    "disease_id": payload.disease_id,
                    "dry_run": payload.dry_run,
                    "require_review": True,
                },
                created_by=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
            )
            db.add(AuditLog(
                user_id=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
                action=AuditAction.UPLOAD,
                resource_type="ingestion_job",
                resource_id=job.id,
                details={
                    "actor": agent_or_admin.name if hasattr(agent_or_admin, "name") else "agent",
                    "auth_method": agent_or_admin.auth_method if hasattr(agent_or_admin, "auth_method") else "bearer",
                    "request_id": getattr(request.state, "request_id", None),
                    "dataset_type": "csv",
                    "queued": True,
                    "dry_run": payload.dry_run,
                },
            ))
            db.commit()
            response.status_code = status.HTTP_202_ACCEPTED
            return IngestResponse(
                success=True,
                records_imported=0,
                warnings=["Import queued for durable worker execution."],
                job_id=job.id,
            )
        result = PublicDatasetService.ingest_csv_url(
            db=db,
            url=payload.url,
            mapping=payload.mapping,
            mapping_version=payload.mapping_version,
            disease_id=payload.disease_id,
            dry_run=payload.dry_run,
            require_review=True,
        )
        db.add(AuditLog(
            user_id=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
            action=AuditAction.UPLOAD,
            resource_type="import_batch",
            resource_id=result.get("batch_id"),
            details={
                "actor": agent_or_admin.name if hasattr(agent_or_admin, "name") else "admin",
                "auth_method": agent_or_admin.auth_method if hasattr(agent_or_admin, "auth_method") else "bearer",
                "request_id": getattr(request.state, "request_id", None),
                "dataset_type": "csv",
                "records_imported": result.get("records_imported", 0),
                "dry_run": payload.dry_run,
            },
        ))
        db.commit()
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
    response: Response,
    payload: WhoGhoIngestRequest,
    db: Session = Depends(get_db),
    agent_or_admin = Depends(get_dataset_agent_or_admin)
):
    """
    Ingest a dataset from WHO Global Health Observatory API.
    Requires admin privileges or Agent API Key.
    """
    try:
        if payload.enqueue or not payload.dry_run:
            job = enqueue_job(
                db,
                job_type="public_who_gho",
                payload={
                    "indicator_code": payload.indicator_code,
                    "disease_id": payload.disease_id,
                    "mapping_version": payload.mapping_version,
                    "dry_run": payload.dry_run,
                    "require_review": True,
                },
                created_by=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
            )
            db.add(AuditLog(
                user_id=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
                action=AuditAction.UPLOAD,
                resource_type="ingestion_job",
                resource_id=job.id,
                details={
                    "actor": agent_or_admin.name if hasattr(agent_or_admin, "name") else "agent",
                    "auth_method": agent_or_admin.auth_method if hasattr(agent_or_admin, "auth_method") else "bearer",
                    "request_id": getattr(request.state, "request_id", None),
                    "dataset_type": "who_gho",
                    "queued": True,
                    "dry_run": payload.dry_run,
                },
            ))
            db.commit()
            response.status_code = status.HTTP_202_ACCEPTED
            return IngestResponse(
                success=True,
                records_imported=0,
                warnings=["Import queued for durable worker execution."],
                job_id=job.id,
            )
        result = PublicDatasetService.ingest_who_gho(
            db=db,
            indicator_code=payload.indicator_code,
            disease_id=payload.disease_id,
            mapping_version=payload.mapping_version,
            dry_run=payload.dry_run,
            require_review=True,
        )
        db.add(AuditLog(
            user_id=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
            action=AuditAction.UPLOAD,
            resource_type="import_batch",
            resource_id=result.get("batch_id"),
            details={
                "actor": agent_or_admin.name if hasattr(agent_or_admin, "name") else "admin",
                "auth_method": agent_or_admin.auth_method if hasattr(agent_or_admin, "auth_method") else "bearer",
                "request_id": getattr(request.state, "request_id", None),
                "dataset_type": "who_gho",
                "records_imported": result.get("records_imported", 0),
                "dry_run": payload.dry_run,
            },
        ))
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
