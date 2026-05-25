from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Child, ParentPolicyRecord
from app.domain.schemas.parent_policy import ParentPolicyUpdateRequest
from app.repositories.parent_policy_repository import ParentPolicyRepository
from app.services.parent_policy_service import ParentPolicyService


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def test_parent_policy_service_persists_parent_message_with_repository() -> None:
    session_factory = _sqlite_session_factory()
    repository = ParentPolicyRepository(session_factory=session_factory)
    service = ParentPolicyService(repository=repository, fallback_to_memory=False)
    child_id = "child_parent_message_db_test"
    parent_message = "小名叫豆豆，最近喜欢恐龙。不要说孩子胆小。"

    saved = service.update_policy(
        ParentPolicyUpdateRequest(
            child_id=child_id,
            parent_message_raw=parent_message,
        )
    )

    reloaded_service = ParentPolicyService(
        repository=repository,
        fallback_to_memory=False,
    )
    reloaded = reloaded_service.get_policy(child_id)

    assert saved.parent_message_raw == parent_message
    assert saved.parent_message_updated_at is not None
    assert reloaded.parent_message_raw == parent_message
    assert reloaded.parent_message_updated_at == saved.parent_message_updated_at


def test_parent_policy_service_persists_child_names_with_repository() -> None:
    session_factory = _sqlite_session_factory()
    repository = ParentPolicyRepository(session_factory=session_factory)
    service = ParentPolicyService(repository=repository, fallback_to_memory=False)
    child_id = "child_names_db_test"

    saved = service.update_policy(
        ParentPolicyUpdateRequest(
            child_id=child_id,
            child_nickname="豆豆",
            child_display_name="王小明",
        )
    )

    reloaded = ParentPolicyService(
        repository=repository,
        fallback_to_memory=False,
    ).get_policy(child_id)

    assert saved.child_nickname == "豆豆"
    assert saved.child_display_name == "王小明"
    assert reloaded.child_nickname == "豆豆"
    assert reloaded.child_display_name == "王小明"


def test_parent_policy_child_profile_uses_children_table_as_source() -> None:
    session_factory = _sqlite_session_factory()
    repository = ParentPolicyRepository(session_factory=session_factory)
    service = ParentPolicyService(repository=repository, fallback_to_memory=False)
    child_id = "child_profile_single_source_test"

    saved = service.update_policy(
        ParentPolicyUpdateRequest(
            child_id=child_id,
            child_nickname="豆豆",
            child_display_name="王小明",
            communication_preferences={
                "tone": "warm_calm",
                "child_age": 8,
                "child_grade": "二年级",
                "child_call_preference": "小名",
                "child_interests": ["恐龙", "画画"],
                "topic_boundaries": ["比赛成绩"],
            },
        )
    )

    with session_factory() as session:
        child = session.get(Child, child_id)
        policy_record = session.execute(
            select(ParentPolicyRecord).where(ParentPolicyRecord.child_id == child_id)
        ).scalar_one()

    assert child is not None
    assert child.nickname == "豆豆"
    assert child.age == 8
    assert child.grade == "二年级"
    assert child.profile["child_nickname"] == "豆豆"
    assert child.profile["child_display_name"] == "王小明"
    assert child.profile["child_interests"] == ["恐龙", "画画"]
    assert policy_record.child_nickname is None
    assert policy_record.child_display_name is None
    assert "child_age" not in policy_record.communication_preferences
    assert "child_grade" not in policy_record.communication_preferences

    reloaded = ParentPolicyService(
        repository=repository,
        fallback_to_memory=False,
    ).get_policy(child_id)

    assert saved.communication_preferences["child_age"] == 8
    assert reloaded.child_nickname == "豆豆"
    assert reloaded.child_display_name == "王小明"
    assert reloaded.communication_preferences["child_grade"] == "二年级"
    assert reloaded.communication_preferences["child_interests"] == ["恐龙", "画画"]
