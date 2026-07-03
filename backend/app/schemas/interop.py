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
