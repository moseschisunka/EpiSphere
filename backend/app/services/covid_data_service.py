"""COVID-19 Data Ingestion Service"""
import logging
import httpx
import pandas as pd
import math
import io
import hashlib
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Case, Country, Disease, SourceSystem, ImportBatch, ImportStatus

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
        try:
            logger.info("Downloading OWID COVID-19 data...")
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    response = await client.get(PRIMARY_URL)
                    response.raise_for_status()
                    csv_text = response.text
                except Exception as e:
                    logger.warning(f"Failed to fetch from primary URL: {e}. Trying fallback...")
                    response = await client.get(FALLBACK_URL)
                    response.raise_for_status()
                    csv_text = response.text
                    
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
                status=ImportStatus.COMMITTED,
                source_system_id=source_system.id,
                disease_id=disease.id,
                uploaded_by=user_id,
                rows_total=len(df),
                uploaded_at=datetime.utcnow(),
                committed_at=datetime.utcnow(),
                batch_metadata={"source": "OWID"}
            )
            self.db.add(batch)
            if self.is_async:
                await self.db.flush()
            else:
                self.db.flush()

            records_to_insert = []
            countries_loaded = set()
            
            for _, row in df.iterrows():
                iso_code = str(row.get('iso_code', ''))
                country_id = country_map.get(iso_code)
                
                if not country_id:
                    continue
                    
                countries_loaded.add(country_id)
                
                daily_cases = row.get('new_cases', 0)
                cumulative_cases = row.get('total_cases', 0)
                daily_deaths = row.get('new_deaths', 0)
                cumulative_deaths = row.get('total_deaths', 0)
                
                daily_cases = 0 if pd.isna(daily_cases) else int(daily_cases)
                cumulative_cases = 0 if pd.isna(cumulative_cases) else int(cumulative_cases)
                daily_deaths = 0 if pd.isna(daily_deaths) else int(daily_deaths)
                cumulative_deaths = 0 if pd.isna(cumulative_deaths) else int(cumulative_deaths)
                
                record = {
                    "country_id": country_id,
                    "disease_id": disease.id,
                    "date": pd.to_datetime(row['date']).date(),
                    "daily_cases": daily_cases,
                    "cumulative_cases": cumulative_cases,
                    "daily_deaths": daily_deaths,
                    "cumulative_deaths": cumulative_deaths,
                    "source_system_id": source_system.id,
                    "source_record_id": hashlib.sha256(
                        f"owid_covid19|{country_id}|{disease.id}|{pd.to_datetime(row['date']).date().isoformat()}".encode("utf-8")
                    ).hexdigest(),
                    "import_batch_id": batch.id,
                    "reporting_level": "national",
                    "data_quality_score": 100.0,
                    "source": "owid_covid19"
                }
                records_to_insert.append(record)
                
            chunk_size = 1000
            for i in range(0, len(records_to_insert), chunk_size):
                chunk = records_to_insert[i:i+chunk_size]
                if self.is_async:
                    for c in chunk:
                        await self._upsert_case_async(c)
                    await self.db.commit()
                else:
                    for c in chunk:
                        self._upsert_case_sync(c)
                    self.db.commit()

            batch.rows_valid = len(records_to_insert)
            batch.rows_committed = len(records_to_insert)
            
            if self.is_async:
                await self.db.commit()
            else:
                self.db.commit()
                
            return {
                "status": "success",
                "total_records_processed": len(records_to_insert),
                "countries_loaded": len(countries_loaded)
            }
            
        except Exception as e:
            logger.error(f"Error ingesting COVID data: {e}")
            if self.is_async:
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
