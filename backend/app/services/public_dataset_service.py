import httpx
import csv
import io
import ipaddress
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.db.models import Case, Country, Disease
from urllib.parse import urlparse

class PublicDatasetService:
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024

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
        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            if len(response.content) > PublicDatasetService.MAX_DOWNLOAD_BYTES:
                raise ValueError("Dataset exceeds the 25 MB download limit.")
        except Exception as e:
            raise ValueError(f"Failed to fetch CSV: {str(e)}")

        reader = csv.DictReader(io.StringIO(response.text))
        
        records_imported = 0
        errors = []
        
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
            try:
                # Resolve country
                country_raw = row.get(mapping.get('country_iso', ''))
                if not country_raw:
                    continue
                
                c_id = country_map.get(str(country_raw).strip().upper())
                if not c_id:
                    continue

                # Resolve date
                date_raw = row.get(mapping.get('date', ''))
                if not date_raw:
                    continue
                
                try:
                    record_date = datetime.strptime(str(date_raw).strip(), "%Y-%m-%d").date()
                except ValueError:
                    # try ISO format or others if needed, fallback to skipping
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
                    else:
                        new_case = Case(
                            country_id=c_id,
                            disease_id=disease_id,
                            date=record_date,
                            daily_cases=daily_cases,
                            daily_deaths=daily_deaths,
                            source=f"Public URL Ingest ({url})"
                        )
                        db.add(new_case)
                
                records_imported += 1
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")

        if not dry_run:
            db.commit()

        return {
            "success": True,
            "records_imported": records_imported,
            "errors": errors[:10] # limit returned errors
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
        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise ValueError(f"Failed to fetch WHO data: {str(e)}")

        values = data.get("value", [])
        records_imported = 0
        
        # Pre-fetch countries
        countries = db.query(Country).all()
        country_map = {c.iso_code.upper(): c.id for c in countries if c.iso_code}

        for item in values:
            try:
                spatial_dim = item.get('SpatialDim')
                time_dim = item.get('TimeDim')
                numeric_val = item.get('NumericValue')

                if not spatial_dim or not time_dim or numeric_val is None:
                    continue
                
                c_id = country_map.get(str(spatial_dim).strip().upper())
                if not c_id:
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
                    else:
                        new_case = Case(
                            country_id=c_id,
                            disease_id=disease_id,
                            date=record_date,
                            daily_cases=daily_cases,
                            source="WHO GHO API"
                        )
                        db.add(new_case)
                        
                records_imported += 1
            except Exception:
                continue

        if not dry_run:
            db.commit()

        return {
            "success": True,
            "records_imported": records_imported,
            "errors": []
        }
