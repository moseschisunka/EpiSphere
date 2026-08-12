"""persist validated manual-upload rows until an operator approves commit

Revision ID: 0012_staged_import_cases
Revises: 0011_legacy_disease_bsl
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_staged_import_cases"
down_revision = "0011_legacy_disease_bsl"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    # The baseline revision creates current metadata on a fresh database. A
    # legacy database needs this table here; a fresh one already has it.
    if not _has_table("import_staged_cases"):
        op.create_table(
            "import_staged_cases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=False),
            sa.Column("row_number", sa.Integer(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("batch_id", "row_number", name="uq_import_staged_case_batch_row"),
        )
        op.create_index("idx_import_staged_case_batch", "import_staged_cases", ["batch_id"])


def downgrade() -> None:
    if _has_table("import_staged_cases"):
        op.drop_index("idx_import_staged_case_batch", table_name="import_staged_cases")
        op.drop_table("import_staged_cases")
