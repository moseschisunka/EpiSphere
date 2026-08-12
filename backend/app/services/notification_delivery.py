"""SMTP delivery for the alert notification outbox."""

import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AlertNotification, NotificationStatus


class AlertNotificationDelivery:
    MAX_ATTEMPTS = 5

    @staticmethod
    def deliver_pending(db: Session, limit: int = 50) -> dict[str, int]:
        now = datetime.utcnow()
        notifications = db.query(AlertNotification).filter(
            AlertNotification.status == NotificationStatus.PENDING,
            (AlertNotification.next_attempt_at.is_(None) | (AlertNotification.next_attempt_at <= now)),
        ).order_by(AlertNotification.created_at.asc()).limit(min(limit, 200)).all()
        sent = 0
        failed = 0
        for notification in notifications:
            if notification.attempts >= AlertNotificationDelivery.MAX_ATTEMPTS:
                notification.status = NotificationStatus.FAILED
                notification.error = "Maximum delivery attempts exceeded"
                failed += 1
                continue
            notification.attempts += 1
            try:
                AlertNotificationDelivery._send_email(notification)
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                notification.error = None
                notification.next_attempt_at = None
                sent += 1
            except Exception as exc:
                notification.status = NotificationStatus.FAILED
                notification.error = str(exc)[:500]
                notification.next_attempt_at = now + timedelta(seconds=min(2 ** notification.attempts * 60, 3600))
                failed += 1
            db.commit()
        return {"selected": len(notifications), "sent": sent, "failed": failed}

    @staticmethod
    def _send_email(notification: AlertNotification) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            raise RuntimeError("SMTP notification configuration is incomplete")
        message = EmailMessage()
        message["Subject"] = notification.subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = notification.recipient_email
        message.set_content(
            "EpiSphere response notification\n\n"
            f"Alert ID: {notification.payload.get('alert_id')}\n"
            f"Severity: {notification.payload.get('severity')}\n"
            "Review the alert in the EpiSphere operator portal."
        )
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
            smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
