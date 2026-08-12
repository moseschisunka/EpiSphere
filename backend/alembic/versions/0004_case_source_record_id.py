"""add source record identity for idempotent case ingestion

Revision ID: 0004_case_source_record_id
Revises: 0003_alert_detection_metadata
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_case_source_record_id"
down_revision = "0003_alert_detection_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "cases" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("cases")}
    if "source_record_id" not in columns:
        with op.batch_alter_table("cases") as batch:
            batch.add_column(sa.Column("source_record_id", sa.String(length=255), nullable=True))
    indexes = {index["name"] for index in inspector.get_indexes("cases")}
    if "idx_case_source_record" not in indexes:
        op.create_index("idx_case_source_record", "cases", ["source_record_id"], unique=False)
    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("cases")}
    if "uq_case_source_record" not in unique_constraints and "uq_case_source_record" not in indexes:
        op.create_index("uq_case_source_record", "cases", ["source_system_id", "source_record_id"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "cases" not in inspector.get_table_names():
        return
    indexes = {index["name"] for index in inspector.get_indexes("cases")}
    if "uq_case_source_record" in indexes:
        op.drop_index("uq_case_source_record", table_name="cases")
    if "idx_case_source_record" in indexes:
        op.drop_index("idx_case_source_record", table_name="cases")
    columns = {column["name"] for column in inspector.get_columns("cases")}
    if "source_record_id" in columns:
        with op.batch_alter_table("cases") as batch:
            batch.drop_column("source_record_id")
