"""record operational investigation notes and evidence

Revision ID: 0013_alert_investigation_evidence
Revises: 0012_staged_import_cases
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_alert_investigation_evidence"
down_revision = "0012_staged_import_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "alerts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    with op.batch_alter_table("alerts") as batch:
        if "investigation_notes" not in columns:
            batch.add_column(sa.Column("investigation_notes", sa.Text(), nullable=True))
        if "evidence_references" not in columns:
            batch.add_column(sa.Column("evidence_references", sa.JSON(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "alerts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    with op.batch_alter_table("alerts") as batch:
        for name in ("evidence_references", "investigation_notes"):
            if name in columns:
                batch.drop_column(name)
