from pydantic import BaseModel, Field
from typing import Dict, Optional

class CsvIngestRequest(BaseModel):
    url: str = Field(..., description="URL of the public CSV dataset")
    mapping: Dict[str, str] = Field(..., description="Dictionary mapping internal keys to CSV headers. Keys: country_iso, date, daily_cases, daily_deaths")
    disease_id: int = Field(..., description="Internal Disease ID to map these cases to")
    dry_run: bool = Field(False, description="If true, parse data but do not write to DB")

class WhoGhoIngestRequest(BaseModel):
    indicator_code: str = Field(..., description="WHO GHO Indicator Code (e.g. CHOLERA_0000000001)")
    disease_id: int = Field(..., description="Internal Disease ID to map these cases to")
    dry_run: bool = Field(False, description="If true, parse data but do not write to DB")

class IngestResponse(BaseModel):
    success: bool
    records_imported: int
    errors: list[str] = []
