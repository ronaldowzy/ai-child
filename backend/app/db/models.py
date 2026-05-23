from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy import Text, UniqueConstraint
from sqlalchemy import false, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Child(Base, TimestampMixin):
    __tablename__ = "children"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False)
    parent_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class ParentPolicyRecord(Base, TimestampMixin):
    __tablename__ = "parent_policies"
    __table_args__ = (
        UniqueConstraint("child_id", name="uq_parent_policies_child_id"),
    )

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    child_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goals: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    communication_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    safety_rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    schedule: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    data_retention: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    child_nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    child_display_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    parent_message_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_message_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )


class ConversationSessionRecord(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    child_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    base_scene: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active_scene: Mapped[str | None] = mapped_column(String(120), nullable=True)
    session_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class ConversationMessageRecord(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor: Mapped[str] = mapped_column(String(40), nullable=False)
    message_type: Mapped[str] = mapped_column(String(40), nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_items: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    attachments: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agent_motion: Mapped[str | None] = mapped_column(String(80), nullable=True)
    time_context: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class RoutingDecisionRecord(Base):
    __tablename__ = "routing_decisions"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    message_id: Mapped[str | None] = mapped_column(
        String(120),
        ForeignKey("conversation_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    primary_intent: Mapped[str] = mapped_column(String(120), nullable=False)
    active_scene: Mapped[str] = mapped_column(String(120), nullable=False)
    sub_scene: Mapped[str | None] = mapped_column(String(120), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    decision: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    signals: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class MemoryItemRecord(Base, TimestampMixin):
    __tablename__ = "memory_items"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    child_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(String(80), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    sensitivity: Mapped[str] = mapped_column(String(40), nullable=False)
    visible_to_parent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    visible_to_child: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    requires_parent_attention: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    embedding_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ParentReportRecord(Base):
    __tablename__ = "parent_reports"
    __table_args__ = (
        UniqueConstraint("child_id", "report_date", name="uq_parent_reports_day"),
    )

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    child_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    learning_observations: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    expression_observations: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    emotion_observations: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    safety_alerts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    suggested_parent_actions: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class ModelDebugTraceRecord(Base):
    __tablename__ = "model_debug_traces"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    request_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    profile_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    child_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    child_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_messages_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    request_input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_context_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    request_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    request_params_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_structured_output_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    response_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    fallback_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    policy_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    error_type: Mapped[str | None] = mapped_column(String(160), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    elapsed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    trace_source: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="model_registry",
        server_default=text("'model_registry'"),
    )
    environment: Mapped[str | None] = mapped_column(String(80), nullable=True)


class TtsCacheRecord(Base, TimestampMixin):
    __tablename__ = "tts_cache_records"
    __table_args__ = (UniqueConstraint("cache_key", name="uq_tts_cache_key"),)

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    voice_version: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    emotion: Mapped[str] = mapped_column(String(40), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    voice_sample_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    audio_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    audio_format: Mapped[str] = mapped_column(String(20), nullable=False)
    content_type: Mapped[str] = mapped_column(String(80), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    public_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    record_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    cache_hit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
