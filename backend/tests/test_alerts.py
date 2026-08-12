import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.alerts import resolve_alert
from app.db.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AuditAction,
    AuditLog,
    Base,
    Country,
    Disease,
    Role,
    User,
)
from app.schemas.alert import AlertUpdate


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def seed_alert(db):
    role = Role(name="epidemiologist", description="Epidemiology user")
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([role, country, disease])
    db.flush()
    user = User(
        username="epi",
        email="epi@example.com",
        hashed_password="test-hash",
        role_id=role.id,
        is_active=True,
    )
    alert = Alert(
        country_id=country.id,
        disease_id=disease.id,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.TRIGGERED,
        probability_score=0.9,
        detection_method="cusum",
        explanation="Cases exceed the configured baseline.",
    )
    db.add_all([user, alert])
    db.commit()
    db.refresh(alert)
    return user, alert


def test_alert_lifecycle_records_investigation_and_audit():
    db = make_session()
    user, alert = seed_alert(db)

    response = asyncio.run(resolve_alert(
        alert.id,
        AlertUpdate(status=AlertStatus.INVESTIGATING, resolution_notes="County team notified."),
        user,
        db,
    ))

    assert response.status == AlertStatus.INVESTIGATING
    assert response.investigated_by == user.id
    audit = db.query(AuditLog).filter(AuditLog.resource_id == alert.id).one()
    assert audit.action == AuditAction.UPDATE
    assert audit.details == {
        "previous_status": "triggered",
        "status": "investigating",
        "resolution_notes_updated": True,
    }
    db.close()


def test_terminal_alert_cannot_be_reopened():
    db = make_session()
    user, alert = seed_alert(db)
    alert.status = AlertStatus.RESOLVED
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(resolve_alert(
            alert.id,
            AlertUpdate(status=AlertStatus.INVESTIGATING),
            user,
            db,
        ))

    assert exc_info.value.status_code == 409
    db.close()
