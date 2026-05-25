"""Create child account auth tables.

Revision ID: 20260525_0006
Revises: 20260524_0005
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_0006"
down_revision = "20260524_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "child_accounts",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column("username", sa.String(length=160), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_by_guardian",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_child_accounts_username"),
    )
    op.create_index(
        op.f("ix_child_accounts_child_id"),
        "child_accounts",
        ["child_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_child_accounts_username"),
        "child_accounts",
        ["username"],
        unique=False,
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_account_id", sa.String(length=120), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["child_account_id"],
            ["child_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
    )
    op.create_index(
        op.f("ix_auth_sessions_child_account_id"),
        "auth_sessions",
        ["child_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_sessions_token_hash"),
        "auth_sessions",
        ["token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_sessions_token_hash"), table_name="auth_sessions")
    op.drop_index(
        op.f("ix_auth_sessions_child_account_id"),
        table_name="auth_sessions",
    )
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_child_accounts_username"), table_name="child_accounts")
    op.drop_index(op.f("ix_child_accounts_child_id"), table_name="child_accounts")
    op.drop_table("child_accounts")
