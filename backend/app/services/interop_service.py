from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import re

import httpx

from app.core.config import settings
from app.db.models import InteropLog, InteropDirection, InteropStatus, User, DHIS2Mapping, Case
from datetime import datetime

class InteropService:
    DEFAULT_REQUIRED_FIELDS = {
        "aggregate": ["dataValues"],
        "event": ["events"],
        "tracker": ["trackedEntityInstances"],
    }

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

            response = httpx.post(
                endpoint,
                json=payload,
                auth=auth,
                timeout=settings.DHIS2_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            log.status = InteropStatus.SUCCESS
            log.external_id = response.headers.get("Location") or response.headers.get("X-Request-ID")
            log.details = {
                **(log.details or {}),
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_preview": response.text[:500],
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
        try:
            if len(period) == 6 and period.isdigit():
                # YYYYMM format
                record_date = datetime.strptime(f"{period}01", "%Y%m%d").date()
            else:
                # Assume ISO format or fallback to today
                record_date = datetime.fromisoformat(period).date()
        except ValueError:
            record_date = datetime.utcnow().date()

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

        if dry_run or not settings.DHIS2_URL:
            log.status = InteropStatus.SUCCESS
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

            response = httpx.get(
                endpoint,
                params=params,
                auth=auth,
                timeout=settings.DHIS2_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
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

                case_record = db.query(Case).filter(
                    Case.country_id == country_id,
                    Case.disease_id == disease_id,
                    Case.date == record_date,
                    Case.source == "DHIS2 Integration"
                ).first()

                if case_record:
                    case_record.daily_cases = cases_count
                else:
                    new_case = Case(
                        country_id=country_id,
                        disease_id=disease_id,
                        date=record_date,
                        daily_cases=cases_count,
                        source="DHIS2 Integration"
                    )
                    db.add(new_case)
                records_imported += 1

            log.status = InteropStatus.SUCCESS
            log.details = {
                **(log.details or {}),
                "records_imported": records_imported,
                "response_preview": str(data)[:500]
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
