"""alert detection metadata

Revision ID: 0003_alert_detection_metadata
Revises: 0002_data_governance
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_alert_detection_metadata"
down_revision = "0002_data_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alerts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    if "detection_metadata" in columns:
        return
    with op.batch_alter_table("alerts") as batch:
        batch.add_column(sa.Column("detection_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alerts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    if "detection_metadata" not in columns:
        return
    with op.batch_alter_table("alerts") as batch:
        batch.drop_column("detection_metadata")
