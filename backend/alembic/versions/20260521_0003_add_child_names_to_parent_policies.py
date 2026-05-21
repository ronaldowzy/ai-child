"""Add child name fields to parent policies.

Revision ID: 20260521_0003
Revises: 20260521_0002
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa


revision: str = "20260521_0003"
down_revision: str | None = "20260521_0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "parent_policies",
        sa.Column("child_nickname", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "parent_policies",
        sa.Column("child_display_name", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("parent_policies", "child_display_name")
    op.drop_column("parent_policies", "child_nickname")
