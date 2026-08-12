from sqlalchemy.orm import Session
from typing import Dict, Any, Mapping, Optional
import re
import hashlib
import json
import time

import httpx

from app.core.config import settings
from app.db.models import (
    Case,
    Country,
    Disease,
    DHIS2Mapping,
    ImportBatch,
    ImportRowError,
    ImportStatus,
    InteropDirection,
    InteropLog,
    InteropStatus,
    SourceSystem,
    User,
    DataQualityCheck,
    QualitySeverity,
)
from datetime import datetime
from app.services.data_upload import DataUploadService

class InteropService:
    DEFAULT_REQUIRED_FIELDS = {
        "aggregate": ["dataValues"],
        "event": ["events"],
        "tracker": ["trackedEntityInstances"],
    }

    @staticmethod
    def _payload_hash(payload: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _request_with_retry(method: str, endpoint: str, *, attempts: int, **kwargs):
        last_error = None
        for attempt in range(max(1, attempts)):
            try:
                response = getattr(httpx, method)(endpoint, **kwargs)
                response.raise_for_status()
                return response, attempt + 1
            except Exception as exc:
                last_error = exc
                if attempt + 1 < max(1, attempts):
                    time.sleep(min(2 ** attempt, 4))
        raise last_error

    @staticmethod
    def _record_pull_quality(
        db: Session,
        batch: ImportBatch,
        records_total: int,
        records_valid: int,
        warnings: list[str],
    ) -> None:
        """Keep DHIS2 validation and quality evidence in the common import lineage."""
        validity_rate = records_valid / records_total if records_total else 0.0
        db.add_all([
            DataQualityCheck(
                batch_id=batch.id,
                check_name="row_validity_rate",
                severity=QualitySeverity.ERROR,
                passed=validity_rate >= 0.95,
                metric_value=validity_rate,
                threshold=0.95,
                message=f"{validity_rate:.0%} of DHIS2 values passed mapping and numeric validation",
            ),
            DataQualityCheck(
                batch_id=batch.id,
                check_name="unmapped_or_invalid_rows",
                severity=QualitySeverity.WARNING,
                passed=not warnings,
                metric_value=float(len(warnings)),
                threshold=0.0,
                message=f"{len(warnings)} DHIS2 value(s) were unmapped, invalid, or duplicated",
            ),
        ])
        for message in warnings:
            db.add(ImportRowError(
                batch_id=batch.id,
                row_number=0,
                severity=QualitySeverity.WARNING,
                message=message,
            ))

    @staticmethod
    def sync_to_dhis2(
        db: Session,
        user: User,
        payload: Dict[str, Any],
        dataset: str,
        mapping_id: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Synchronize a validated payload to DHIS2 or record a dry-run."""
        mapping, errors = InteropService._resolve_mapping(db, dataset, mapping_id)
        if not errors:
            errors = InteropService._validate_payload(payload, mapping)

        endpoint_path = mapping.endpoint_path if mapping else dataset.strip("/")
        payload_hash = InteropService._payload_hash(payload)
        if not dry_run:
            recent_successes = db.query(InteropLog).filter(
                InteropLog.system_name == "DHIS2",
                InteropLog.direction == InteropDirection.OUTBOUND,
                InteropLog.status == InteropStatus.SUCCESS,
            ).order_by(InteropLog.timestamp.desc()).limit(100).all()
            for previous in recent_successes:
                if (previous.details or {}).get("payload_hash") == payload_hash and (previous.details or {}).get("dataset") == dataset:
                    return {
                        "success": True,
                        "status": previous.status.value,
                        "log_id": previous.id,
                        "dry_run": False,
                        "errors": [],
                        "message": "DHIS2 payload already exchanged; returning the previous successful log.",
                        "replayed": True,
                    }
        log = InteropLog(
            system_name="DHIS2",
            direction=InteropDirection.OUTBOUND,
            status=InteropStatus.PENDING,
            dataset_type=dataset,
            mapping_id=mapping.id if mapping else None,
            details={
                "triggered_by": user.username,
                "payload_size": len(str(payload)),
                "mapping": mapping.dataset if mapping else "default_shape_validation",
                "dry_run_requested": dry_run,
                "dataset": dataset,
                "payload_hash": payload_hash,
            },
        )
        db.add(log)
        db.flush()

        if errors:
            log.status = InteropStatus.FAILURE
            log.details = {**(log.details or {}), "validation_errors": errors}
            db.commit()
            return {
                "success": False,
                "status": log.status.value,
                "log_id": log.id,
                "dry_run": True,
                "errors": errors,
                "message": "DHIS2 payload failed validation and was not sent.",
            }

        if dry_run or not settings.DHIS2_URL:
            log.status = InteropStatus.SUCCESS
            log.details = {
                **(log.details or {}),
                "dry_run": True,
                "message": "Payload validated and logged only; DHIS2_URL is not configured or dry_run was requested.",
            }
            db.commit()
            return {
                "success": True,
                "status": log.status.value,
                "log_id": log.id,
                "dry_run": True,
                "errors": [],
                "message": "DHIS2 payload validated in dry-run mode.",
            }

        try:
            endpoint = settings.DHIS2_URL.rstrip("/") + f"/{endpoint_path.strip('/')}"
            auth = None
            if settings.DHIS2_USERNAME and settings.DHIS2_PASSWORD:
                auth = (settings.DHIS2_USERNAME, settings.DHIS2_PASSWORD)

            response, attempts = InteropService._request_with_retry(
                "post",
                endpoint,
                json=payload,
                auth=auth,
                timeout=settings.DHIS2_TIMEOUT_SECONDS,
                attempts=settings.DHIS2_MAX_RETRIES,
            )
            log.status = InteropStatus.SUCCESS
            log.external_id = response.headers.get("Location") or response.headers.get("X-Request-ID")
            log.details = {
                **(log.details or {}),
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_preview": response.text[:500],
                "attempts": attempts,
            }
        except Exception as e:
            log.status = InteropStatus.FAILURE
            log.details = {**(log.details or {}), "error": str(e)}
            db.commit()
            return {
                "success": False,
                "status": log.status.value,
                "log_id": log.id,
                "dry_run": False,
                "errors": [str(e)],
                "message": "DHIS2 sync failed after validation.",
            }

        db.commit()
        return {
            "success": True,
            "status": log.status.value,
            "log_id": log.id,
            "dry_run": False,
            "errors": [],
            "message": "DHIS2 payload sent successfully.",
        }

    @staticmethod
    def pull_from_dhis2(
        db: Session,
        user: User,
        dataset_id: str,
        org_unit: str,
        period: str,
        mapping: Dict[str, int],
        country_id: int,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Pull aggregate data from DHIS2 and store it in EpiSphere."""
        log = InteropLog(
            system_name="DHIS2",
            direction=InteropDirection.INBOUND,
            status=InteropStatus.PENDING,
            dataset_type=dataset_id,
            details={
                "triggered_by": user.username,
                "org_unit": org_unit,
                "period": period,
                "dry_run": dry_run,
            },
        )
        db.add(log)
        db.flush()
        try:
            if len(period) == 6 and period.isdigit():
                # YYYYMM format
                record_date = datetime.strptime(f"{period}01", "%Y%m%d").date()
            elif len(period) == 10:
                record_date = datetime.fromisoformat(period).date()
            else:
                raise ValueError("DHIS2 period must be YYYYMM or YYYY-MM-DD")
        except (TypeError, ValueError) as exc:
            log.status = InteropStatus.FAILURE
            log.details = {**(log.details or {}), "validation_error": str(exc)}
            db.commit()
            return {
                "success": False,
                "status": log.status.value,
                "log_id": log.id,
                "records_imported": 0,
                "dry_run": True,
                "errors": [str(exc)],
                "message": "DHIS2 period failed validation and was not requested.",
            }

        country = db.query(Country).filter(Country.id == country_id).first()
        if not country:
            error = "Country not found"
            log.status = InteropStatus.FAILURE
            log.details = {**(log.details or {}), "validation_error": error}
            db.commit()
            return {"success": False, "status": log.status.value, "log_id": log.id, "records_imported": 0, "dry_run": True, "errors": [error], "message": error}

        disease_ids = set(mapping.values())
        known_disease_ids = {row.id for row in db.query(Disease.id).filter(Disease.id.in_(disease_ids)).all()}
        unknown_disease_ids = sorted(disease_ids - known_disease_ids)
        if unknown_disease_ids:
            error = f"Unknown disease IDs in DHIS2 mapping: {unknown_disease_ids}"
            log.status = InteropStatus.FAILURE
            log.details = {**(log.details or {}), "validation_error": error}
            db.commit()
            return {"success": False, "status": log.status.value, "log_id": log.id, "records_imported": 0, "dry_run": True, "errors": [error], "message": error}

        source_system = db.query(SourceSystem).filter(SourceSystem.code == "dhis2").first()
        if not source_system:
            source_system = SourceSystem(name="DHIS2", code="dhis2", system_type="interop", owner="DHIS2", is_active=True)
            db.add(source_system)
            db.flush()
        batch = ImportBatch(
            filename=f"{dataset_id}_{org_unit}_{period}",
            dataset_type="dhis2_aggregate",
            status=ImportStatus.PENDING,
            source_system_id=source_system.id,
            country_id=country_id,
            batch_metadata={
                "dataset_id": dataset_id,
                "org_unit": org_unit,
                "period": period,
                "mapping": mapping,
                "mapping_sha256": InteropService._payload_hash(mapping),
                "mapping_version": "dhis2-pull-v1",
                "dataset_contract_version": "case_timeseries/v1",
                "transformation_version": "dhis2_aggregate/v1",
                "dry_run": dry_run,
                "require_review": True,
                "approval_scope": "admin",
            },
        )
        db.add(batch)
        db.flush()

        if dry_run or not settings.DHIS2_URL:
            log.status = InteropStatus.SUCCESS
            batch.status = ImportStatus.VALIDATED
            log.details = {**(log.details or {}), "message": "Dry run or DHIS2_URL not configured."}
            db.commit()
            return {
                "success": True,
                "status": log.status.value,
                "log_id": log.id,
                "records_imported": 0,
                "dry_run": True,
                "errors": [],
                "message": "DHIS2 pull simulated (dry-run).",
            }

        try:
            endpoint = settings.DHIS2_URL.rstrip("/") + "/api/dataValueSets"
            params = {
                "dataSet": dataset_id,
                "period": period,
                "orgUnit": org_unit
            }
            auth = None
            if settings.DHIS2_USERNAME and settings.DHIS2_PASSWORD:
                auth = (settings.DHIS2_USERNAME, settings.DHIS2_PASSWORD)

            response, attempts = InteropService._request_with_retry(
                "get",
                endpoint,
                params=params,
                auth=auth,
                timeout=settings.DHIS2_TIMEOUT_SECONDS,
                attempts=settings.DHIS2_MAX_RETRIES,
            )
            data = response.json()
            
            data_values = data.get("dataValues", [])
            records_imported = 0
            warnings: list[str] = []
            validated_cases: list[Case] = []
            seen_source_records: set[str] = set()

            for row_number, dv in enumerate(data_values, start=1):
                dhis2_element = dv.get("dataElement")
                value = dv.get("value")
                
                disease_id = mapping.get(dhis2_element)
                if not disease_id:
                    warnings.append(f"Row {row_number}: DHIS2 data element is not mapped to a disease")
                    continue
                
                try:
                    cases_count = int(value)
                except (ValueError, TypeError):
                    warnings.append(f"Row {row_number}: DHIS2 value is not a valid integer")
                    continue
                if cases_count < 0:
                    warnings.append(f"Row {row_number}: DHIS2 value cannot be negative")
                    continue

                source_record_id = hashlib.sha256(
                    f"dhis2|{dataset_id}|{org_unit}|{period}|{country_id}|{disease_id}|{dhis2_element}".encode("utf-8")
                ).hexdigest()
                if source_record_id in seen_source_records:
                    warnings.append(f"Row {row_number}: duplicate DHIS2 source value")
                    continue
                seen_source_records.add(source_record_id)
                validated_cases.append(Case(
                    country_id=country_id,
                    disease_id=disease_id,
                    date=record_date,
                    daily_cases=cases_count,
                    cumulative_cases=0,
                    daily_deaths=0,
                    cumulative_deaths=0,
                    source="DHIS2 Integration",
                    source_system_id=source_system.id,
                    source_record_id=source_record_id,
                    import_batch_id=batch.id,
                    reporting_level="national",
                ))
                records_imported += 1

            batch.rows_total = len(data_values)
            batch.rows_valid = records_imported
            batch.rows_committed = 0
            batch.warning_count = len(warnings)
            batch.error_count = 0
            batch.quality_score = round((records_imported / len(data_values)) * 100, 2) if data_values else 0.0
            response_headers = getattr(response, "headers", {})
            source_last_modified = response_headers.get("last-modified") if isinstance(response_headers, Mapping) else None
            batch.batch_metadata = {
                **(batch.batch_metadata or {}),
                "source_last_modified": source_last_modified,
                "response_sha256": InteropService._payload_hash(data),
            }
            DataUploadService(db)._stage_cases(batch, validated_cases)
            batch.status = ImportStatus.VALIDATED
            InteropService._record_pull_quality(db, batch, len(data_values), records_imported, warnings)
            log.status = InteropStatus.SUCCESS
            log.details = {
                **(log.details or {}),
                "records_imported": records_imported,
                "records_staged": len(validated_cases),
                "response_preview": str(data)[:500],
                "attempts": attempts,
            }
            db.commit()

            return {
                "success": True,
                "status": log.status.value,
                "log_id": log.id,
                "records_imported": records_imported,
                "records_staged": len(validated_cases),
                "batch_id": batch.id,
                "dry_run": False,
                "errors": [],
                "message": f"Validated and staged {records_imported} records from DHIS2 for administrator approval.",
            }

        except Exception as e:
            batch.status = ImportStatus.FAILED
            batch.error_count = 1
            log.status = InteropStatus.FAILURE
            log.details = {**(log.details or {}), "error": str(e)}
            db.commit()
            return {
                "success": False,
                "status": log.status.value,
                "log_id": log.id,
                "records_imported": 0,
                "dry_run": False,
                "errors": [str(e)],
                "message": "Failed to pull data from DHIS2.",
            }

    @staticmethod
    def _resolve_mapping(db: Session, dataset: str, mapping_id: Optional[int]) -> tuple[Optional[DHIS2Mapping], list[str]]:
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", dataset or ""):
            return None, ["Dataset may only contain letters, numbers, slash, dot, dash, and underscore."]

        query = db.query(DHIS2Mapping).filter(DHIS2Mapping.is_active.is_(True))
        if mapping_id:
            mapping = query.filter(DHIS2Mapping.id == mapping_id).first()
            if not mapping:
                return None, ["DHIS2 mapping not found or inactive."]
            if mapping.dataset != dataset:
                return None, ["Mapping dataset does not match request dataset."]
            return mapping, []

        mapping = query.filter(DHIS2Mapping.dataset == dataset).first()
        return mapping, []

    @staticmethod
    def _validate_payload(payload: Dict[str, Any], mapping: Optional[DHIS2Mapping]) -> list[str]:
        if not isinstance(payload, dict) or not payload:
            return ["Payload must be a non-empty JSON object."]

        if mapping:
            required_fields = mapping.required_fields or []
            payload_type = mapping.payload_type
        else:
            if "dataValues" in payload:
                payload_type = "aggregate"
            elif "events" in payload:
                payload_type = "event"
            elif "trackedEntityInstances" in payload:
                payload_type = "tracker"
            else:
                payload_type = "aggregate"
            required_fields = InteropService.DEFAULT_REQUIRED_FIELDS[payload_type]

        errors = [f"Missing required DHIS2 field: {field}" for field in required_fields if field not in payload]

        if payload_type == "aggregate" and "dataValues" in payload and not isinstance(payload["dataValues"], list):
            errors.append("dataValues must be a list.")
        if payload_type == "event" and "events" in payload and not isinstance(payload["events"], list):
            errors.append("events must be a list.")
        if payload_type == "tracker" and "trackedEntityInstances" in payload and not isinstance(payload["trackedEntityInstances"], list):
            errors.append("trackedEntityInstances must be a list.")

        return errors
