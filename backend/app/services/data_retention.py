"""Safe, auditable retention operations for scheduled maintenance runs."""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import logging

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    AlertNotification,
    AuditAction,
    AuditLog,
    NotificationStatus,
    UserSecurityToken,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetentionResult:
    """Counts from one retention run; no raw records or identifiers included."""

    security_tokens: int
    notifications: int
    dry_run: bool
    completed_at: str

    def as_dict(self) -> dict[str, int | bool | str]:
        return asdict(self)


def run_retention(
    db: Session,
    *,
    now: datetime | None = None,
    dry_run: bool = True,
    security_token_retention_days: int | None = None,
    notification_retention_days: int | None = None,
) -> RetentionResult:
    """Purge only explicitly eligible security artifacts.

    Expired or used security tokens are safe to remove. Notification rows are
    retained while pending and only terminal SENT/FAILED rows older than the
    configured retention period are eligible. Other evidence-bearing tables
    are deliberately not deleted until their partner-approved schedules and
    foreign-key/archive strategy are implemented.
    """

    current_time = now or datetime.utcnow()
    token_days = (
        settings.SECURITY_TOKEN_RETENTION_DAYS
        if security_token_retention_days is None
        else security_token_retention_days
    )
    notification_days = (
        settings.NOTIFICATION_RETENTION_DAYS
        if notification_retention_days is None
        else notification_retention_days
    )
    if token_days < 0 or notification_days < 0:
        raise ValueError("Retention periods must be non-negative")

    token_cutoff = current_time - timedelta(days=token_days)
    notification_cutoff = current_time - timedelta(days=notification_days)

    expired_tokens = db.query(UserSecurityToken).filter(
        or_(
            UserSecurityToken.expires_at <= current_time,
            and_(
                UserSecurityToken.used_at.is_not(None),
                UserSecurityToken.used_at <= token_cutoff,
            ),
        )
    )
    terminal_notifications = db.query(AlertNotification).filter(
        AlertNotification.status.in_([NotificationStatus.SENT, NotificationStatus.FAILED]),
        func.coalesce(AlertNotification.sent_at, AlertNotification.created_at) <= notification_cutoff,
    )

    token_count = expired_tokens.count()
    notification_count = terminal_notifications.count()

    if not dry_run:
        expired_tokens.delete(synchronize_session=False)
        terminal_notifications.delete(synchronize_session=False)

    result = RetentionResult(
        security_tokens=token_count,
        notifications=notification_count,
        dry_run=dry_run,
        completed_at=current_time.isoformat() + "Z",
    )
    db.add(AuditLog(
        action=AuditAction.DELETE,
        resource_type="retention_job",
        details=result.as_dict(),
    ))
    logger.info(
        "retention run completed",
        extra={"retention_counts": result.as_dict()},
    )
    return result
