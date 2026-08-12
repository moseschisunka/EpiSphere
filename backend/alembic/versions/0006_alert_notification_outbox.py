"""add durable alert notification outbox

Revision ID: 0006_alert_notification_outbox
Revises: 0005_alert_response_lifecycle
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_alert_notification_outbox"
down_revision = "0005_alert_response_lifecycle"
branch_labels = None
depends_on = None


notification_status = sa.Enum("PENDING", "SENT", "FAILED", name="notificationstatus")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alert_notifications" in inspector.get_table_names():
        return
    if bind.dialect.name == "postgresql":
        notification_status.create(bind, checkfirst=True)
    op.create_table(
        "alert_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=True),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("status", notification_status, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id", "event_type", "recipient_email", name="uq_alert_notification_recipient"),
    )
    for name, column in (
        ("ix_alert_notifications_id", "id"),
        ("ix_alert_notifications_alert_id", "alert_id"),
        ("ix_alert_notifications_recipient_user_id", "recipient_user_id"),
        ("ix_alert_notifications_status", "status"),
        ("ix_alert_notifications_created_at", "created_at"),
        ("ix_alert_notifications_next_attempt_at", "next_attempt_at"),
    ):
        op.create_index(name, "alert_notifications", [column], unique=False)


def downgrade() -> None:
    op.drop_table("alert_notifications")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        notification_status.drop(bind, checkfirst=True)
