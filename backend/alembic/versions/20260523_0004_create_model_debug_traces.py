"""Create local model debug trace table.

Revision ID: 20260523_0004
Revises: 20260521_0003
Create Date: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_0004"
down_revision: str | None = "20260521_0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "model_debug_traces",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("task_type", sa.String(length=80), nullable=False),
        sa.Column("profile_name", sa.String(length=120), nullable=True),
        sa.Column("provider_name", sa.String(length=120), nullable=True),
        sa.Column("model_name", sa.String(length=160), nullable=True),
        sa.Column("child_id", sa.String(length=120), nullable=True),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("child_id_hash", sa.String(length=64), nullable=True),
        sa.Column("session_id_hash", sa.String(length=64), nullable=True),
        sa.Column("request_messages_json", sa.JSON(), nullable=True),
        sa.Column("request_input_text", sa.Text(), nullable=True),
        sa.Column("request_context_json", sa.JSON(), nullable=True),
        sa.Column("request_metadata_json", sa.JSON(), nullable=True),
        sa.Column("request_params_json", sa.JSON(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("response_structured_output_json", sa.JSON(), nullable=True),
        sa.Column("response_metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "fallback_used",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "policy_blocked",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("error_type", sa.String(length=160), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("elapsed_ms", sa.Float(), nullable=True),
        sa.Column(
            "trace_source",
            sa.String(length=80),
            server_default=sa.text("'model_registry'"),
            nullable=False,
        ),
        sa.Column("environment", sa.String(length=80), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_model_debug_traces_child_id"),
        "model_debug_traces",
        ["child_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_debug_traces_request_id"),
        "model_debug_traces",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_debug_traces_session_id"),
        "model_debug_traces",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_debug_traces_task_type"),
        "model_debug_traces",
        ["task_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_model_debug_traces_task_type"), table_name="model_debug_traces")
    op.drop_index(op.f("ix_model_debug_traces_session_id"), table_name="model_debug_traces")
    op.drop_index(op.f("ix_model_debug_traces_request_id"), table_name="model_debug_traces")
    op.drop_index(op.f("ix_model_debug_traces_child_id"), table_name="model_debug_traces")
    op.drop_table("model_debug_traces")
