from dataclasses import asdict
from datetime import datetime
import json

import pytest
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    ConversationMessageRecord,
    ConversationSessionRecord,
    RoutingDecisionRecord,
)
from app.domain.enums import IntentType, RiskLevel
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
    ConversationMessageResponse,
    Reply,
    SessionState,
)
from app.domain.scene import SceneId, SceneRouteDecision, SceneTransitionType
from app.domain.time import TimeContext, TimePeriod
from app.repositories.conversation_persistence_repository import (
    ConversationMessageWrite,
    ConversationPersistenceRepository,
    ConversationSessionWrite,
    ConversationTurnWrite,
    RoutingDecisionWrite,
)
from app.services.conversation_persistence_service import (
    ConversationPersistenceService,
)
from app.services.conversation_service import ConversationService
from app.services.intent_classifier import IntentClassification
from app.services.scene_orchestrator import SceneOrchestrator
from app.services.safety_engine import SafetyClassification


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def _time_context() -> TimeContext:
    return TimeContext(
        now=datetime.fromisoformat("2026-05-22T16:30:00+08:00"),
        timezone="Asia/Shanghai",
        time_period=TimePeriod.AFTER_SCHOOL,
        weekday=True,
        schedule_goal="情绪缓冲",
        preferred_interactions=["兴趣切入"],
        avoid=["立刻追问学校"],
    )


def _request(
    *,
    child_id: str = "child_conversation_persistence",
    session_id: str = "session_conversation_persistence",
    text: str = "我想聊恐龙",
    attachments: list[str] | None = None,
) -> ConversationMessageRequest:
    return ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(
            type="text",
            text=text,
            attachments=attachments or [],
        ),
        client_context=ClientContext(
            device_time=datetime.fromisoformat("2026-05-22T16:30:00+08:00"),
            timezone="Asia/Shanghai",
            app_mode="child",
        ),
    )


def _response(*, audio_url: str | None = "/media/tts/test.wav") -> ConversationMessageResponse:
    return ConversationMessageResponse(
        reply=Reply(
            text="我们可以聊霸王龙，也可以聊三角龙。",
            audio_url=audio_url,
            emotion="warm",
            agent_motion="listening_tail",
        ),
        ui_actions=[],
        session_state=SessionState(
            base_scene=SceneId.OPEN_CONVERSATION.value,
            active_scene=SceneId.OPEN_CONVERSATION.value,
        ),
    )


def _route_decision(session_id: str = "session_conversation_persistence") -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id=session_id,
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.82,
        reason="test",
        reply_text="我们可以聊霸王龙，也可以聊三角龙。",
        reply_emotion="warm",
    )


def test_repository_upserts_session_and_repeated_call_updates_scene() -> None:
    session_factory = _sqlite_session_factory()
    repository = ConversationPersistenceRepository(session_factory=session_factory)

    repository.upsert_session(
        ConversationSessionWrite(
            id="session_repo_upsert",
            child_id="child_repo_upsert",
            base_scene="conversation.open",
            active_scene="conversation.open",
        )
    )
    repository.upsert_session(
        ConversationSessionWrite(
            id="session_repo_upsert",
            child_id="child_repo_upsert",
            base_scene="conversation.open",
            active_scene="learning.homework_help",
        )
    )

    with session_factory() as session:
        records = session.execute(select(ConversationSessionRecord)).scalars().all()

    assert len(records) == 1
    assert records[0].id == "session_repo_upsert"
    assert records[0].active_scene == "learning.homework_help"


def test_repository_saves_child_agent_messages_and_routing_decision() -> None:
    session_factory = _sqlite_session_factory()
    repository = ConversationPersistenceRepository(session_factory=session_factory)
    repository.upsert_session(
        ConversationSessionWrite(
            id="session_repo_messages",
            child_id="child_repo_messages",
            base_scene="conversation.open",
            active_scene="conversation.open",
        )
    )

    child_message = repository.save_message(
        ConversationMessageWrite(
            id="msg_child_repo",
            session_id="session_repo_messages",
            child_id="child_repo_messages",
            actor="child",
            message_type="text",
            normalized_text="我想聊恐龙",
            input_items=[{"type": "text"}],
            attachments=[{"id": "attachment_1", "type": "attachment"}],
            time_context={"period": "after_school"},
        )
    )
    agent_message = repository.save_message(
        ConversationMessageWrite(
            id="msg_agent_repo",
            session_id="session_repo_messages",
            child_id="child_repo_messages",
            actor="agent",
            message_type="agent_message",
            normalized_text="我们聊恐龙。",
            audio_url="/media/tts/repo.wav",
            emotion="warm",
            agent_motion="listening_tail",
        )
    )
    routing = repository.save_routing_decision(
        RoutingDecisionWrite(
            id="route_repo",
            message_id=child_message.id,
            session_id="session_repo_messages",
            primary_intent="casual_chat",
            active_scene="conversation.open",
            sub_scene=None,
            risk_level="none",
            decision={"base_scene": "conversation.open"},
            signals={"attachment_count": 1},
            confidence=0.82,
        )
    )

    assert child_message.actor == "child"
    assert child_message.message_type == "text"
    assert child_message.normalized_text == "我想聊恐龙"
    assert child_message.session_id == "session_repo_messages"
    assert child_message.child_id == "child_repo_messages"
    assert agent_message.audio_url == "/media/tts/repo.wav"
    assert agent_message.emotion == "warm"
    assert agent_message.agent_motion == "listening_tail"
    assert routing.message_id == "msg_child_repo"


