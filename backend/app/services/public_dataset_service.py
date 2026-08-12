import httpx
import csv
import io
import ipaddress
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.models import (
    Case,
    Country,
    Disease,
    ImportBatch,
    ImportStatus,
    SourceSystem,
)
from urllib.parse import urlparse

class PublicDatasetService:
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    REQUIRED_MAPPING_KEYS = {"country_iso", "date", "daily_cases"}

    @staticmethod
    def _validate_csv_mapping(mapping: Dict[str, str]) -> None:
        missing = PublicDatasetService.REQUIRED_MAPPING_KEYS - mapping.keys()
        if missing:
            raise ValueError(f"CSV mapping is missing required keys: {', '.join(sorted(missing))}")
        if any(
            not isinstance(key, str)
            or not isinstance(value, str)
            or not key.strip()
            or not value.strip()
            or len(value) > 255
            for key, value in mapping.items()
        ):
            raise ValueError("CSV mapping keys and column names must be non-empty strings of 255 characters or fewer.")

    @staticmethod
    def _get_or_create_source_system(db: Session, code: str, name: str, system_type: str) -> SourceSystem:
        source = db.query(SourceSystem).filter(SourceSystem.code == code).first()
        if source:
            return source
        source = SourceSystem(
            name=name,
            code=code,
            system_type=system_type,
            owner="EpiSphere",
            is_active=True,
        )
        db.add(source)
        db.flush()
        return source

    @staticmethod
    def _start_batch(
        db: Session,
        source_system: SourceSystem,
        disease_id: int,
        filename: str,
        metadata: Dict[str, Any],
    ) -> ImportBatch:
        batch = ImportBatch(
            filename=filename[:500],
            dataset_type="case_timeseries",
            status=ImportStatus.PENDING,
            source_system_id=source_system.id,
            disease_id=disease_id,
            batch_metadata=metadata,
        )
        db.add(batch)
        db.flush()
        return batch

    @staticmethod
    def _validate_public_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Dataset URL must be an absolute HTTP(S) URL.")
        hostname = parsed.hostname.lower()
        if hostname in {"localhost", "localhost.localdomain"}:
            raise ValueError("Local dataset URLs are not allowed.")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
            raise ValueError("Private or local dataset addresses are not allowed.")

    @staticmethod
    def ingest_csv_url(
        db: Session,
        url: str,
        mapping: Dict[str, str],
        disease_id: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest a public CSV from a URL.
        `mapping` should map our internal keys (country_iso, date, daily_cases, etc.) 
        to the CSV column headers.
        """
        PublicDatasetService._validate_public_url(url)
        PublicDatasetService._validate_csv_mapping(mapping)
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            raise ValueError("Disease not found")

        source_system = PublicDatasetService._get_or_create_source_system(
            db, "public_url", "Public dataset URLs", "public_dataset"
        )
        batch = PublicDatasetService._start_batch(
            db,
            source_system,
            disease_id,
            url.rsplit("/", 1)[-1] or "public-dataset.csv",
            {"url": url, "mapping": mapping, "dry_run": dry_run},
        )
        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            if len(response.content) > PublicDatasetService.MAX_DOWNLOAD_BYTES:
                raise ValueError("Dataset exceeds the 25 MB download limit.")
        except Exception as e:
            batch.status = ImportStatus.FAILED
            batch.error_count = 1
            db.commit()
            raise ValueError(f"Failed to fetch CSV: {str(e)}")

        reader = csv.DictReader(io.StringIO(response.text))
        rows_total = 0
        records_imported = 0
        errors = []
        warnings = []
        
        # Pre-fetch countries
        countries = db.query(Country).all()
        country_map = {c.iso_code.upper(): c.id for c in countries if c.iso_code}
        country_map.update({c.iso_code_2.upper(): c.id for c in countries if c.iso_code_2})
        country_map.update({c.name.upper(): c.id for c in countries if c.name})

        # Columns expected in mapping:
        # country_iso -> CSV column name for country
        # date -> CSV column name for date
        # daily_cases -> CSV column name for cases
        # daily_deaths -> CSV column name for deaths

        for i, row in enumerate(reader):
            rows_total += 1
            try:
                # Resolve country
                country_raw = row.get(mapping.get('country_iso', ''))
                if not country_raw:
                    warnings.append(f"Row {i + 1}: country value is missing")
                    continue
                
                c_id = country_map.get(str(country_raw).strip().upper())
                if not c_id:
                    warnings.append(f"Row {i + 1}: country is not in the EpiSphere country registry")
                    continue

                # Resolve date
                date_raw = row.get(mapping.get('date', ''))
                if not date_raw:
                    warnings.append(f"Row {i + 1}: date value is missing")
                    continue
                
                try:
                    record_date = datetime.strptime(str(date_raw).strip(), "%Y-%m-%d").date()
                except ValueError:
                    # try ISO format or others if needed, fallback to skipping
                    warnings.append(f"Row {i + 1}: date is not in YYYY-MM-DD format")
                    continue

                cases_raw = row.get(mapping.get('daily_cases', ''))
                deaths_raw = row.get(mapping.get('daily_deaths', ''))
                
                daily_cases = int(cases_raw) if cases_raw and str(cases_raw).isdigit() else 0
                daily_deaths = int(deaths_raw) if deaths_raw and str(deaths_raw).isdigit() else 0

                if not dry_run:
                    # Upsert logic
                    existing_case = db.query(Case).filter(
                        Case.country_id == c_id,
                        Case.disease_id == disease_id,
                        Case.date == record_date
                    ).first()

                    if existing_case:
                        existing_case.daily_cases = daily_cases
                        existing_case.daily_deaths = daily_deaths
                        existing_case.source = f"Public URL Ingest ({url})"
                        existing_case.source_system_id = source_system.id
                        existing_case.import_batch_id = batch.id
                    else:
                        new_case = Case(
                            country_id=c_id,
                            disease_id=disease_id,
                            date=record_date,
                            daily_cases=daily_cases,
                            daily_deaths=daily_deaths,
                            source=f"Public URL Ingest ({url})",
                            source_system_id=source_system.id,
                            import_batch_id=batch.id,
                        )
                        db.add(new_case)
                
                records_imported += 1
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")

        batch.rows_total = rows_total
        batch.rows_valid = records_imported
        batch.rows_committed = records_imported if not dry_run else 0
        batch.warning_count = len(warnings)
        batch.error_count = len(errors)
        batch.quality_score = round((records_imported / rows_total) * 100, 2) if rows_total else 0.0
        batch.status = ImportStatus.VALIDATED if dry_run else (ImportStatus.FAILED if errors else ImportStatus.COMMITTED)
        if not dry_run and not errors:
            batch.committed_at = datetime.utcnow()

        db.commit()

        return {
            "success": not errors,
            "records_imported": records_imported,
            "errors": errors[:10],
            "warnings": warnings[:10],
            "batch_id": batch.id,
        }

    @staticmethod
    def ingest_who_gho(
        db: Session,
        indicator_code: str,
        disease_id: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Ingests data from WHO Global Health Observatory Athena API.
        `indicator_code` e.g., 'CHOLERA_0000000001'
        """
        url = f"https://ghoapi.azureedge.net/api/{indicator_code}"
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            raise ValueError("Disease not found")
        source_system = PublicDatasetService._get_or_create_source_system(
            db, "who_gho", "WHO Global Health Observatory", "public_api"
        )
        batch = PublicDatasetService._start_batch(
            db,
            source_system,
            disease_id,
            f"{indicator_code}.json",
            {"indicator_code": indicator_code, "url": url, "dry_run": dry_run},
        )
        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            batch.status = ImportStatus.FAILED
            batch.error_count = 1
            db.commit()
            raise ValueError(f"Failed to fetch WHO data: {str(e)}")

        values = data.get("value", [])
        rows_total = len(values)
        records_imported = 0
        warnings = []
        
        # Pre-fetch countries
        countries = db.query(Country).all()
        country_map = {c.iso_code.upper(): c.id for c in countries if c.iso_code}

        for item in values:
            try:
                spatial_dim = item.get('SpatialDim')
                time_dim = item.get('TimeDim')
                numeric_val = item.get('NumericValue')

                if not spatial_dim or not time_dim or numeric_val is None:
                    warnings.append("WHO row is missing country, time, or numeric value")
                    continue
                
                c_id = country_map.get(str(spatial_dim).strip().upper())
                if not c_id:
                    warnings.append(f"WHO country {spatial_dim} is not in the EpiSphere country registry")
                    continue

                # WHO GHO usually returns Year like "2020" or Date
                record_date = None
                if len(str(time_dim)) == 4:
                    record_date = datetime.strptime(f"{time_dim}-01-01", "%Y-%m-%d").date()
                else:
                    try:
                        record_date = datetime.strptime(str(time_dim).strip(), "%Y-%m-%d").date()
                    except:
                        continue
                
                daily_cases = int(numeric_val)

                if not dry_run:
                    existing_case = db.query(Case).filter(
                        Case.country_id == c_id,
                        Case.disease_id == disease_id,
                        Case.date == record_date
                    ).first()

                    if existing_case:
                        existing_case.daily_cases = daily_cases
                        existing_case.source = "WHO GHO API"
                        existing_case.source_system_id = source_system.id
                        existing_case.import_batch_id = batch.id
                    else:
                        new_case = Case(
                            country_id=c_id,
                            disease_id=disease_id,
                            date=record_date,
                            daily_cases=daily_cases,
                            source="WHO GHO API",
                            source_system_id=source_system.id,
                            import_batch_id=batch.id,
                        )
                        db.add(new_case)
                        
                records_imported += 1
            except Exception as exc:
                warnings.append(f"WHO row could not be parsed: {exc}")
                continue

        batch.rows_total = rows_total
        batch.rows_valid = records_imported
        batch.rows_committed = records_imported if not dry_run else 0
        batch.warning_count = len(warnings)
        batch.quality_score = round((records_imported / rows_total) * 100, 2) if rows_total else 0.0
        batch.status = ImportStatus.VALIDATED if dry_run else ImportStatus.COMMITTED
        if not dry_run:
            batch.committed_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "records_imported": records_imported,
            "errors": [],
            "warnings": warnings[:10],
            "batch_id": batch.id,
        }
