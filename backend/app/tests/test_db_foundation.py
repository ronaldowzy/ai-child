from pathlib import Path

import sqlalchemy as sa

from app.core.config import get_settings
from app.db.base import Base
import app.db.models as db_models


EXPECTED_TABLES = {
    "children",
    "parent_policies",
    "conversation_sessions",
    "conversation_messages",
    "routing_decisions",
    "memory_items",
    "parent_reports",
    "tts_cache_records",
}


def test_db_metadata_includes_initial_tables() -> None:
    assert db_models.Child.__tablename__ == "children"
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_db_metadata_includes_key_columns() -> None:
    expected_columns = {
        "children": {"id", "nickname", "timezone", "created_at", "updated_at"},
        "parent_policies": {
            "id",
            "child_id",
            "goals",
            "communication_preferences",
            "safety_rules",
            "schedule",
            "child_nickname",
            "child_display_name",
            "parent_message_raw",
            "parent_message_updated_at",
            "version",
            "created_at",
            "updated_at",
        },
        "conversation_sessions": {
            "id",
            "child_id",
            "started_at",
            "ended_at",
            "base_scene",
            "active_scene",
            "created_at",
        },
        "conversation_messages": {
            "id",
            "session_id",
            "child_id",
            "actor",
            "message_type",
            "normalized_text",
            "input_items",
            "attachments",
            "audio_url",
            "emotion",
            "agent_motion",
            "time_context",
            "created_at",
        },
        "routing_decisions": {
            "id",
            "message_id",
            "session_id",
            "primary_intent",
            "active_scene",
            "risk_level",
            "decision",
            "signals",
            "confidence",
            "created_at",
        },
        "memory_items": {
            "id",
            "child_id",
            "memory_type",
            "content",
            "tags",
            "evidence",
            "confidence",
            "importance",
            "sensitivity",
            "expires_at",
            "created_at",
            "updated_at",
        },
        "parent_reports": {
            "id",
            "child_id",
            "report_date",
            "summary",
            "learning_observations",
            "expression_observations",
            "emotion_observations",
            "safety_alerts",
            "suggested_parent_actions",
            "created_at",
        },
        "tts_cache_records": {
            "id",
            "cache_key",
            "voice_version",
            "provider",
            "model",
            "emotion",
            "prompt_version",
            "voice_sample_sha256",
            "text_sha256",
            "audio_format",
            "storage_path",
            "metadata",
            "created_at",
            "updated_at",
        },
    }

    for table_name, column_names in expected_columns.items():
        assert column_names.issubset(Base.metadata.tables[table_name].columns.keys())


def test_db_json_columns_use_sqlalchemy_json_type() -> None:
    json_columns = {
        "children": {"profile"},
        "parent_policies": {
            "goals",
            "communication_preferences",
            "safety_rules",
            "schedule",
            "data_retention",
        },
        "conversation_messages": {"input_items", "attachments", "time_context"},
        "routing_decisions": {"decision", "signals"},
        "memory_items": {"tags", "evidence"},
        "parent_reports": {
            "learning_observations",
            "expression_observations",
            "emotion_observations",
            "safety_alerts",
            "suggested_parent_actions",
        },
        "tts_cache_records": {"metadata"},
    }

    for table_name, column_names in json_columns.items():
        table = Base.metadata.tables[table_name]
        for column_name in column_names:
            assert isinstance(table.c[column_name].type, sa.JSON)


def test_db_datetime_columns_are_timezone_aware() -> None:
    datetime_columns = {
        "children": {"created_at", "updated_at"},
        "parent_policies": {
            "parent_message_updated_at",
            "created_at",
            "updated_at",
        },
        "conversation_sessions": {"started_at", "ended_at", "created_at"},
        "conversation_messages": {"created_at"},
        "routing_decisions": {"created_at"},
        "memory_items": {"expires_at", "created_at", "updated_at"},
        "parent_reports": {"created_at"},
        "tts_cache_records": {"created_at", "updated_at", "last_accessed_at"},
    }

    for table_name, column_names in datetime_columns.items():
        table = Base.metadata.tables[table_name]
        for column_name in column_names:
            column_type = table.c[column_name].type
            assert isinstance(column_type, sa.DateTime)
            assert column_type.timezone is True


def test_database_url_uses_child_ai_env_prefix(monkeypatch) -> None:
    database_url = "postgresql+psycopg://child_ai:child_ai@localhost:5432/test_db"
    monkeypatch.setenv("CHILD_AI_DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        assert get_settings().database_url == database_url
    finally:
        get_settings.cache_clear()


def test_alembic_initial_revision_is_readable() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    revision_path = (
        backend_dir
        / "alembic"
        / "versions"
        / "20260520_0001_create_initial_db1a_tables.py"
    )

    assert revision_path.is_file()
    revision_text = revision_path.read_text(encoding="utf-8")
    assert 'revision: str = "20260520_0001"' in revision_text
    assert "down_revision: str | None = None" in revision_text
    assert "sa.JSON()" in revision_text
    for table_name in EXPECTED_TABLES:
        assert table_name in revision_text


def test_alembic_parent_message_revision_is_readable() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    revision_path = (
        backend_dir
        / "alembic"
        / "versions"
        / "20260521_0002_add_parent_message_to_parent_policies.py"
    )

    assert revision_path.is_file()
    revision_text = revision_path.read_text(encoding="utf-8")
    assert 'revision: str = "20260521_0002"' in revision_text
    assert 'down_revision: str | None = "20260520_0001"' in revision_text
    assert "parent_message_raw" in revision_text
    assert "parent_message_updated_at" in revision_text


def test_alembic_child_name_revision_is_readable() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    revision_path = (
        backend_dir
        / "alembic"
        / "versions"
        / "20260521_0003_add_child_names_to_parent_policies.py"
    )

    assert revision_path.is_file()
    revision_text = revision_path.read_text(encoding="utf-8")
    assert 'revision: str = "20260521_0003"' in revision_text
    assert 'down_revision: str | None = "20260521_0002"' in revision_text
    assert "child_nickname" in revision_text
    assert "child_display_name" in revision_text