def test_repository_save_turn_writes_existing_db_tables() -> None:
    session_factory = _sqlite_session_factory()
    repository = ConversationPersistenceRepository(session_factory=session_factory)

    repository.save_turn(
        ConversationTurnWrite(
            session=ConversationSessionWrite(
                id="session_repo_turn",
                child_id="child_repo_turn",
                base_scene="conversation.open",
                active_scene="conversation.open",
            ),
            child_message=ConversationMessageWrite(
                id="msg_child_turn",
                session_id="session_repo_turn",
                child_id="child_repo_turn",
                actor="child",
                message_type="text",
                normalized_text="你好",
                input_items=[{"type": "text"}],
                attachments=None,
                time_context={"period": "after_school"},
            ),
            agent_message=ConversationMessageWrite(
                id="msg_agent_turn",
                session_id="session_repo_turn",
                child_id="child_repo_turn",
                actor="agent",
                message_type="agent_message",
                normalized_text="你好呀。",
                audio_url="/media/tts/turn.wav",
                emotion="warm",
                agent_motion="listening_tail",
            ),
            routing_decision=RoutingDecisionWrite(
                id="route_turn",
                message_id="msg_child_turn",
                session_id="session_repo_turn",
                primary_intent="casual_chat",
                active_scene="conversation.open",
                sub_scene=None,
                risk_level="none",
                decision={"base_scene": "conversation.open"},
                signals={"attachment_count": 0},
                confidence=0.8,
            ),
        )
    )

    with session_factory() as session:
        db_session = session.get(ConversationSessionRecord, "session_repo_turn")
        child_message = session.get(ConversationMessageRecord, "msg_child_turn")
        agent_message = session.get(ConversationMessageRecord, "msg_agent_turn")
        routing = session.get(RoutingDecisionRecord, "route_turn")

    assert db_session is not None
    assert child_message is not None
    assert child_message.input_items == [{"type": "text"}]
    assert agent_message is not None
    assert agent_message.audio_url == "/media/tts/turn.wav"
    assert routing is not None
    assert routing.message_id == "msg_child_turn"


def test_persistence_service_builds_minimal_non_sensitive_turn_payload() -> None:
    class CapturingRepository:
        def __init__(self) -> None:
            self.turn: ConversationTurnWrite | None = None

        def save_turn(self, turn_write: ConversationTurnWrite) -> None:
            self.turn = turn_write

    repository = CapturingRepository()
    service = ConversationPersistenceService(repository=repository)

    service.record_turn(
        request=_request(attachments=["attachment_photo_1"]),
        response=_response(),
        safety=SafetyClassification(),
        intent=IntentClassification(
            intent=IntentType.CASUAL_CHAT,
            confidence=0.82,
        ),
        route_decision=_route_decision(),
        time_context=_time_context(),
    )

    assert repository.turn is not None
    assert repository.turn.child_message.actor == "child"
    assert repository.turn.agent_message.audio_url == "/media/tts/test.wav"
    assert repository.turn.routing_decision.message_id == repository.turn.child_message.id
    assert repository.turn.child_message.attachments == [
        {"id": "attachment_photo_1", "type": "attachment"}
    ]
    serialized = json.dumps(asdict(repository.turn), ensure_ascii=False)
    assert "parent_message_raw" not in serialized
    assert "prompt" not in serialized
    assert "debug" not in serialized
    assert "raw_photo" not in serialized
    assert "base64" not in serialized


def test_conversation_service_persists_successful_turn_after_audio_url() -> None:
    class AudioTtsService:
        def generate_for_conversation(self, *, text: str, emotion: str) -> str:
            return f"/media/tts/{emotion}.wav"

    class CapturingPersistenceService:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def record_turn(self, **kwargs: object) -> None:
            self.calls.append(kwargs)

    persistence = CapturingPersistenceService()
    service = ConversationService(
        scene_orchestrator=SceneOrchestrator(),
        conversation_persistence_service=persistence,
        tts_service=AudioTtsService(),
        debug_enabled=False,
    )

    response = service.handle_message(_request(text="我想聊恐龙"))

    assert response.reply.audio_url == f"/media/tts/{response.reply.emotion}.wav"
    assert len(persistence.calls) == 1
    call = persistence.calls[0]
    assert call["request"].input.text == "我想聊恐龙"
    assert call["response"].reply.audio_url == response.reply.audio_url
    assert call["route_decision"].active_scene == SceneId.OPEN_CONVERSATION
    assert "parent_policy" not in call
    assert "prompt" not in call
    assert "runtime_result" not in call


def test_conversation_service_persistence_failure_does_not_block_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FailingPersistenceService:
        def record_turn(self, **_kwargs: object) -> None:
            raise RuntimeError("simulated persistence failure")

    service = ConversationService(
        scene_orchestrator=SceneOrchestrator(),
        conversation_persistence_service=FailingPersistenceService(),
        debug_enabled=False,
    )
    request = _request(text="这句话不应该写进失败日志")

    response = service.handle_message(request)

    assert response.reply.text
    assert "conversation_persistence_failed" in caplog.text
    assert "这句话不应该写进失败日志" not in caplog.text
