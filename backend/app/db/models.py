"""
Database models for EpiSphere AI
Production-ready schema with proper relationships and indexing
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text,
    Date, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
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
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


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
    
    role = relationship("Role", back_populates="users")
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
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    country = relationship("Country", back_populates="cases")
    disease = relationship("Disease", back_populates="cases")
    
    # Composite indexes for time-series queries
    __table_args__ = (
        Index("idx_case_country_disease_date", "country_id", "disease_id", "date"),
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
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    investigated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    investigated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    country = relationship("Country", back_populates="alerts")
    disease = relationship("Disease", back_populates="alerts")
    investigator = relationship("User", foreign_keys=[investigated_by])
    
    __table_args__ = (
        Index("idx_alert_country_disease", "country_id", "disease_id"),
        Index("idx_alert_status", "status"),
        Index("idx_alert_severity", "severity"),
        Index("idx_alert_triggered", "triggered_at"),
    )
    
    def __repr__(self):
        return f"<Alert(country_id={self.country_id}, disease_id={self.disease_id}, severity='{self.severity}')>"


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


class Facility(Base):
    """Health facilities"""
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(FacilityType), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    location = Column(String(255), nullable=True) # "Lat,Lon" or address
    province = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    
    # Consent Setting
    public_visible = Column(Boolean, default=False)
    
    parent_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="facility")
    patients = relationship("Patient", back_populates="facility")
    encounters = relationship("Encounter", back_populates="facility")
    
    def __repr__(self):
        return f"<Facility(name='{self.name}', type='{self.type}')>"


class Patient(Base):
    """
    Patients - Encrypted/Anonymized identity
    Strictly scoped to facility. Not for global aggregation without anonymization.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    mrn = Column(String(255), nullable=True) # Medical Record Number (Should be encrypted in app)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    facility = relationship("Facility", back_populates="patients")
    encounters = relationship("Encounter", back_populates="patient")

    __table_args__ = (
        Index("idx_patient_facility", "facility_id"),
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
    timestamp = Column(DateTime, default=datetime.utcnow)

