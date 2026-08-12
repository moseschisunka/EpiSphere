"""
Database models for EpiSphere AI
Production-ready schema with proper relationships and indexing
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text,
    Date, Enum as SQLEnum, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


# Enums
class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AlertStatus(str, enum.Enum):
    """Alert lifecycle status"""
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class ReportType(str, enum.Enum):
    """Report types"""
    WEEKLY_BULLETIN = "weekly_bulletin"
    MONTHLY_REPORT = "monthly_report"
    OUTBREAK_REPORT = "outbreak_report"
    CUSTOM = "custom"


class AuditAction(str, enum.Enum):
    """Audit log actions"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    LOGIN = "login"
    LOGOUT = "logout"
    CLINICAL_ENTRY = "clinical_entry"
    RX_DISPENSE = "rx_dispense"


class FacilityType(str, enum.Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    PHARMACY = "pharmacy"
    LABORATORY = "laboratory"


class DiagnosisType(str, enum.Enum):
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"


class InteropDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class InteropStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    COMMITTED = "committed"
    REJECTED = "rejected"
    FAILED = "failed"


class IngestionJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class QualitySeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class BiosafetyLevel(str, enum.Enum):
    BSL1 = "BSL-1"
    BSL2 = "BSL-2"
    BSL3 = "BSL-3"
    BSL4 = "BSL-4"



# Models
class Role(Base):
    """User roles for RBAC"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role(name='{self.name}')>"


class User(Base):
    """User accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    token_version = Column(Integer, nullable=False, default=0)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(64), nullable=True)
    mfa_pending_secret = Column(String(64), nullable=True)
    
    role = relationship("Role", back_populates="users")

    @property
    def roles(self) -> list[str]:
        """Compatibility-safe role names for the authenticated UI contract.

        EpiSphere currently assigns one operational role per user, but clients
        consume a list to avoid baking that storage decision into navigation and
        authorization UX.
        """
        return [self.role.name] if self.role and self.role.name else []
    country = relationship("Country", back_populates="users")
    facility = relationship("Facility", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    encounters = relationship("Encounter", back_populates="clinician")
    dispensations = relationship("Dispensation", back_populates="pharmacist")
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role_id"),
    )
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class UserSecurityToken(Base):
    """Single-use, hashed tokens for account security workflows."""
    __tablename__ = "user_security_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    token_type = Column(String(40), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")

    __table_args__ = (
        Index("idx_user_security_token_active", "user_id", "token_type", "used_at"),
    )


class Country(Base):
    """Countries"""
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    iso_code = Column(String(3), unique=True, nullable=False, index=True)  # ISO 3166-1 alpha-3
    iso_code_2 = Column(String(2), unique=True, nullable=False)  # ISO 3166-1 alpha-2
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    population = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    region = relationship("Region", back_populates="countries")
    users = relationship("User", back_populates="country")
    cases = relationship("Case", back_populates="country")
    alerts = relationship("Alert", back_populates="country")
    forecasts = relationship("Forecast", back_populates="country")
    
    __table_args__ = (
        Index("idx_country_iso", "iso_code"),
        Index("idx_country_region", "region_id"),
    )
    
    def __repr__(self):
        return f"<Country(name='{self.name}', iso_code='{self.iso_code}')>"


class Region(Base):
    """Geographic regions (e.g., WHO regions)"""
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    countries = relationship("Country", back_populates="region")
    
    def __repr__(self):
        return f"<Region(name='{self.name}')>"


