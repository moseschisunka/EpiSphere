"""COVID-19 Data Ingestion Service"""
import logging
import httpx
import pandas as pd
import io
import hashlib
from datetime import date, datetime
from typing import Any, Dict

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Case,
    Country,
    DataQualityCheck,
    Disease,
    ImportBatch,
    ImportRowError,
    ImportStatus,
    QualitySeverity,
    SourceSystem,
)
from app.services.data_upload import DataUploadService

logger = logging.getLogger(__name__)

PRIMARY_URL = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
FALLBACK_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"

# Ignore these aggregated locations
IGNORE_LOCATIONS = [
    "World", "Africa", "Asia", "Europe", "North America", "South America", 
    "European Union", "High income", "Upper middle income", "Lower middle income", 
    "Low income", "Oceania"
]

class CovidDataService:
    def __init__(self, db: Session | AsyncSession):
        self.db = db
        self.is_async = isinstance(db, AsyncSession)

    async def ingest_owid_data(self, user_id: int = None) -> Dict[str, Any]:
        batch: ImportBatch | None = None
        try:
            logger.info("Downloading OWID COVID-19 data...")
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    response = await client.get(PRIMARY_URL)
                    response.raise_for_status()
                    csv_text = response.text
                    source_url = PRIMARY_URL
                except Exception as e:
                    logger.warning(f"Failed to fetch from primary URL: {e}. Trying fallback...")
                    response = await client.get(FALLBACK_URL)
                    response.raise_for_status()
                    csv_text = response.text
                    source_url = FALLBACK_URL
                    
            df = pd.read_csv(io.StringIO(csv_text))
            
            disease = await self._get_or_create_disease()
            source_system = await self._get_or_create_source_system()
            
            # Filter rows
            df = df[~df['location'].isin(IGNORE_LOCATIONS)]
            df = df.dropna(subset=['iso_code', 'date'])
            
            country_map = await self._get_country_map()
            
            batch = ImportBatch(
                filename="owid_covid_data",
                dataset_type="case_timeseries",
                status=ImportStatus.PENDING,
                source_system_id=source_system.id,
                disease_id=disease.id,
                uploaded_by=user_id,
                rows_total=len(df),
                uploaded_at=datetime.utcnow(),
                batch_metadata={
                    "source": "OWID",
                    "url": source_url,
                    "content_sha256": hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
                    "source_last_modified": response.headers.get("last-modified"),
                    "dataset_contract_version": "case_timeseries/v1",
                    "mapping_version": "owid-covid-v1",
                    "transformation_version": "owid_covid19/v1",
                    "require_review": True,
                    "approval_scope": "admin",
                },
            )
            self.db.add(batch)
            if self.is_async:
                await self.db.flush()
            else:
                self.db.flush()

            validated_cases: list[Case] = []
            countries_loaded = set()
            warnings: list[str] = []
            seen_source_records: set[str] = set()
            record_dates: list[date] = []
            
            for row_number, (_, row) in enumerate(df.iterrows(), start=2):
                iso_code = str(row.get('iso_code', ''))
                country_id = country_map.get(iso_code)
                
                if not country_id:
                    warnings.append(f"Row {row_number}: country ISO code is not in the EpiSphere country registry")
                    continue
                    
                countries_loaded.add(country_id)
                
                daily_cases = row.get('new_cases', 0)
                cumulative_cases = row.get('total_cases', 0)
                daily_deaths = row.get('new_deaths', 0)
                cumulative_deaths = row.get('total_deaths', 0)
                
                try:
                    daily_cases = 0 if pd.isna(daily_cases) else int(daily_cases)
                    cumulative_cases = 0 if pd.isna(cumulative_cases) else int(cumulative_cases)
                    daily_deaths = 0 if pd.isna(daily_deaths) else int(daily_deaths)
                    cumulative_deaths = 0 if pd.isna(cumulative_deaths) else int(cumulative_deaths)
                    record_date = pd.to_datetime(row['date']).date()
                except (TypeError, ValueError):
                    warnings.append(f"Row {row_number}: cases, deaths, or date could not be parsed")
                    continue
                if min(daily_cases, cumulative_cases, daily_deaths, cumulative_deaths) < 0:
                    warnings.append(f"Row {row_number}: negative counts are not allowed")
                    continue
                if daily_deaths > daily_cases or cumulative_deaths > cumulative_cases:
                    warnings.append(f"Row {row_number}: death counts exceed case counts")
                    continue
                
                source_record_id = hashlib.sha256(
                    f"owid_covid19|{country_id}|{disease.id}|{record_date.isoformat()}".encode("utf-8")
                ).hexdigest()
                if source_record_id in seen_source_records:
                    warnings.append(f"Row {row_number}: duplicate country/date source row")
                    continue
                seen_source_records.add(source_record_id)
                validated_cases.append(Case(
                    country_id=country_id,
                    disease_id=disease.id,
                    date=record_date,
                    daily_cases=daily_cases,
                    cumulative_cases=cumulative_cases,
                    daily_deaths=daily_deaths,
                    cumulative_deaths=cumulative_deaths,
                    source_system_id=source_system.id,
                    source_record_id=source_record_id,
                    import_batch_id=batch.id,
                    reporting_level="national",
                    data_quality_score=100.0,
                    source="owid_covid19",
                ))
                record_dates.append(record_date)
                
            batch.rows_valid = len(validated_cases)
            batch.rows_committed = 0
            batch.warning_count = len(warnings)
            batch.error_count = 0
            batch.quality_score = round((len(validated_cases) / len(df)) * 100, 2) if len(df) else 0.0
            DataUploadService(self.db)._stage_cases(batch, validated_cases)
            latest_date = max(record_dates) if record_dates else None
            lag_days = (date.today() - latest_date).days if latest_date else None
            self.db.add_all([
                DataQualityCheck(
                    batch_id=batch.id,
                    check_name="row_validity_rate",
                    severity=QualitySeverity.ERROR,
                    passed=(len(validated_cases) / len(df) if len(df) else 0.0) >= 0.95,
                    metric_value=len(validated_cases) / len(df) if len(df) else 0.0,
                    threshold=0.95,
                    message="OWID rows passed country, date, and count validation",
                ),
                DataQualityCheck(
                    batch_id=batch.id,
                    check_name="timeliness",
                    severity=QualitySeverity.WARNING,
                    passed=lag_days is not None and lag_days <= 14,
                    metric_value=float(lag_days) if lag_days is not None else None,
                    threshold=14.0,
                    message="Latest OWID record is within 14 days" if lag_days is not None and lag_days <= 14 else "Latest OWID record is older than 14 days or unavailable",
                ),
                DataQualityCheck(
                    batch_id=batch.id,
                    check_name="invalid_or_duplicate_rows",
                    severity=QualitySeverity.WARNING,
                    passed=not warnings,
                    metric_value=float(len(warnings)),
                    threshold=0.0,
                    message=f"{len(warnings)} OWID row(s) failed validation or were duplicated",
                ),
            ])
            for warning in warnings:
                self.db.add(ImportRowError(batch_id=batch.id, row_number=0, severity=QualitySeverity.WARNING, message=warning))
            batch.status = ImportStatus.VALIDATED
            if self.is_async:
                await self.db.commit()
            else:
                self.db.commit()
                
            return {
                "status": "success",
                "batch_id": batch.id,
                "records_validated": len(validated_cases),
                "records_staged": len(validated_cases),
                "countries_loaded": len(countries_loaded)
            }
            
        except Exception as e:
            logger.error(f"Error ingesting COVID data: {e}")
            if batch is not None:
                batch.status = ImportStatus.FAILED
                batch.error_count = 1
                batch.batch_metadata = {**(batch.batch_metadata or {}), "failure": str(e)[:1000]}
                if self.is_async:
                    await self.db.commit()
                else:
                    self.db.commit()
            elif self.is_async:
                await self.db.rollback()
            else:
                self.db.rollback()
            raise e

    async def _get_or_create_disease(self) -> Disease:
        code = "U07.1"
        if self.is_async:
            res = await self.db.execute(select(Disease).filter_by(code=code))
            disease = res.scalar_one_or_none()
        else:
            disease = self.db.query(Disease).filter_by(code=code).first()
            
        if not disease:
            disease = Disease(name="COVID-19", code=code, description="Coronavirus disease 2019")
            self.db.add(disease)
            if self.is_async:
                await self.db.flush()
            else:
                self.db.flush()
        return disease

    async def _get_or_create_source_system(self) -> SourceSystem:
        code = "owid_covid19"
        if self.is_async:
            res = await self.db.execute(select(SourceSystem).filter_by(code=code))
            source = res.scalar_one_or_none()
        else:
            source = self.db.query(SourceSystem).filter_by(code=code).first()
            
        if not source:
            source = SourceSystem(
                name="Our World in Data COVID-19",
                code=code,
                system_type="api_ingestion",
                owner="OWID"
            )
            self.db.add(source)
            if self.is_async:
                await self.db.flush()
            else:
                self.db.flush()
        return source

    async def _get_country_map(self) -> Dict[str, int]:
        if self.is_async:
            res = await self.db.execute(select(Country.id, Country.iso_code))
            countries = res.all()
        else:
            countries = self.db.query(Country.id, Country.iso_code).all()
            
        return {c.iso_code: c.id for c in countries}

    async def _upsert_case_async(self, record):
        res = await self.db.execute(
            select(Case).filter_by(
                source_system_id=record['source_system_id'],
                source_record_id=record['source_record_id'],
            )
        )
        case = res.scalar_one_or_none()
        
        if case:
            for k, v in record.items():
                setattr(case, k, v)
        else:
            self.db.add(Case(**record))

    def _upsert_case_sync(self, record):
        case = self.db.query(Case).filter_by(
            source_system_id=record['source_system_id'],
            source_record_id=record['source_record_id'],
        ).first()
        
        if case:
            for k, v in record.items():
                setattr(case, k, v)
        else:
            self.db.add(Case(**record))
