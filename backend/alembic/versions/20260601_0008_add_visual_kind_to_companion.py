"""Add visual_kind column to companion_objects.

Revision ID: 20260601_0008
Revises: 20260530_0007
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0008"
down_revision = "20260530_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companion_objects",
        sa.Column(
            "visual_kind",
            sa.String(length=40),
            nullable=True,
            server_default=sa.text("'star'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("companion_objects", "visual_kind")
