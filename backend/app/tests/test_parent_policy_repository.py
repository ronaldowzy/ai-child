from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
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
