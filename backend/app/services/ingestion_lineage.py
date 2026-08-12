"""Shared lineage primitives used by all synchronous ingestion entry points."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ImportBatch, ImportStatus, SourceSystem


def get_or_create_source_system(
    db: Session,
    *,
    code: str,
    name: str,
    system_type: str,
    owner: str = "EpiSphere",
) -> SourceSystem:
    """Return a stable source identity without creating duplicate systems."""

    normalized_code = code.strip().lower()
    if not normalized_code:
        raise ValueError("Source system code is required")
    source = db.query(SourceSystem).filter(SourceSystem.code == normalized_code).first()
    if source:
        return source
    source = SourceSystem(
        code=normalized_code,
        name=name,
        system_type=system_type,
        owner=owner,
        is_active=True,
    )
    db.add(source)
    db.flush()
    return source


def create_import_batch(
    db: Session,
    *,
    filename: str,
    dataset_type: str,
    source_system: SourceSystem,
    uploaded_by: int | None = None,
    country_id: int | None = None,
    disease_id: int | None = None,
    rows_total: int = 0,
    metadata: dict[str, Any] | None = None,
    status: ImportStatus = ImportStatus.PENDING,
) -> ImportBatch:
    """Create a durable batch envelope before records are written."""

    batch = ImportBatch(
        filename=filename,
        dataset_type=dataset_type,
        status=status,
        source_system_id=source_system.id,
        country_id=country_id,
        disease_id=disease_id,
        uploaded_by=uploaded_by,
        rows_total=rows_total,
        uploaded_at=datetime.utcnow(),
        batch_metadata=metadata or {},
    )
    if status == ImportStatus.COMMITTED:
        batch.rows_valid = rows_total
        batch.rows_committed = rows_total
        batch.committed_at = datetime.utcnow()
    db.add(batch)
    db.flush()
    return batch
