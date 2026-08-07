from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DHIS2SyncRequest(BaseModel):
    dataset: str = Field(..., min_length=1, max_length=100)
    payload: Dict[str, Any]
    mapping_id: Optional[int] = None
    dry_run: bool = False


class DHIS2SyncResponse(BaseModel):
    success: bool
    status: str
    log_id: int
    dry_run: bool
    errors: list[str] = []
    message: str


class DHIS2PullRequest(BaseModel):
    dataset_id: str = Field(..., description="DHIS2 dataset ID to pull")
    org_unit: str = Field(..., description="DHIS2 Organization Unit ID")
    period: str = Field(..., description="DHIS2 Period (e.g. 202301 or 2023-01-01)")
    mapping: Dict[str, int] = Field(..., description="Mapping of DHIS2 data element UUID to internal Disease ID")
    country_id: int = Field(..., description="Internal Country ID to assign the data to")
    dry_run: bool = False


class DHIS2PullResponse(BaseModel):
    success: bool
    status: str
    log_id: int
    records_imported: int
    dry_run: bool
    errors: list[str] = []
    message: str
