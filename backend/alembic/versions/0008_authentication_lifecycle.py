"""add account security lifecycle fields and one-time tokens

Revision ID: 0008_authentication_lifecycle
Revises: 0007_alert_human_review
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_authentication_lifecycle"
down_revision = "0007_alert_human_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "users" in tables:
        columns = {column["name"] for column in inspector.get_columns("users")}
        with op.batch_alter_table("users") as batch:
            if "token_version" not in columns:
                batch.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
            if "mfa_enabled" not in columns:
                batch.add_column(sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
            if "mfa_secret" not in columns:
                batch.add_column(sa.Column("mfa_secret", sa.String(length=64), nullable=True))
            if "mfa_pending_secret" not in columns:
                batch.add_column(sa.Column("mfa_pending_secret", sa.String(length=64), nullable=True))

    if "user_security_tokens" not in tables:
        op.create_table(
            "user_security_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("token_type", sa.String(length=40), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("token_hash", name="uq_user_security_token_hash"),
        )
        op.create_index("ix_user_security_tokens_id", "user_security_tokens", ["id"])
        op.create_index("ix_user_security_tokens_user_id", "user_security_tokens", ["user_id"])
        op.create_index("ix_user_security_tokens_token_hash", "user_security_tokens", ["token_hash"])
        op.create_index("ix_user_security_tokens_token_type", "user_security_tokens", ["token_type"])
        op.create_index("ix_user_security_tokens_expires_at", "user_security_tokens", ["expires_at"])
        op.create_index("idx_user_security_token_active", "user_security_tokens", ["user_id", "token_type", "used_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_security_tokens" in inspector.get_table_names():
        op.drop_index("idx_user_security_token_active", table_name="user_security_tokens")
        for name in (
            "ix_user_security_tokens_expires_at",
            "ix_user_security_tokens_token_type",
            "ix_user_security_tokens_token_hash",
            "ix_user_security_tokens_user_id",
            "ix_user_security_tokens_id",
        ):
            op.drop_index(name, table_name="user_security_tokens")
        op.drop_table("user_security_tokens")

    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        with op.batch_alter_table("users") as batch:
            for name in ("mfa_pending_secret", "mfa_secret", "mfa_enabled", "token_version"):
                if name in columns:
                    batch.drop_column(name)
