"""baseline schema

Revision ID: 0001_baseline_schema
Revises:
Create Date: 2026-07-02
"""

from alembic import op

from app.db.models import Base
from app.core.config import settings

# revision identifiers, used by Alembic.
revision = "0001_baseline_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    if bind.dialect.name == "postgresql" and settings.TIMESCALEDB_ENABLED:
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        op.execute(
            "SELECT create_hypertable('cases', 'date', if_not_exists => TRUE, migrate_data => TRUE)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
