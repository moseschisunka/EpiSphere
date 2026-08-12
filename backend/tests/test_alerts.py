import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.alerts import resolve_alert, review_alert
from app.db.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AuditAction,
    AuditLog,
    AlertNotification,
    NotificationStatus,
    ReviewStatus,
    Base,
    Country,
    Disease,
    Role,
    User,
)
from app.schemas.alert import AlertReviewUpdate, AlertUpdate
from app.services.notification_delivery import AlertNotificationDelivery


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
        "assigned_to": None,
        "resolution_notes_updated": True,
    }
    db.close()


def test_terminal_alert_cannot_be_reopened():
    db = make_session()
    user, alert = seed_alert(db)
    alert.status = AlertStatus.CLOSED
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


def test_alert_can_be_acknowledged_assigned_escalated_and_reopened():
    db = make_session()
    user, alert = seed_alert(db)

    for next_status in (AlertStatus.ACKNOWLEDGED, AlertStatus.ESCALATED):
        response = asyncio.run(resolve_alert(
            alert.id,
            AlertUpdate(status=next_status, assigned_to=user.id),
            user,
            db,
        ))
        assert response.status == next_status
        assert response.assigned_to == user.id

    notification = db.query(AlertNotification).one()
    assert notification.status == NotificationStatus.PENDING
    assert notification.recipient_email == user.email

    response = asyncio.run(resolve_alert(
        alert.id,
        AlertUpdate(status=AlertStatus.RESOLVED, resolution_notes="Response complete."),
        user,
        db,
    ))
    assert response.resolved_at is not None

    response = asyncio.run(resolve_alert(
        alert.id,
        AlertUpdate(status=AlertStatus.INVESTIGATING),
        user,
        db,
    ))
    assert response.reopened_at is not None
    db.close()


def test_human_review_decision_is_recorded_and_audited():
    db = make_session()
    user, alert = seed_alert(db)

    response = asyncio.run(review_alert(
        alert.id,
        AlertReviewUpdate(review_status=ReviewStatus.ACCEPTED, review_notes="Validated with district team."),
        user,
        db,
    ))

    assert response.review_status == ReviewStatus.ACCEPTED
    assert response.reviewed_by == user.id
    assert response.reviewed_at is not None
    audit = db.query(AuditLog).filter(AuditLog.resource_type == "alert_review").one()
    assert audit.details["review_status"] == "accepted"
    db.close()


def test_failed_notification_can_be_retried_with_backoff(monkeypatch):
    db = make_session()
    user, alert = seed_alert(db)
    asyncio.run(resolve_alert(alert.id, AlertUpdate(status=AlertStatus.ESCALATED), user, db))
    notification = db.query(AlertNotification).one()

    def fail_send(_notification):
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr(AlertNotificationDelivery, "_send_email", fail_send)
    result = AlertNotificationDelivery.deliver_pending(db)
    db.refresh(notification)
    assert result == {"selected": 1, "sent": 0, "failed": 1}
    assert notification.status == NotificationStatus.FAILED
    assert notification.attempts == 1
    assert notification.next_attempt_at is not None
    db.close()
