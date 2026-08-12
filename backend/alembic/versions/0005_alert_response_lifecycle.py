"""expand alert response lifecycle

Revision ID: 0005_alert_response_lifecycle
Revises: 0004_case_source_record_id
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_alert_response_lifecycle"
down_revision = "0004_case_source_record_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alerts" not in inspector.get_table_names():
        return

    if bind.dialect.name == "postgresql":
        for value in ("ACKNOWLEDGED", "ESCALATED", "CLOSED"):
            op.execute(f"ALTER TYPE alertstatus ADD VALUE IF NOT EXISTS '{value}'")

    columns = {column["name"] for column in inspector.get_columns("alerts")}
    additions = [
        ("acknowledged_at", sa.DateTime()),
        ("acknowledged_by", sa.Integer(), "users", "id"),
        ("assigned_to", sa.Integer(), "users", "id"),
        ("escalated_at", sa.DateTime()),
        ("escalated_by", sa.Integer(), "users", "id"),
        ("reopened_at", sa.DateTime()),
        ("closed_at", sa.DateTime()),
    ]
    with op.batch_alter_table("alerts") as batch:
        for addition in additions:
            if addition[0] in columns:
                continue
            column = sa.Column(addition[0], addition[1], nullable=True)
            batch.add_column(column)
            if len(addition) == 4:
                batch.create_foreign_key(
                    f"fk_alerts_{addition[0]}", addition[2], [addition[0]], [addition[3]]
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alerts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    with op.batch_alter_table("alerts") as batch:
        for name in ("closed_at", "reopened_at", "escalated_by", "escalated_at", "assigned_to", "acknowledged_by", "acknowledged_at"):
            if name in columns:
                if name in {"acknowledged_by", "assigned_to", "escalated_by"}:
                    batch.drop_constraint(f"fk_alerts_{name}", type_="foreignkey")
                batch.drop_column(name)
