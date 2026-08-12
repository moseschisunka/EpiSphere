"""add durable ingestion worker jobs

Revision ID: 0009_durable_ingestion_jobs
Revises: 0008_authentication_lifecycle
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_durable_ingestion_jobs"
down_revision = "0008_authentication_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ingestion_jobs" in inspector.get_table_names():
        return

    job_status = sa.Enum(
        "QUEUED",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "CANCEL_REQUESTED",
        "CANCELLED",
        "DEAD_LETTER",
        name="ingestionjobstatus",
    )
    if bind.dialect.name == "postgresql":
        job_status.create(bind, checkfirst=True)
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="QUEUED"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancel_requested_at", sa.DateTime(), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("import_batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_ingestion_jobs_id", "ingestion_jobs", ["id"])
    op.create_index("ix_ingestion_jobs_job_type", "ingestion_jobs", ["job_type"])
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])
    op.create_index("ix_ingestion_jobs_available_at", "ingestion_jobs", ["available_at"])
    op.create_index("ix_ingestion_jobs_import_batch_id", "ingestion_jobs", ["import_batch_id"])
    op.create_index("ix_ingestion_jobs_created_by", "ingestion_jobs", ["created_by"])
    op.create_index("ix_ingestion_jobs_created_at", "ingestion_jobs", ["created_at"])
    op.create_index("idx_ingestion_job_queue", "ingestion_jobs", ["status", "available_at"])
    op.create_index("idx_ingestion_job_type_created", "ingestion_jobs", ["job_type", "created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ingestion_jobs" not in inspector.get_table_names():
        return
    for name in (
        "idx_ingestion_job_type_created",
        "idx_ingestion_job_queue",
        "ix_ingestion_jobs_created_at",
        "ix_ingestion_jobs_created_by",
        "ix_ingestion_jobs_import_batch_id",
        "ix_ingestion_jobs_available_at",
        "ix_ingestion_jobs_status",
        "ix_ingestion_jobs_job_type",
        "ix_ingestion_jobs_id",
    ):
        op.drop_index(name, table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    if bind.dialect.name == "postgresql":
        sa.Enum(name="ingestionjobstatus").drop(bind, checkfirst=True)
