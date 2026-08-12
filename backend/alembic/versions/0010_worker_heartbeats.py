"""add durable worker heartbeats

Revision ID: 0010_worker_heartbeats
Revises: 0009_durable_ingestion_jobs
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_worker_heartbeats"
down_revision = "0009_durable_ingestion_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "worker_heartbeats" in inspector.get_table_names():
        return

    op.create_table(
        "worker_heartbeats",
        sa.Column("worker_id", sa.String(length=255), primary_key=True),
        sa.Column("worker_type", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(), nullable=False),
        sa.Column("last_job_id", sa.Integer(), sa.ForeignKey("ingestion_jobs.id"), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index("ix_worker_heartbeats_worker_type", "worker_heartbeats", ["worker_type"])
    op.create_index("ix_worker_heartbeats_last_heartbeat_at", "worker_heartbeats", ["last_heartbeat_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "worker_heartbeats" not in inspector.get_table_names():
        return
    op.drop_index("ix_worker_heartbeats_last_heartbeat_at", table_name="worker_heartbeats")
    op.drop_index("ix_worker_heartbeats_worker_type", table_name="worker_heartbeats")
    op.drop_table("worker_heartbeats")
