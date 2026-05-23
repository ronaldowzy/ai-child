"""Add parent report generation status fields.

Revision ID: 20260524_0005
Revises: 20260523_0004
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260524_0005"
down_revision = "20260523_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "parent_reports",
        sa.Column(
            "generation_status",
            sa.String(length=80),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.add_column(
        "parent_reports",
        sa.Column(
            "generated_by",
            sa.String(length=80),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.add_column(
        "parent_reports",
        sa.Column("generation_error_code", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "parent_reports",
        sa.Column("material_fingerprint", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("parent_reports", "material_fingerprint")
    op.drop_column("parent_reports", "generation_error_code")
    op.drop_column("parent_reports", "generated_by")
    op.drop_column("parent_reports", "generation_status")
