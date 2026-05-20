"""create initial DB1-A tables

Revision ID: 20260520_0001
Revises:
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260520_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "children",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("nickname", sa.String(length=120), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("grade", sa.String(length=80), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("parent_notes", sa.Text(), nullable=True),
        sa.Column("profile", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "parent_policies",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("communication_preferences", sa.JSON(), nullable=False),
        sa.Column("safety_rules", sa.JSON(), nullable=False),
        sa.Column("schedule", sa.JSON(), nullable=False),
        sa.Column("data_retention", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_id", name="uq_parent_policies_child_id"),
    )
    op.create_index(
        op.f("ix_parent_policies_child_id"),
        "parent_policies",
        ["child_id"],
        unique=False,
    )
    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("base_scene", sa.String(length=120), nullable=True),
        sa.Column("active_scene", sa.String(length=120), nullable=True),
        sa.Column("session_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversation_sessions_child_id"),
        "conversation_sessions",
        ["child_id"],
        unique=False,
    )
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("session_id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=40), nullable=False),
        sa.Column("message_type", sa.String(length=40), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("input_items", sa.JSON(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("emotion", sa.String(length=80), nullable=True),
        sa.Column("agent_motion", sa.String(length=80), nullable=True),
        sa.Column("time_context", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["conversation_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversation_messages_child_id"),
        "conversation_messages",
        ["child_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_messages_session_id"),
        "conversation_messages",
        ["session_id"],
        unique=False,
    )
    op.create_table(
        "routing_decisions",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("message_id", sa.String(length=120), nullable=True),
        sa.Column("session_id", sa.String(length=120), nullable=False),
        sa.Column("primary_intent", sa.String(length=120), nullable=False),
        sa.Column("active_scene", sa.String(length=120), nullable=False),
        sa.Column("sub_scene", sa.String(length=120), nullable=True),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("decision", sa.JSON(), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["conversation_messages.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["conversation_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_routing_decisions_message_id"),
        "routing_decisions",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_routing_decisions_session_id"),
        "routing_decisions",
        ["session_id"],
        unique=False,
    )
    op.create_table(
        "memory_items",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column("memory_type", sa.String(length=80), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("sensitivity", sa.String(length=40), nullable=False),
        sa.Column("visible_to_parent", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("visible_to_child", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "requires_parent_attention",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("embedding_id", sa.String(length=160), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_memory_items_child_id"),
        "memory_items",
        ["child_id"],
        unique=False,
    )
    op.create_table(
        "parent_reports",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("child_id", sa.String(length=120), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("learning_observations", sa.JSON(), nullable=True),
        sa.Column("expression_observations", sa.JSON(), nullable=True),
        sa.Column("emotion_observations", sa.JSON(), nullable=True),
        sa.Column("safety_alerts", sa.JSON(), nullable=True),
        sa.Column("suggested_parent_actions", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_id", "report_date", name="uq_parent_reports_day"),
    )
    op.create_index(
        op.f("ix_parent_reports_child_id"),
        "parent_reports",
        ["child_id"],
        unique=False,
    )
    op.create_table(
        "tts_cache_records",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("voice_version", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("emotion", sa.String(length=40), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("voice_sample_sha256", sa.String(length=64), nullable=False),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
        sa.Column("audio_sha256", sa.String(length=64), nullable=True),
        sa.Column("audio_format", sa.String(length=20), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("public_url", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "cache_hit_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key", name="uq_tts_cache_key"),
    )
    op.create_index(
        op.f("ix_tts_cache_records_cache_key"),
        "tts_cache_records",
        ["cache_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tts_cache_records_cache_key"), table_name="tts_cache_records")
    op.drop_table("tts_cache_records")
    op.drop_index(op.f("ix_parent_reports_child_id"), table_name="parent_reports")
    op.drop_table("parent_reports")
    op.drop_index(op.f("ix_memory_items_child_id"), table_name="memory_items")
    op.drop_table("memory_items")
    op.drop_index(op.f("ix_routing_decisions_session_id"), table_name="routing_decisions")
    op.drop_index(op.f("ix_routing_decisions_message_id"), table_name="routing_decisions")
    op.drop_table("routing_decisions")
    op.drop_index(
        op.f("ix_conversation_messages_session_id"),
        table_name="conversation_messages",
    )
    op.drop_index(
        op.f("ix_conversation_messages_child_id"),
        table_name="conversation_messages",
    )
    op.drop_table("conversation_messages")
    op.drop_index(
        op.f("ix_conversation_sessions_child_id"),
        table_name="conversation_sessions",
    )
    op.drop_table("conversation_sessions")
    op.drop_index(op.f("ix_parent_policies_child_id"), table_name="parent_policies")
    op.drop_table("parent_policies")
    op.drop_table("children")
