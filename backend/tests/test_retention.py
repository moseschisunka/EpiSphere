from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import (
    Alert,
    AlertNotification,
    AlertSeverity,
    AlertStatus,
    AuditLog,
    Base,
    NotificationStatus,
    Role,
    User,
    UserSecurityToken,
)
from app.services.data_retention import run_retention


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def seed_security_artifacts(db, now):
    role = Role(name="retention-test", description="Retention test role")
    user = User(
        username="retention-user",
        email="retention@example.com",
        hashed_password="test-hash",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add_all([
        UserSecurityToken(
            user_id=user.id,
            token_hash="expired-token",
            token_type="email_verification",
            expires_at=now - timedelta(hours=1),
            created_at=now - timedelta(days=2),
        ),
        UserSecurityToken(
            user_id=user.id,
            token_hash="fresh-token",
            token_type="password_reset",
            expires_at=now + timedelta(hours=1),
            created_at=now,
        ),
    ])
    alert = Alert(
        country_id=1,
        disease_id=1,
        severity=AlertSeverity.MODERATE,
        status=AlertStatus.CLOSED,
        probability_score=0.5,
        detection_method="test",
        explanation="retention test",
        triggered_at=now - timedelta(days=200),
    )
    db.add(alert)
    db.flush()
    db.add_all([
        AlertNotification(
            alert_id=alert.id,
            recipient_email="old@example.com",
            channel="email",
            event_type="closed",
            status=NotificationStatus.SENT,
            subject="old notification",
            payload={},
            created_at=now - timedelta(days=200),
            sent_at=now - timedelta(days=200),
        ),
        AlertNotification(
            alert_id=alert.id,
            recipient_email="pending@example.com",
            channel="email",
            event_type="closed",
            status=NotificationStatus.PENDING,
            subject="pending notification",
            payload={},
            created_at=now - timedelta(days=200),
        ),
    ])
    db.commit()


def test_retention_dry_run_is_non_destructive_and_audited():
    db = make_session()
    now = datetime(2026, 8, 12, 12, 0, 0)
    seed_security_artifacts(db, now)

    result = run_retention(db, now=now, dry_run=True, notification_retention_days=180)
    db.commit()

    assert result.security_tokens == 1
    assert result.notifications == 1
    assert db.query(UserSecurityToken).count() == 2
    assert db.query(AlertNotification).count() == 2
    assert db.query(AuditLog).count() == 1
    assert db.query(AuditLog).one().details["dry_run"] is True
    db.close()


def test_retention_apply_preserves_fresh_tokens_and_pending_notifications():
    db = make_session()
    now = datetime(2026, 8, 12, 12, 0, 0)
    seed_security_artifacts(db, now)

    result = run_retention(db, now=now, dry_run=False, notification_retention_days=180)
    db.commit()

    assert result.security_tokens == 1
    assert result.notifications == 1
    assert db.query(UserSecurityToken).count() == 1
    assert db.query(AlertNotification).count() == 1
    assert db.query(AlertNotification).one().status is NotificationStatus.PENDING
    assert db.query(AuditLog).one().details["dry_run"] is False
    db.close()
