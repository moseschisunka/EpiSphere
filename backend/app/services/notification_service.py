"""Durable response-notification outbox helpers."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Alert, AlertNotification, NotificationStatus, Role, User


class AlertNotificationService:
    """Create retryable notification records without sending email in a request."""

    @staticmethod
    def enqueue_escalation(db: Session, alert: Alert) -> int:
        if alert.assignee and alert.assignee.is_active:
            recipients = [alert.assignee]
        else:
            recipients = (
                db.query(User)
                .join(Role, User.role_id == Role.id)
                .filter(User.is_active.is_(True), Role.name.in_(["admin", "epidemiologist"]))
                .order_by(User.id)
                .limit(50)
                .all()
            )

        created = 0
        for user in recipients:
            if not user.email:
                continue
            exists = db.query(AlertNotification).filter(
                AlertNotification.alert_id == alert.id,
                AlertNotification.event_type == "escalated",
                AlertNotification.recipient_email == user.email,
            ).first()
            if exists:
                continue
            db.add(AlertNotification(
                alert_id=alert.id,
                recipient_user_id=user.id,
                recipient_email=user.email,
                channel="email",
                event_type="escalated",
                status=NotificationStatus.PENDING,
                attempts=0,
                subject=f"EpiSphere alert escalated: {alert.severity.value}",
                payload={
                    "alert_id": alert.id,
                    "country_id": alert.country_id,
                    "disease_id": alert.disease_id,
                    "severity": alert.severity.value,
                },
                next_attempt_at=datetime.utcnow(),
            ))
            created += 1
        return created
