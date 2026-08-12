"""add human review decision fields to alerts

Revision ID: 0007_alert_human_review
Revises: 0006_alert_notification_outbox
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_alert_human_review"
down_revision = "0006_alert_notification_outbox"
branch_labels = None
depends_on = None


review_status = sa.Enum("PENDING", "ACCEPTED", "REJECTED", "INCONCLUSIVE", name="reviewstatus")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alerts" not in inspector.get_table_names():
        return
    if bind.dialect.name == "postgresql":
        review_status.create(bind, checkfirst=True)
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    with op.batch_alter_table("alerts") as batch:
        if "review_status" not in columns:
            batch.add_column(sa.Column("review_status", review_status, nullable=False, server_default="PENDING"))
        if "reviewed_by" not in columns:
            batch.add_column(sa.Column("reviewed_by", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_alerts_reviewed_by", "users", ["reviewed_by"], ["id"])
        if "reviewed_at" not in columns:
            batch.add_column(sa.Column("reviewed_at", sa.DateTime(), nullable=True))
        if "review_notes" not in columns:
            batch.add_column(sa.Column("review_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alerts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    with op.batch_alter_table("alerts") as batch:
        if "reviewed_by" in columns:
            batch.drop_constraint("fk_alerts_reviewed_by", type_="foreignkey")
        for name in ("review_notes", "reviewed_at", "reviewed_by", "review_status"):
            if name in columns:
                batch.drop_column(name)
    if bind.dialect.name == "postgresql":
        review_status.drop(bind, checkfirst=True)
