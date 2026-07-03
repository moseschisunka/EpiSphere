"""Data upload, lineage, and validation service."""

import io
from typing import Dict, Any, Optional
from datetime import datetime, date

import pandas as pd
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    Case,
    Country,
    Disease,
    AuditLog,
    AuditAction,
    SourceSystem,
    ImportBatch,
    ImportRowError,
    DataQualityCheck,
    ImportStatus,
    QualitySeverity,
)
from app.core.config import settings


class DataUploadService:
    """Service for handling data uploads with validation, lineage, and auditability."""

    REQUIRED_COLUMNS = ["date", "daily_cases"]
    OPTIONAL_COLUMNS = {
        "cumulative_cases",
        "daily_deaths",
        "cumulative_deaths",
        "daily_recovered",
        "cumulative_recovered",
        "subnational_region",
        "reporting_period_start",
        "reporting_period_end",
        "reporting_level",
        "case_definition",
        "confirmation_status",
        "source",
        "notes",
    }
    VALID_REPORTING_LEVELS = {"national", "admin1", "admin2", "facility"}
    VALID_CONFIRMATION_STATUS = {"suspected", "probable", "confirmed"}

    def __init__(self, db: Session):
        self.db = db

    async def upload_file(
        self,
        file: UploadFile,
        country_id: int,
        disease_id: int,
        user_id: int,
        commit: bool = True,
        source_system_code: str = "manual_upload",
    ) -> Dict[str, Any]:
        """Validate and optionally commit CSV/Excel case data."""
        file_ext = self._validate_file_name(file.filename)
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds maximum upload size",
            )

        df = self._read_dataframe(contents, file_ext)
        df.columns = [str(col).strip() for col in df.columns]

        country = self.db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        disease = self.db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            raise HTTPException(status_code=404, detail="Disease not found")

        source_system = self._get_or_create_source_system(source_system_code)
        batch = ImportBatch(
            filename=file.filename or "upload",
            dataset_type="case_timeseries",
            status=ImportStatus.PENDING,
            source_system_id=source_system.id,
            country_id=country_id,
            disease_id=disease_id,
            uploaded_by=user_id,
            rows_total=len(df),
            batch_metadata={
                "columns": list(df.columns),
                "commit_requested": commit,
                "country": country.iso_code,
                "disease": disease.name,
            },
        )
        self.db.add(batch)
        self.db.flush()

        issues: list[ImportRowError] = []
        quality_checks: list[DataQualityCheck] = []
        validated_cases: list[Case] = []

        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            issues.append(self._issue(batch.id, 1, None, QualitySeverity.ERROR, f"Missing required columns: {', '.join(missing_columns)}"))
        else:
            validated_cases, issues = self._validate_rows(df, batch, country_id, disease_id, source_system.id)
            quality_checks = self._build_quality_checks(batch.id, df, validated_cases, issues)

        errors = [issue for issue in issues if issue.severity == QualitySeverity.ERROR]
        warnings = [issue for issue in issues if issue.severity == QualitySeverity.WARNING]
        batch.rows_valid = len(validated_cases)
        batch.error_count = len(errors)
        batch.warning_count = len(warnings)
        batch.quality_score = self._quality_score(len(df), len(errors), len(warnings), quality_checks)

        for issue in issues:
            self.db.add(issue)
        for check in quality_checks:
            self.db.add(check)

        committed_count = 0
        if errors:
            batch.status = ImportStatus.FAILED
        elif not commit:
            batch.status = ImportStatus.VALIDATED
        else:
            committed_count = self._commit_cases(validated_cases)
            batch.rows_committed = committed_count
            batch.committed_at = datetime.utcnow()
            batch.status = ImportStatus.COMMITTED

        self.db.add(AuditLog(
            user_id=user_id,
            action=AuditAction.UPLOAD,
            resource_type="import_batch",
            resource_id=batch.id,
            details={
                "filename": file.filename,
                "rows_total": len(df),
                "rows_valid": len(validated_cases),
                "rows_committed": committed_count,
                "errors": len(errors),
                "warnings": len(warnings),
                "country_id": country_id,
                "disease_id": disease_id,
                "status": batch.status.value,
            },
        ))
        self.db.commit()
        self.db.refresh(batch)

        return self._result(batch, issues, quality_checks, committed=committed_count > 0)

    def _validate_file_name(self, filename: Optional[str]) -> str:
        if not filename or "." not in filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")

        file_ext = filename.rsplit(".", 1)[-1].lower()
        if f".{file_ext}" not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Supported: CSV, XLSX, XLS",
            )
        return file_ext

    def _read_dataframe(self, contents: bytes, file_ext: str) -> pd.DataFrame:
        try:
            if file_ext == "csv":
                return pd.read_csv(io.BytesIO(contents))
            return pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error reading file: {str(e)}")

    def _get_or_create_source_system(self, code: str) -> SourceSystem:
        normalized = code.strip().lower() or "manual_upload"
        source = self.db.query(SourceSystem).filter(SourceSystem.code == normalized).first()
        if source:
            return source
        source = SourceSystem(
            name="Manual Upload",
            code=normalized,
            system_type="manual_upload",
            owner="EpiSphere",
            is_active=True,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def _validate_rows(
        self,
        df: pd.DataFrame,
        batch: ImportBatch,
        country_id: int,
        disease_id: int,
        source_system_id: int,
    ) -> tuple[list[Case], list[ImportRowError]]:
        issues: list[ImportRowError] = []
        cases: list[Case] = []
        seen_keys: set[tuple[Any, ...]] = set()

        for idx, row in df.iterrows():
            row_number = idx + 2
            row_issues: list[ImportRowError] = []

            date_value = self._parse_date(row.get("date"), row_number, "date", row_issues)
            if not date_value:
                for issue in row_issues:
                    issue.batch_id = batch.id
                issues.extend(row_issues)
                continue

            if date_value > date.today():
                row_issues.append(self._issue(batch.id, row_number, "date", QualitySeverity.ERROR, "Case date cannot be in the future", str(row.get("date"))))

            daily_cases = self._parse_int(row.get("daily_cases"), row_number, "daily_cases", row_issues, required=True)
            cumulative_cases = self._parse_int(row.get("cumulative_cases"), row_number, "cumulative_cases", row_issues, default=0)
            daily_deaths = self._parse_int(row.get("daily_deaths"), row_number, "daily_deaths", row_issues, default=0)
            cumulative_deaths = self._parse_int(row.get("cumulative_deaths"), row_number, "cumulative_deaths", row_issues, default=0)
            daily_recovered = self._parse_int(row.get("daily_recovered"), row_number, "daily_recovered", row_issues, default=None)
            cumulative_recovered = self._parse_int(row.get("cumulative_recovered"), row_number, "cumulative_recovered", row_issues, default=None)

            values = [value for value in [daily_cases, cumulative_cases, daily_deaths, cumulative_deaths, daily_recovered, cumulative_recovered] if value is not None]
            if any(value < 0 for value in values):
                row_issues.append(self._issue(batch.id, row_number, None, QualitySeverity.ERROR, "Negative values are not allowed"))
            if daily_cases is not None and daily_deaths is not None and daily_cases > 0 and daily_deaths > daily_cases:
                row_issues.append(self._issue(batch.id, row_number, "daily_deaths", QualitySeverity.ERROR, "Daily deaths cannot exceed daily cases", str(row.get("daily_deaths"))))
            if cumulative_cases is not None and cumulative_deaths is not None and cumulative_cases > 0 and cumulative_deaths > cumulative_cases:
                row_issues.append(self._issue(batch.id, row_number, "cumulative_deaths", QualitySeverity.ERROR, "Cumulative deaths cannot exceed cumulative cases", str(row.get("cumulative_deaths"))))

            reporting_level = self._optional_text(row.get("reporting_level")) or ("admin1" if self._optional_text(row.get("subnational_region")) else "national")
            if reporting_level not in self.VALID_REPORTING_LEVELS:
                row_issues.append(self._issue(batch.id, row_number, "reporting_level", QualitySeverity.ERROR, "Reporting level must be national, admin1, admin2, or facility", reporting_level))

            confirmation_status = self._optional_text(row.get("confirmation_status"))
            if confirmation_status and confirmation_status not in self.VALID_CONFIRMATION_STATUS:
                row_issues.append(self._issue(batch.id, row_number, "confirmation_status", QualitySeverity.ERROR, "Confirmation status must be suspected, probable, or confirmed", confirmation_status))

            subnational_region = self._optional_text(row.get("subnational_region"))
            key = (country_id, disease_id, date_value, subnational_region or "")
            if key in seen_keys:
                row_issues.append(self._issue(batch.id, row_number, None, QualitySeverity.WARNING, "Duplicate country/disease/date/subnational row within this file; later row will update the same record"))
            seen_keys.add(key)

            reporting_period_start = self._parse_date(row.get("reporting_period_start"), row_number, "reporting_period_start", row_issues, required=False) or date_value
            reporting_period_end = self._parse_date(row.get("reporting_period_end"), row_number, "reporting_period_end", row_issues, required=False) or date_value
            if reporting_period_start and reporting_period_end and reporting_period_start > reporting_period_end:
                row_issues.append(self._issue(batch.id, row_number, "reporting_period_start", QualitySeverity.ERROR, "Reporting period start cannot be after reporting period end"))

            for issue in row_issues:
                issue.batch_id = batch.id
            issues.extend(row_issues)
            if any(issue.severity == QualitySeverity.ERROR for issue in row_issues):
                continue

            cases.append(Case(
                country_id=country_id,
                disease_id=disease_id,
                date=date_value,
                daily_cases=daily_cases or 0,
                cumulative_cases=cumulative_cases or 0,
                daily_deaths=daily_deaths or 0,
                cumulative_deaths=cumulative_deaths or 0,
                daily_recovered=daily_recovered,
                cumulative_recovered=cumulative_recovered,
                subnational_region=subnational_region,
                source=self._optional_text(row.get("source")) or batch.filename,
                source_system_id=source_system_id,
                import_batch_id=batch.id,
                reporting_period_start=reporting_period_start,
                reporting_period_end=reporting_period_end,
                reporting_level=reporting_level,
                case_definition=self._optional_text(row.get("case_definition")),
                confirmation_status=confirmation_status,
                data_quality_score=100.0,
                notes=self._optional_text(row.get("notes")),
            ))

        return cases, issues

    def _commit_cases(self, cases: list[Case]) -> int:
        committed = 0
        for case in cases:
            existing_query = self.db.query(Case).filter(
                Case.country_id == case.country_id,
                Case.disease_id == case.disease_id,
                Case.date == case.date,
            )
            if case.subnational_region:
                existing_query = existing_query.filter(Case.subnational_region == case.subnational_region)
            else:
                existing_query = existing_query.filter(Case.subnational_region.is_(None))

            existing = existing_query.first()
            if existing:
                for field in [
                    "daily_cases", "cumulative_cases", "daily_deaths", "cumulative_deaths",
                    "daily_recovered", "cumulative_recovered", "source", "source_system_id",
                    "import_batch_id", "reporting_period_start", "reporting_period_end",
                    "reporting_level", "case_definition", "confirmation_status", "data_quality_score", "notes",
                ]:
                    setattr(existing, field, getattr(case, field))
                existing.updated_at = datetime.utcnow()
            else:
                self.db.add(case)
            committed += 1
        self.db.flush()
        return committed

    def _build_quality_checks(
        self,
        batch_id: int,
        df: pd.DataFrame,
        cases: list[Case],
        issues: list[ImportRowError],
    ) -> list[DataQualityCheck]:
        row_count = max(len(df), 1)
        required_present = all(col in df.columns for col in self.REQUIRED_COLUMNS)
        validity_rate = len(cases) / row_count
        duplicate_warnings = sum(1 for issue in issues if "Duplicate" in issue.message)
        latest_date = max((case.date for case in cases), default=None)
        lag_days = (date.today() - latest_date).days if latest_date else None

        return [
            DataQualityCheck(
                batch_id=batch_id,
                check_name="required_columns",
                severity=QualitySeverity.ERROR,
                passed=required_present,
                metric_value=1.0 if required_present else 0.0,
                threshold=1.0,
                message="Required surveillance columns are present" if required_present else "Required surveillance columns are missing",
            ),
            DataQualityCheck(
                batch_id=batch_id,
                check_name="row_validity_rate",
                severity=QualitySeverity.ERROR,
                passed=validity_rate >= 0.95,
                metric_value=validity_rate,
                threshold=0.95,
                message=f"{validity_rate:.0%} of rows passed validation",
            ),
            DataQualityCheck(
                batch_id=batch_id,
                check_name="duplicate_rows",
                severity=QualitySeverity.WARNING,
                passed=duplicate_warnings == 0,
                metric_value=float(duplicate_warnings),
                threshold=0.0,
                message=f"{duplicate_warnings} duplicate row warnings found",
            ),
            DataQualityCheck(
                batch_id=batch_id,
                check_name="timeliness",
                severity=QualitySeverity.WARNING,
                passed=lag_days is not None and lag_days <= 14,
                metric_value=float(lag_days) if lag_days is not None else None,
                threshold=14.0,
                message="Latest record is within 14 days" if lag_days is not None and lag_days <= 14 else "Latest record is older than 14 days or unavailable",
            ),
        ]

    def _quality_score(
        self,
        row_count: int,
        error_count: int,
        warning_count: int,
        checks: list[DataQualityCheck],
    ) -> float:
        if row_count <= 0:
            return 0.0
        score = 100.0
        score -= (error_count / row_count) * 100.0
        score -= min((warning_count / row_count) * 25.0, 25.0)
        for check in checks:
            if not check.passed:
                score -= 5.0 if check.severity == QualitySeverity.WARNING else 15.0
        return round(max(score, 0.0), 2)

    def _parse_date(self, value: Any, row_number: int, field_name: str, issues: list[ImportRowError], required: bool = True) -> Optional[date]:
        if self._is_blank(value):
            if required:
                issues.append(self._issue(0, row_number, field_name, QualitySeverity.ERROR, f"{field_name} is required"))
            return None
        try:
            return pd.to_datetime(value).date()
        except Exception:
            issues.append(self._issue(0, row_number, field_name, QualitySeverity.ERROR, f"{field_name} is not a valid date", str(value)))
            return None

    def _parse_int(
        self,
        value: Any,
        row_number: int,
        field_name: str,
        issues: list[ImportRowError],
        required: bool = False,
        default: Optional[int] = 0,
    ) -> Optional[int]:
        if self._is_blank(value):
            if required:
                issues.append(self._issue(0, row_number, field_name, QualitySeverity.ERROR, f"{field_name} is required"))
            return default
        try:
            return int(value)
        except Exception:
            issues.append(self._issue(0, row_number, field_name, QualitySeverity.ERROR, f"{field_name} must be an integer", str(value)))
            return default

    def _issue(
        self,
        batch_id: int,
        row_number: int,
        field_name: Optional[str],
        severity: QualitySeverity,
        message: str,
        raw_value: Optional[str] = None,
    ) -> ImportRowError:
        return ImportRowError(
            batch_id=batch_id,
            row_number=row_number,
            field_name=field_name,
            severity=severity,
            message=message,
            raw_value=raw_value,
        )

    def _optional_text(self, value: Any) -> Optional[str]:
        if self._is_blank(value):
            return None
        return str(value).strip().lower()

    def _is_blank(self, value: Any) -> bool:
        return value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == ""

    def _result(
        self,
        batch: ImportBatch,
        issues: list[ImportRowError],
        checks: list[DataQualityCheck],
        committed: bool,
    ) -> Dict[str, Any]:
        issue_payload = [
            {
                "row_number": issue.row_number,
                "field_name": issue.field_name,
                "severity": issue.severity.value,
                "message": issue.message,
                "raw_value": issue.raw_value,
            }
            for issue in issues
        ]
        check_payload = [
            {
                "check_name": check.check_name,
                "severity": check.severity.value,
                "passed": check.passed,
                "metric_value": check.metric_value,
                "threshold": check.threshold,
                "message": check.message,
            }
            for check in checks
        ]
        errors = [f"Row {issue.row_number}: {issue.message}" for issue in issues if issue.severity == QualitySeverity.ERROR]
        return {
            "success": batch.error_count == 0,
            "committed": committed,
            "batch_id": batch.id,
            "status": batch.status.value,
            "rows_total": batch.rows_total,
            "rows_valid": batch.rows_valid,
            "rows_committed": batch.rows_committed,
            "error_count": batch.error_count,
            "warning_count": batch.warning_count,
            "quality_score": batch.quality_score,
            "errors": errors,
            "issues": issue_payload,
            "quality_checks": check_payload,
            "message": self._message(batch, committed),
            "metadata": batch.batch_metadata or {},
        }

    def _message(self, batch: ImportBatch, committed: bool) -> str:
        if batch.error_count:
            return f"Validated {batch.rows_total} rows; {batch.error_count} errors must be fixed before commit."
        if not committed:
            return f"Validated {batch.rows_total} rows successfully. Review passed; no records were committed."
        return f"Committed {batch.rows_committed} case records with {batch.warning_count} warnings."
