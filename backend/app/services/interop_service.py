from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
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
    ImportStatus,
    InteropDirection,
    InteropLog,
    InteropStatus,
    SourceSystem,
    User,
)
from datetime import datetime

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
            batch_metadata={"dataset_id": dataset_id, "org_unit": org_unit, "period": period, "dry_run": dry_run},
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

            for dv in data_values:
                dhis2_element = dv.get("dataElement")
                value = dv.get("value")
                
                disease_id = mapping.get(dhis2_element)
                if not disease_id:
                    continue
                
                try:
                    cases_count = int(value)
                except (ValueError, TypeError):
                    continue

                source_record_id = hashlib.sha256(
                    f"dhis2|{dataset_id}|{org_unit}|{period}|{country_id}|{disease_id}|{dhis2_element}".encode("utf-8")
                ).hexdigest()
                case_record = db.query(Case).filter(
                    Case.source_system_id == source_system.id,
                    Case.source_record_id == source_record_id,
                ).first()

                if case_record:
                    case_record.daily_cases = cases_count
                    case_record.import_batch_id = batch.id
                else:
                    new_case = Case(
                        country_id=country_id,
                        disease_id=disease_id,
                        date=record_date,
                        daily_cases=cases_count,
                        source="DHIS2 Integration",
                        source_system_id=source_system.id,
                        source_record_id=source_record_id,
                        import_batch_id=batch.id,
                    )
                    db.add(new_case)
                records_imported += 1

            batch.rows_total = len(data_values)
            batch.rows_valid = records_imported
            batch.rows_committed = records_imported
            batch.status = ImportStatus.COMMITTED
            batch.committed_at = datetime.utcnow()
            log.status = InteropStatus.SUCCESS
            log.details = {
                **(log.details or {}),
                "records_imported": records_imported,
                "response_preview": str(data)[:500],
                "attempts": attempts,
            }
            db.commit()

            return {
                "success": True,
                "status": log.status.value,
                "log_id": log.id,
                "records_imported": records_imported,
                "dry_run": False,
                "errors": [],
                "message": f"Successfully imported {records_imported} records from DHIS2.",
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
