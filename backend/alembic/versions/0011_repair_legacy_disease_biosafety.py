"""Repair the legacy SQLite disease table created before the migration ledger.

Revision ID: 0011_legacy_disease_bsl
Revises: 0010_worker_heartbeats
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_legacy_disease_bsl"
down_revision = "0010_worker_heartbeats"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    # Revision 0001 used metadata.create_all(), which does not add columns to
    # SQLite files created by an older application build. Keep this migration
    # idempotent so fresh databases and legacy pilot databases both upgrade.
    if not _has_column("diseases", "biosafety_level"):
        op.add_column("diseases", sa.Column("biosafety_level", sa.String(length=16), nullable=True))


def downgrade() -> None:
    if _has_column("diseases", "biosafety_level"):
        op.drop_column("diseases", "biosafety_level")
