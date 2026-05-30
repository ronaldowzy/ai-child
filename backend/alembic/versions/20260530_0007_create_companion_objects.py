"""Create companion_objects table.

Revision ID: 20260530_0007
Revises: 20260525_0006
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260530_0007"
down_revision = "20260525_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companion_objects",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("object_type", sa.String(length=40), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("safe_summary", sa.String(length=500), nullable=False),
        sa.Column("light_location", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_recalled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recall_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "skip_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["child_id"], ["children.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_companion_objects_child_id",
        "companion_objects",
        ["child_id"],
    )
    op.create_index(
        "ix_companion_objects_status",
        "companion_objects",
        ["status"],
    )
    # Partial unique index: one active companion per child
    op.execute(
        "CREATE UNIQUE INDEX ix_companion_child_active "
        "ON companion_objects (child_id) "
        "WHERE status = 'active'"
    )


def downgrade() -> None:
    op.drop_index("ix_companion_child_active", table_name="companion_objects")
    op.drop_index("ix_companion_objects_status", table_name="companion_objects")
    op.drop_index("ix_companion_objects_child_id", table_name="companion_objects")
    op.drop_table("companion_objects")
