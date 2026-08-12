from pydantic import BaseModel, Field
from typing import Dict, Optional

class CsvIngestRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="URL of the public CSV dataset")
    mapping: Dict[str, str] = Field(..., description="Dictionary mapping internal keys to CSV headers. Keys: country_iso, date, daily_cases, daily_deaths")
    disease_id: int = Field(..., gt=0, description="Internal Disease ID to map these cases to")
    mapping_version: str = Field("v1", min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$", description="Version label for this CSV field mapping")
    dry_run: bool = Field(False, description="If true, parse data but do not write to DB")
    enqueue: bool = Field(False, description="Queue the import for the durable ingestion worker")

class WhoGhoIngestRequest(BaseModel):
    indicator_code: str = Field(..., min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$", description="WHO GHO Indicator Code (e.g. CHOLERA_0000000001)")
    disease_id: int = Field(..., gt=0, description="Internal Disease ID to map these cases to")
    mapping_version: str = Field("who-gho-v1", min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$", description="Version label for the WHO GHO field mapping")
    dry_run: bool = Field(False, description="If true, parse data but do not write to DB")
    enqueue: bool = Field(False, description="Queue the import for the durable ingestion worker")

class IngestResponse(BaseModel):
    success: bool
    records_imported: int
    errors: list[str] = []
    warnings: list[str] = []
    batch_id: int | None = None
    job_id: int | None = None
    records_staged: int = 0
