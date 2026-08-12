import httpx
import csv
import io
import ipaddress
import json
import hashlib
import re
import socket
from datetime import date, datetime
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.models import (
    Case,
    Country,
    Disease,
    ImportBatch,
    ImportRowError,
    ImportStatus,
    SourceSystem,
    DataQualityCheck,
    QualitySeverity,
)
from urllib.parse import urljoin, urlparse
from app.core.config import settings
from app.services.data_upload import DataUploadService

class PublicDatasetService:
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    REQUIRED_MAPPING_KEYS = {"country_iso", "date", "daily_cases"}
    MIN_VALIDITY_RATE = 0.95
    MAX_TIMELINESS_LAG_DAYS = 14

    @staticmethod
    def _source_record_id(*parts: Any) -> str:
        return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()

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
    def _is_private_address(hostname: str) -> bool:
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            return False
        return any((
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_reserved,
            address.is_multicast,
            address.is_unspecified,
        ))

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

    @classmethod
    def _add_quality_checks(
        cls,
        db: Session,
        batch_id: int,
        rows_total: int,
        rows_valid: int,
        duplicate_rows: int,
        record_dates: list[date],
    ) -> None:
        """Persist shared quality signals for every public-source import batch."""
        validity_rate = rows_valid / rows_total if rows_total else 0.0
        latest_date = max(record_dates) if record_dates else None
        lag_days = (date.today() - latest_date).days if latest_date else None
        checks = (
            DataQualityCheck(
                batch_id=batch_id,
                check_name="row_validity_rate",
                severity=QualitySeverity.ERROR,
                passed=validity_rate >= cls.MIN_VALIDITY_RATE,
                metric_value=validity_rate,
                threshold=cls.MIN_VALIDITY_RATE,
                message=f"{validity_rate:.0%} of source rows passed validation",
            ),
            DataQualityCheck(
                batch_id=batch_id,
                check_name="duplicate_source_rows",
                severity=QualitySeverity.WARNING,
                passed=duplicate_rows == 0,
                metric_value=float(duplicate_rows),
                threshold=0.0,
                message=f"{duplicate_rows} duplicate source row(s) found",
            ),
            DataQualityCheck(
                batch_id=batch_id,
                check_name="timeliness",
                severity=QualitySeverity.WARNING,
                passed=lag_days is not None and lag_days <= cls.MAX_TIMELINESS_LAG_DAYS,
                metric_value=float(lag_days) if lag_days is not None else None,
                threshold=float(cls.MAX_TIMELINESS_LAG_DAYS),
                message=(
                    f"Latest record is within {cls.MAX_TIMELINESS_LAG_DAYS} days"
                    if lag_days is not None and lag_days <= cls.MAX_TIMELINESS_LAG_DAYS
                    else "Latest record is older than the configured timeliness threshold or unavailable"
                ),
            ),
        )
        db.add_all(checks)

    @staticmethod
    def _add_row_issues(db: Session, batch_id: int, errors: list[str], warnings: list[str]) -> None:
        """Persist external-source validation evidence alongside its import batch."""
        for severity, messages in ((QualitySeverity.ERROR, errors), (QualitySeverity.WARNING, warnings)):
            for message in messages:
                match = re.match(r"(?:Row )?(\\d+)(?::|\\s)", message)
                db.add(ImportRowError(
                    batch_id=batch_id,
                    row_number=int(match.group(1)) if match else 0,
                    severity=severity,
                    message=message,
                ))

    @staticmethod
    def _validate_public_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Dataset URL must be an absolute HTTP(S) URL.")
        hostname = parsed.hostname.lower().rstrip(".")
        allowed_hosts = {host.lower().strip().rstrip(".") for host in settings.PUBLIC_DATASET_ALLOWED_HOSTS}
        if hostname not in allowed_hosts:
            raise ValueError("Dataset host is not in the approved public-source allowlist.")
        if PublicDatasetService._is_private_address(hostname):
            raise ValueError("Private or local dataset addresses are not allowed.")
        try:
            resolved = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except (socket.gaierror, ValueError) as exc:
            raise ValueError("Dataset host could not be resolved safely.") from exc
        if not resolved or any(PublicDatasetService._is_private_address(info[4][0].split("%", 1)[0]) for info in resolved):
            raise ValueError("Dataset host resolves to a private or local address.")

    @classmethod
    def _download_public_url(cls, url: str) -> tuple[bytes, str, Dict[str, str]]:
        """Download a public source while validating every redirect and byte limit."""
        current_url = url
        for redirect_number in range(settings.PUBLIC_DATASET_MAX_REDIRECTS + 1):
            cls._validate_public_url(current_url)
            with httpx.Client(timeout=30.0, follow_redirects=False) as client:
                with client.stream("GET", current_url, follow_redirects=False) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise ValueError("Dataset redirect did not include a location.")
                        if redirect_number >= settings.PUBLIC_DATASET_MAX_REDIRECTS:
                            raise ValueError("Dataset exceeded the maximum redirect count.")
                        current_url = urljoin(current_url, location)
                        continue

                    response.raise_for_status()
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > cls.MAX_DOWNLOAD_BYTES:
                        raise ValueError("Dataset exceeds the 25 MB download limit.")
                    chunks: list[bytes] = []
                    total_bytes = 0
                    for chunk in response.iter_bytes(64 * 1024):
                        total_bytes += len(chunk)
                        if total_bytes > cls.MAX_DOWNLOAD_BYTES:
                            raise ValueError("Dataset exceeds the 25 MB download limit.")
                        chunks.append(chunk)
                    return b"".join(chunks), current_url, dict(response.headers)
        raise ValueError("Dataset redirect handling failed.")

    @staticmethod
    def ingest_csv_url(
        db: Session,
        url: str,
        mapping: Dict[str, str],
        disease_id: int,
        mapping_version: str = "v1",
        dry_run: bool = False,
        require_review: bool = True,
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
            {
                "url": url,
                "mapping": mapping,
                "mapping_version": mapping_version,
                "mapping_sha256": hashlib.sha256(json.dumps(mapping, sort_keys=True).encode("utf-8")).hexdigest(),
                "dataset_contract_version": "case_timeseries/v1",
                "transformation_version": "public_csv/v1",
                "dry_run": dry_run,
                "require_review": require_review,
                "approval_scope": "admin" if require_review else None,
            },
        )
        try:
            content, final_url, response_headers = PublicDatasetService._download_public_url(url)
            if content.count(b"\n") > settings.PUBLIC_DATASET_MAX_ROWS + 1:
                raise ValueError("Dataset exceeds the configured row limit.")
            batch.batch_metadata = {
                **(batch.batch_metadata or {}),
                "final_url": final_url,
                "content_length": len(content),
                "content_type": response_headers.get("content-type"),
                "source_last_modified": response_headers.get("last-modified"),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        except Exception as e:
            batch.status = ImportStatus.FAILED
            batch.error_count = 1
            db.commit()
            raise ValueError(f"Failed to fetch CSV: {str(e)}")

        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        rows_total = 0
        records_imported = 0
        errors = []
        warnings = []
        validated_cases: list[Case] = []
        source_keys: set[tuple[int, Any]] = set()
        record_dates: list[date] = []
        duplicate_rows = 0
        
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

                source_key = (c_id, record_date)
                if source_key in source_keys:
                    duplicate_rows += 1
                    warnings.append(f"Row {i + 1}: duplicate country/date source row")
                    continue
                source_keys.add(source_key)

                cases_raw = row.get(mapping.get('daily_cases', ''))
                deaths_raw = row.get(mapping.get('daily_deaths', ''))
                
                daily_cases = int(cases_raw) if cases_raw and str(cases_raw).isdigit() else 0
                daily_deaths = int(deaths_raw) if deaths_raw and str(deaths_raw).isdigit() else 0

                source_record_id = PublicDatasetService._source_record_id(
                    "public_url", url, c_id, disease_id, record_date
                )
                validated_cases.append(Case(
                    country_id=c_id,
                    disease_id=disease_id,
                    date=record_date,
                    daily_cases=daily_cases,
                    cumulative_cases=0,
                    daily_deaths=daily_deaths,
                    cumulative_deaths=0,
                    source=f"Public URL Ingest ({url})",
                    source_system_id=source_system.id,
                    source_record_id=source_record_id,
                    import_batch_id=batch.id,
                ))
                
                records_imported += 1
                record_dates.append(record_date)
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")

        batch.rows_total = rows_total
        batch.rows_valid = records_imported
        batch.rows_committed = 0
        batch.warning_count = len(warnings)
        batch.error_count = len(errors)
        batch.quality_score = round((records_imported / rows_total) * 100, 2) if rows_total else 0.0
        records_staged = 0
        committed_count = 0
        if errors:
            batch.status = ImportStatus.FAILED
        elif dry_run:
            batch.status = ImportStatus.VALIDATED
        elif require_review:
            DataUploadService(db)._stage_cases(batch, validated_cases)
            records_staged = len(validated_cases)
            batch.status = ImportStatus.VALIDATED
        else:
            committed_count = DataUploadService(db)._commit_cases(validated_cases)
            batch.rows_committed = committed_count
            batch.committed_at = datetime.utcnow()
            batch.status = ImportStatus.COMMITTED
        PublicDatasetService._add_row_issues(db, batch.id, errors, warnings)
        PublicDatasetService._add_quality_checks(
            db, batch.id, rows_total, records_imported, duplicate_rows, record_dates
        )

        db.commit()

        return {
            "success": not errors,
            "records_imported": records_imported,
            "records_staged": records_staged,
            "errors": errors[:10],
            "warnings": warnings[:10],
            "batch_id": batch.id,
        }

    @staticmethod
    def ingest_who_gho(
        db: Session,
        indicator_code: str,
        disease_id: int,
        mapping_version: str = "who-gho-v1",
        dry_run: bool = False,
        require_review: bool = True,
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
            {
                "indicator_code": indicator_code,
                "url": url,
                "mapping_version": mapping_version,
                "dataset_contract_version": "case_timeseries/v1",
                "transformation_version": "who_gho/v1",
                "dry_run": dry_run,
                "require_review": require_review,
                "approval_scope": "admin" if require_review else None,
            },
        )
        try:
            content, final_url, response_headers = PublicDatasetService._download_public_url(url)
            if len(content) > PublicDatasetService.MAX_DOWNLOAD_BYTES:
                raise ValueError("Dataset exceeds the 25 MB download limit.")
            batch.batch_metadata = {
                **(batch.batch_metadata or {}),
                "final_url": final_url,
                "content_length": len(content),
                "content_type": response_headers.get("content-type"),
                "source_last_modified": response_headers.get("last-modified"),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            data = json.loads(content.decode("utf-8"))
        except Exception as e:
            batch.status = ImportStatus.FAILED
            batch.error_count = 1
            db.commit()
            raise ValueError(f"Failed to fetch WHO data: {str(e)}")

        values = data.get("value", [])
        if len(values) > settings.PUBLIC_DATASET_MAX_ROWS:
            batch.status = ImportStatus.FAILED
            batch.error_count = 1
            db.commit()
            raise ValueError("Dataset exceeds the configured row limit.")
        rows_total = len(values)
        records_imported = 0
        warnings = []
        errors = []
        validated_cases: list[Case] = []
        source_keys: set[tuple[int, Any]] = set()
        record_dates: list[date] = []
        duplicate_rows = 0
        
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

                source_key = (c_id, record_date)
                if source_key in source_keys:
                    duplicate_rows += 1
                    warnings.append(f"WHO row for {spatial_dim} and {record_date.isoformat()} is duplicated")
                    continue
                source_keys.add(source_key)
                
                daily_cases = int(numeric_val)

                source_record_id = PublicDatasetService._source_record_id(
                    "who_gho", indicator_code, c_id, disease_id, record_date
                )
                validated_cases.append(Case(
                    country_id=c_id,
                    disease_id=disease_id,
                    date=record_date,
                    daily_cases=daily_cases,
                    cumulative_cases=0,
                    daily_deaths=0,
                    cumulative_deaths=0,
                    source="WHO GHO API",
                    source_system_id=source_system.id,
                    source_record_id=source_record_id,
                    import_batch_id=batch.id,
                ))
                        
                records_imported += 1
                record_dates.append(record_date)
            except Exception as exc:
                warnings.append(f"WHO row could not be parsed: {exc}")
                continue

        batch.rows_total = rows_total
        batch.rows_valid = records_imported
        batch.warning_count = len(warnings)
        batch.error_count = len(errors)
        batch.quality_score = round((records_imported / rows_total) * 100, 2) if rows_total else 0.0
        records_staged = 0
        committed_count = 0
        if errors:
            batch.status = ImportStatus.FAILED
        elif dry_run:
            batch.status = ImportStatus.VALIDATED
        elif require_review:
            DataUploadService(db)._stage_cases(batch, validated_cases)
            records_staged = len(validated_cases)
            batch.status = ImportStatus.VALIDATED
        else:
            committed_count = DataUploadService(db)._commit_cases(validated_cases)
            batch.rows_committed = committed_count
            batch.committed_at = datetime.utcnow()
            batch.status = ImportStatus.COMMITTED
        PublicDatasetService._add_row_issues(db, batch.id, errors, warnings)
        PublicDatasetService._add_quality_checks(
            db, batch.id, rows_total, records_imported, duplicate_rows, record_dates
        )

        db.commit()

        return {
            "success": not errors,
            "records_imported": records_imported,
            "records_staged": records_staged,
            "errors": errors[:10],
            "warnings": warnings[:10],
            "batch_id": batch.id,
        }
