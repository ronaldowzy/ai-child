from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Child
from app.domain.companion_object import (
    CompanionObjectCreateRequest,
    CompanionObjectSource,
    CompanionObjectType,
)
from app.repositories.companion_object_sql_repository import (
    SqlAlchemyCompanionObjectRepository,
)
from app.services.companion_object_service import CompanionObjectService


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    with factory() as session:
        session.add(
            Child(
                id="child_sql_companion",
                nickname="豆豆",
                timezone="Asia/Shanghai",
            )
        )
        session.commit()
    return engine, factory


def test_companion_objects_table_contains_visual_kind_column() -> None:
    engine, _session_factory = _sqlite_session_factory()

    columns = {
        column["name"]
        for column in inspect(engine).get_columns("companion_objects")
    }

    assert "visual_kind" in columns


def test_sql_repository_persists_visual_kind_and_recall_survives_restart() -> None:
    _engine, session_factory = _sqlite_session_factory()
    repository = SqlAlchemyCompanionObjectRepository(session_factory=session_factory)
    service = CompanionObjectService(
        repository=repository,
        fallback_to_memory=False,
        now_provider=lambda: datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
    )

    created = service.create(
        CompanionObjectCreateRequest(
            child_id="child_sql_companion",
            name="小棉花",
            object_type=CompanionObjectType.STAR,
            source_type=CompanionObjectSource.FIRST_OPEN,
            safe_summary="这颗星星叫小棉花",
            light_location="窗边",
        )
    )

    restarted_service = CompanionObjectService(
        repository=SqlAlchemyCompanionObjectRepository(session_factory=session_factory),
        fallback_to_memory=False,
        now_provider=lambda: datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc),
    )
    recalled = restarted_service.can_recall(
        "child_sql_companion",
        session_id="session_after_restart",
    )

    assert created.visual_kind == "star"
    assert recalled is not None
    assert recalled.id == created.id
    assert recalled.visual_kind == "star"
