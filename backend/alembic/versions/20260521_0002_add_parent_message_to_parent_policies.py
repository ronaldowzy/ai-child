"""add parent message fields to parent policies

Revision ID: 20260521_0002
Revises: 20260520_0001
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0002"
down_revision: str | None = "20260520_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "parent_policies",
        sa.Column("parent_message_raw", sa.Text(), nullable=True),
    )
    op.add_column(
        "parent_policies",
        sa.Column("parent_message_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("parent_policies", "parent_message_updated_at")
    op.drop_column("parent_policies", "parent_message_raw")