class Disease(Base):
    """Diseases being monitored"""
    __tablename__ = "diseases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True)  # ICD-10 or custom code
    description = Column(Text)
    biosafety_level = Column(SQLEnum(BiosafetyLevel), nullable=True, default=BiosafetyLevel.BSL2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cases = relationship("Case", back_populates="disease")
    alerts = relationship("Alert", back_populates="disease")
    forecasts = relationship("Forecast", back_populates="disease")
    
    __table_args__ = (
        Index("idx_disease_code", "code"),
        Index("idx_disease_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<Disease(name='{self.name}', code='{self.code}')>"


class Case(Base):
    """
    Disease case records (time-series optimized)
    This table will be converted to a TimescaleDB hypertable for time-series optimization
    """
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    daily_cases = Column(Integer, default=0, nullable=False)
    cumulative_cases = Column(Integer, default=0, nullable=False)
    daily_deaths = Column(Integer, default=0, nullable=False)
    cumulative_deaths = Column(Integer, default=0, nullable=False)
    daily_recovered = Column(Integer, default=0, nullable=True)
    cumulative_recovered = Column(Integer, default=0, nullable=True)
    subnational_region = Column(String(255), nullable=True)  # For subnational data
    source = Column(String(255), nullable=True)  # Data source
    source_system_id = Column(Integer, ForeignKey("source_systems.id"), nullable=True, index=True)
    source_record_id = Column(String(255), nullable=True, index=True)
    import_batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=True, index=True)
    reporting_period_start = Column(Date, nullable=True)
    reporting_period_end = Column(Date, nullable=True)
    reporting_level = Column(String(50), nullable=True)  # national, admin1, admin2, facility
    case_definition = Column(String(100), nullable=True)
    confirmation_status = Column(String(50), nullable=True)  # suspected, probable, confirmed
    data_quality_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    country = relationship("Country", back_populates="cases")
    disease = relationship("Disease", back_populates="cases")
    source_system = relationship("SourceSystem", back_populates="cases")
    import_batch = relationship("ImportBatch", back_populates="cases")
    
    # Composite indexes for time-series queries
    __table_args__ = (
        Index("idx_case_country_disease_date", "country_id", "disease_id", "date"),
        Index("idx_case_lineage", "source_system_id", "import_batch_id"),
        UniqueConstraint("source_system_id", "source_record_id", name="uq_case_source_record"),
        Index("idx_case_date", "date"),
        Index("idx_case_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<Case(country_id={self.country_id}, disease_id={self.disease_id}, date={self.date}, cases={self.daily_cases})>"


class Alert(Base):
    """Outbreak detection alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.TRIGGERED, index=True)
    probability_score = Column(Float, nullable=False)  # 0.0 to 1.0
    detection_method = Column(String(100), nullable=False)  # e.g., "isolation_forest", "cusum"
    explanation = Column(Text, nullable=False)  # Why alert was triggered
    detection_metadata = Column(JSON, nullable=True)  # Method scores, thresholds, preprocessing, model lineage
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    investigated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    investigated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    escalated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reopened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    review_status = Column(SQLEnum(ReviewStatus), nullable=False, default=ReviewStatus.PENDING, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    country = relationship("Country", back_populates="alerts")
    disease = relationship("Disease", back_populates="alerts")
    investigator = relationship("User", foreign_keys=[investigated_by])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    escalator = relationship("User", foreign_keys=[escalated_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    __table_args__ = (
        Index("idx_alert_country_disease", "country_id", "disease_id"),
        Index("idx_alert_status", "status"),
        Index("idx_alert_severity", "severity"),
        Index("idx_alert_triggered", "triggered_at"),
    )
    
    def __repr__(self):
        return f"<Alert(country_id={self.country_id}, disease_id={self.disease_id}, severity='{self.severity}')>"


class AlertNotification(Base):
    """Durable outbox record for response notifications."""
    __tablename__ = "alert_notifications"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=False)
    channel = Column(String(30), nullable=False, default="email")
    event_type = Column(String(50), nullable=False)
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    subject = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)

    alert = relationship("Alert")
    recipient = relationship("User", foreign_keys=[recipient_user_id])

    __table_args__ = (
        UniqueConstraint("alert_id", "event_type", "recipient_email", name="uq_alert_notification_recipient"),
    )

    def __repr__(self):
        return f"<AlertNotification(alert={self.alert_id}, recipient='{self.recipient_email}', status='{self.status}')>"


class Forecast(Base):
    """Forecast results"""
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # "arima", "prophet", "lstm"
    horizon_days = Column(Integer, nullable=False)  # Forecast horizon
    forecast_data = Column(JSON, nullable=False)  # {date: value, confidence_interval: [...]}
    accuracy_metrics = Column(JSON, nullable=True)  # MAE, RMSE, MAPE, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    country = relationship("Country", back_populates="forecasts")
    disease = relationship("Disease", back_populates="forecasts")
    
    __table_args__ = (
        Index("idx_forecast_country_disease", "country_id", "disease_id"),
        Index("idx_forecast_date", "forecast_date"),
    )
    
    def __repr__(self):
        return f"<Forecast(country_id={self.country_id}, disease_id={self.disease_id}, model='{self.model_type}')>"


class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True, index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    file_path = Column(String(500), nullable=True)  # Path to generated file
    file_format = Column(String(10), nullable=False)  # "pdf", "docx", "csv"
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    report_metadata = Column(JSON, nullable=True)  # Additional report metadata (renamed from metadata to avoid SQLAlchemy conflict)
    
    country = relationship("Country")
    disease = relationship("Disease")
    generator = relationship("User")
    
    __table_args__ = (
        Index("idx_report_type", "report_type"),
        Index("idx_report_generated", "generated_at"),
    )
    
    def __repr__(self):
        return f"<Report(title='{self.title}', type='{self.report_type}')>"


class AuditLog(Base):
    """Audit trail for data access and modifications"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)  # "case", "alert", "user", etc.
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)  # Additional action details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )
    
    def __repr__(self):
        return f"<AuditLog(user_id={self.user_id}, action='{self.action}', resource='{self.resource_type}')>"


class SourceSystem(Base):
    """External or internal system that provides public health data."""
    __tablename__ = "source_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    system_type = Column(String(100), nullable=False, default="manual_upload")
    owner = Column(String(255), nullable=True)
    system_metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="source_system")
    import_batches = relationship("ImportBatch", back_populates="source_system")


class ImportBatch(Base):
    """Durable lineage record for a data import, validation, and commit."""
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    dataset_type = Column(String(100), nullable=False, default="case_timeseries")
    status = Column(SQLEnum(ImportStatus), default=ImportStatus.PENDING, nullable=False, index=True)
    source_system_id = Column(Integer, ForeignKey("source_systems.id"), nullable=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    committed_at = Column(DateTime, nullable=True)
    rows_total = Column(Integer, default=0)
    rows_valid = Column(Integer, default=0)
    rows_committed = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    quality_score = Column(Float, nullable=True)
    batch_metadata = Column(JSON, nullable=True)

    source_system = relationship("SourceSystem", back_populates="import_batches")
    country = relationship("Country")
    disease = relationship("Disease")
    uploader = relationship("User")
    row_errors = relationship("ImportRowError", back_populates="batch", cascade="all, delete-orphan")
    quality_checks = relationship("DataQualityCheck", back_populates="batch", cascade="all, delete-orphan")
    staged_cases = relationship("ImportStagedCase", back_populates="batch", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="import_batch")
    jobs = relationship("IngestionJob", back_populates="import_batch")

    __table_args__ = (
        Index("idx_import_batch_status_uploaded", "status", "uploaded_at"),
        Index("idx_import_batch_scope", "country_id", "disease_id", "dataset_type"),
    )


class ImportStagedCase(Base):
    """Validated case payload held for a data-officer approval decision."""

    __tablename__ = "import_staged_cases"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    batch = relationship("ImportBatch", back_populates="staged_cases")

    __table_args__ = (
        UniqueConstraint("batch_id", "row_number", name="uq_import_staged_case_batch_row"),
        Index("idx_import_staged_case_batch", "batch_id"),
    )


class IngestionJob(Base):
    """Durable worker job envelope for long-running ingestion operations."""

    __tablename__ = "ingestion_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(100), nullable=False, index=True)
    status = Column(SQLEnum(IngestionJobStatus), nullable=False, default=IngestionJobStatus.QUEUED, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    available_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancel_requested_at = Column(DateTime, nullable=True)
    worker_id = Column(String(255), nullable=True)
    import_batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    import_batch = relationship("ImportBatch", back_populates="jobs")
    creator = relationship("User")

    __table_args__ = (
        Index("idx_ingestion_job_queue", "status", "available_at"),
        Index("idx_ingestion_job_type_created", "job_type", "created_at"),
    )


class WorkerHeartbeat(Base):
    """Latest liveness signal from a durable background worker."""

    __tablename__ = "worker_heartbeats"

    worker_id = Column(String(255), primary_key=True)
    worker_type = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_heartbeat_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_job_id = Column(Integer, ForeignKey("ingestion_jobs.id"), nullable=True)
    last_error = Column(Text, nullable=True)

    last_job = relationship("IngestionJob")


class ImportRowError(Base):
    """Row-level validation issue captured during upload."""
    __tablename__ = "import_row_errors"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=True)
    severity = Column(SQLEnum(QualitySeverity), default=QualitySeverity.ERROR, nullable=False, index=True)
    message = Column(Text, nullable=False)
    raw_value = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("ImportBatch", back_populates="row_errors")

    __table_args__ = (
        Index("idx_import_row_error_batch_row", "batch_id", "row_number"),
    )


class DataQualityCheck(Base):
    """Batch-level data quality check for completeness, validity, timeliness, and uniqueness."""
    __tablename__ = "data_quality_checks"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=False, index=True)
    check_name = Column(String(100), nullable=False)
    severity = Column(SQLEnum(QualitySeverity), default=QualitySeverity.INFO, nullable=False)
    passed = Column(Boolean, nullable=False)
    metric_value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("ImportBatch", back_populates="quality_checks")


class CodeSystem(Base):
    """Terminology code system such as ICD-10, ICD-11, SNOMED CT, LOINC, or DHIS2."""
    __tablename__ = "code_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    uri = Column(String(500), nullable=True)
    version = Column(String(100), nullable=True)
    owner = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    concepts = relationship("StandardConcept", back_populates="code_system", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_code_system_name_version"),
    )


class StandardConcept(Base):
    """A coded disease, diagnosis, lab observation, symptom, medicine, or DHIS2 element."""
    __tablename__ = "standard_concepts"

    id = Column(Integer, primary_key=True, index=True)
    code_system_id = Column(Integer, ForeignKey("code_systems.id"), nullable=False, index=True)
    code = Column(String(100), nullable=False)
    display = Column(String(255), nullable=False)
    concept_type = Column(String(100), nullable=False, index=True)
    concept_metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    code_system = relationship("CodeSystem", back_populates="concepts")

    __table_args__ = (
        UniqueConstraint("code_system_id", "code", name="uq_standard_concept_code"),
        Index("idx_standard_concept_type_code", "concept_type", "code"),
    )


class ConceptMap(Base):
    """Mapping from local/source codes to standard concepts."""
    __tablename__ = "concept_maps"

    id = Column(Integer, primary_key=True, index=True)
    source_system_id = Column(Integer, ForeignKey("source_systems.id"), nullable=True, index=True)
    source_code = Column(String(255), nullable=False)
    source_display = Column(String(255), nullable=True)
    target_concept_id = Column(Integer, ForeignKey("standard_concepts.id"), nullable=False, index=True)
    map_type = Column(String(50), default="equivalent")
    created_at = Column(DateTime, default=datetime.utcnow)

    source_system = relationship("SourceSystem")
    target_concept = relationship("StandardConcept")

    __table_args__ = (
        UniqueConstraint("source_system_id", "source_code", "target_concept_id", name="uq_concept_map_source_target"),
    )


class Facility(Base):
    """Health facilities"""
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(FacilityType), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    location = Column(String(255), nullable=True) # Legacy display address or lat,lon text
    facility_code = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    province = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    admin1_code = Column(String(100), nullable=True, index=True)
    admin2_code = Column(String(100), nullable=True, index=True)
    
    # Consent Setting
    public_visible = Column(Boolean, default=False)
    
    parent_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="facility")
    patients = relationship("Patient", back_populates="facility")
    encounters = relationship("Encounter", back_populates="facility")
    
    def __repr__(self):
        return f"<Facility(name='{self.name}', type='{self.type}')>"

    __table_args__ = (
        UniqueConstraint("country_id", "facility_code", name="uq_facility_country_code"),
        Index("idx_facility_admin", "country_id", "admin1_code", "admin2_code"),
        Index("idx_facility_geo", "latitude", "longitude"),
    )


class Patient(Base):
    """
    Patients - Encrypted/Anonymized identity
    Strictly scoped to facility. Not for global aggregation without anonymization.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    mrn = Column(String(255), nullable=True) # Medical Record Number, never returned raw by API
    mrn_hash = Column(String(64), nullable=True, index=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    facility = relationship("Facility", back_populates="patients")
    encounters = relationship("Encounter", back_populates="patient")

    __table_args__ = (
        Index("idx_patient_facility", "facility_id"),
        Index("idx_patient_facility_mrn_hash", "facility_id", "mrn_hash"),
    )


class Encounter(Base):
    """Clinical visits"""
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    clinician_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    symptoms = Column(JSON, nullable=True) # List of symptom codes/names
    notes = Column(Text, nullable=True)
    
    patient = relationship("Patient", back_populates="encounters")
    facility = relationship("Facility", back_populates="encounters")
    clinician = relationship("User", back_populates="encounters")
    diagnoses = relationship("Diagnosis", back_populates="encounter")
    prescriptions = relationship("Prescription", back_populates="encounter")


class Diagnosis(Base):
    """Diagnoses linked to encounters"""
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True) # Can be null if disease not in system
    icd10_code = Column(String(20), nullable=True)
    diagnosis_type = Column(SQLEnum(DiagnosisType), default=DiagnosisType.SUSPECTED)
    comments = Column(Text, nullable=True)

    encounter = relationship("Encounter", back_populates="diagnoses")
    disease = relationship("Disease")


class Prescription(Base):
    """Medications prescribed"""
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    drug_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    is_dispensed = Column(Boolean, default=False)

    encounter = relationship("Encounter", back_populates="prescriptions")
    dispensation = relationship("Dispensation", back_populates="prescription", uselist=False)


class Dispensation(Base):
    """Medication fulfillment"""
    __tablename__ = "dispensations"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False, unique=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dispensed_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    prescription = relationship("Prescription", back_populates="dispensation")
    pharmacist = relationship("User", back_populates="dispensations")


class InteropLog(Base):
    """Log of data exchange with external systems (e.g. DHIS2)"""
    __tablename__ = "interop_logs"

    id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String(50), nullable=False) # e.g. "DHIS2"
    direction = Column(SQLEnum(InteropDirection), nullable=False)
    status = Column(SQLEnum(InteropStatus), default=InteropStatus.PENDING)
    dataset_type = Column(String(50), nullable=False) # e.g. "weekly_aggregate"
    details = Column(JSON, nullable=True) # Payload summary or error message
    external_id = Column(String(255), nullable=True, index=True)
    mapping_id = Column(Integer, ForeignKey("dhis2_mappings.id"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class DHIS2Mapping(Base):
    """Named DHIS2 mapping contract used to validate outbound payloads."""
    __tablename__ = "dhis2_mappings"

    id = Column(Integer, primary_key=True, index=True)
    dataset = Column(String(100), nullable=False, unique=True, index=True)
    endpoint_path = Column(String(255), nullable=False)
    payload_type = Column(String(50), nullable=False, default="aggregate")
    required_fields = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsArticle(Base):
    """Health news articles for public browse"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True) # e.g. "WHO", "CDC", "EpiSphere"
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_public = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title}')>"




