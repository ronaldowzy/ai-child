import json
import logging
import time
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.domain.schemas.parent_policy import ParentPolicyUpdateRequest
from app.main import app
from app.services.memory_service import MemoryService
from app.services.opening_service import OpeningService
from app.services.parent_policy_service import get_parent_policy_service


client = TestClient(app)


def _opening_payload(
    *,
    child_id: str,
    session_id: str = "opening-session",
    device_time: str = "2026-05-21T16:30:00+08:00",
) -> dict[str, object]:
    return {
        "child_id": child_id,
        "session_id": session_id,
        "client_context": {
            "device_time": device_time,
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }


def _update_policy(child_id: str, **kwargs: object) -> None:
    get_parent_policy_service().update_policy(
        ParentPolicyUpdateRequest(child_id=child_id, **kwargs)
    )


def test_opening_uses_child_nickname() -> None:
    child_id = "opening_nickname_child"
    _update_policy(child_id, child_nickname="豆豆", child_display_name="王小明")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id=child_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["text"].startswith("豆豆，")
    assert body["session_state"]["active_scene"] == "conversation.open"


def test_opening_uses_display_name_when_nickname_missing() -> None:
    child_id = "opening_display_name_child"
    _update_policy(child_id, child_display_name="王小明")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id=child_id),
    )

    assert response.status_code == 200
    assert response.json()["reply"]["text"].startswith("王小明，")


def test_opening_without_name_does_not_force_call_name() -> None:
    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id="opening_no_name_child"),
    )

    assert response.status_code == 200
    text = response.json()["reply"]["text"]
    assert "child" not in text
    assert "大名" not in text


def test_after_school_opening_is_light_and_not_forced_school_checkin() -> None:
    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id="opening_after_school_child"),
    )

    text = response.json()["reply"]["text"]
    assert text
    assert "今天在学校怎么样" not in text
    assert "学校" not in text


def test_bedtime_opening_is_low_stimulation() -> None:
    child_id = "opening_bedtime_child"
    _update_policy(child_id, child_nickname="豆豆")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(
            child_id=child_id,
            device_time="2026-05-21T20:40:00+08:00",
        ),
    )

    body = response.json()
    assert "一小句" in body["reply"]["text"]
    assert body["reply"]["emotion"] == "sleepy"


def test_parent_message_can_block_school_checkin() -> None:
    child_id = "opening_parent_message_no_school"
    _update_policy(child_id, parent_message_raw="不要查岗学校，不要追问。")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id=child_id),
    )

    text = response.json()["reply"]["text"]
    assert "学校" not in text
    assert "今天在学校怎么样" not in text


def test_opening_falls_back_when_model_opening_unavailable() -> None:
    class FailingOpeningModelRegistry:
        requests = 0

        def generate(self, _request):
            self.requests += 1
            raise RuntimeError("opening model unavailable")

    child_id = "opening_model_child"
    _update_policy(child_id, child_nickname="豆豆", parent_message_raw="晚上要低刺激。")
    model_registry = FailingOpeningModelRegistry()
    service = OpeningService(model_registry=model_registry)
    request = _request_model(
        child_id=child_id,
        session_id="opening-model-session",
        device_time="2026-05-21T20:40:00+08:00",
    )

    response = service.create_opening(request)

    assert response.reply.text.startswith("豆豆，")
    assert "一小句" in response.reply.text
    assert model_registry.requests == 1


def test_opening_can_use_non_mock_model_text_when_safe() -> None:
    class FixedOpeningModelRegistry:
        def generate(self, _request):
            from app.domain.model_types import ModelResponse, ModelTaskType

            return ModelResponse(
                task_type=ModelTaskType.CHILD_CHAT,
                response_text="豆豆，今天可以从恐龙或画画里选一个轻松说。",
                structured_output={},
                provider_name="fixed",
                model_name="fixed-opening",
                metadata={},
            )

    child_id = "opening_model_v2_child"
    _update_policy(
        child_id,
        child_nickname="豆豆",
        communication_preferences={"child_interests": ["恐龙", "画画"]},
    )
    service = OpeningService(model_registry=FixedOpeningModelRegistry())

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-model-v2-session",
        )
    )

    assert response.reply.text == "豆豆，今天可以从恐龙或画画里选一个轻松说。"


def test_model_opening_prompt_constrains_interest_revisit() -> None:
    child_id = "opening_prompt_contract_child"
    _update_policy(child_id, child_nickname="豆豆")
    service = OpeningService(
        memory_service=_memory_service_with_interest_seed(
            child_id=child_id,
            topic="跑步比赛",
        ),
    )
    parent_policy = get_parent_policy_service().get_policy(child_id)
    time_context = service._time_context_service.build_context(
        device_time=datetime.fromisoformat("2026-05-21T16:30:00+08:00"),
        timezone="Asia/Shanghai",
        schedule=parent_policy.schedule,
    )
    opening_policy = service._opening_policy_builder.build(
        child_id=child_id,
        parent_policy=parent_policy,
        time_context=time_context,
    )

    prompt = service._opening_prompt(
        parent_policy=parent_policy,
        time_context=time_context,
        opening_policy=opening_policy,
    )

    assert isinstance(prompt, str)
    assert "最多只轻轻回访一个低敏 topic" in prompt
    assert "必须给孩子选择权" in prompt
    assert "小白狐想你了" in prompt
    assert "每天都要来" in prompt
    assert "这是我们的小秘密" in prompt


def test_opening_model_failure_does_not_retry_more_than_once() -> None:
    class CountingOpeningModelRegistry:
        requests = 0

        def generate(self, _request):
            self.requests += 1
            raise RuntimeError("opening model unavailable")

    child_id = "opening_empty_retry_child"
    _update_policy(child_id, child_nickname="豆豆")
    model_registry = CountingOpeningModelRegistry()
    service = OpeningService(model_registry=model_registry)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-empty-retry-session",
        )
    )

    assert response.reply.text
    assert response.reply.text.startswith("豆豆，")
    assert model_registry.requests == 1


def test_opening_returns_nonempty_text_when_model_fails() -> None:
    class EmptyOpeningModelRegistry:
        requests = 0

        def generate(self, _request):
            self.requests += 1
            raise RuntimeError("opening model unavailable")

    child_id = "opening_empty_fallback_child"
    _update_policy(child_id, child_nickname="豆豆")
    model_registry = EmptyOpeningModelRegistry()
    service = OpeningService(model_registry=model_registry)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-empty-fallback-session",
        )
    )

    assert response.reply.text
    assert response.reply.text.startswith("豆豆，")
    assert model_registry.requests == 1


def test_model_opening_prompt_honors_no_school_check_without_school_word() -> None:
    child_id = "opening_prompt_no_school_child"
    _update_policy(child_id, child_nickname="豆豆", parent_message_raw="不要查岗学校。")
    service = OpeningService()
    parent_policy = get_parent_policy_service().get_policy(child_id)
    time_context = service._time_context_service.build_context(
        device_time=datetime.fromisoformat("2026-05-21T16:30:00+08:00"),
        timezone="Asia/Shanghai",
        schedule=parent_policy.schedule,
    )
    opening_policy = service._opening_policy_builder.build(
        child_id=child_id,
        parent_policy=parent_policy,
        time_context=time_context,
    )

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-prompt-no-school-session",
        )
    )

    prompt = service._opening_prompt(
        parent_policy=parent_policy,
        time_context=time_context,
        opening_policy=opening_policy,
    )
    assert isinstance(prompt, str)
    assert "学校" not in prompt
    assert "学校" not in response.reply.text


def test_opening_tts_failure_still_returns_text() -> None:
    class FailingTts:
        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            raise RuntimeError("tts failed")

    service = OpeningService(tts_service=FailingTts())
    request = _request_model(
        child_id="opening_tts_failure_child",
        session_id="opening-tts-failure",
    )

    response = service.create_opening(request)

    assert response.reply.text
    assert response.reply.audio_url is None
    assert response.reply.voice_enabled is False


def test_opening_tts_timeout_still_returns_text(caplog) -> None:
    class SlowTts:
        calls = 0

        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            self.calls += 1
            time.sleep(0.2)
            return "/media/tts/late-opening.wav"

    caplog.set_level(logging.INFO, logger="app.opening_timing")
    tts = SlowTts()
    service = OpeningService(tts_service=tts, tts_soft_timeout_ms=1)
    request = _request_model(
        child_id="opening_tts_timeout_child",
        session_id="opening-tts-timeout",
    )

    response = service.create_opening(request)

    assert response.reply.text
    assert response.reply.audio_url is None
    assert response.reply.voice_enabled is False
    assert tts.calls == 1
    record = _last_opening_timing_record(caplog)
    assert record.tts_error_type == "TimeoutError"
    assert record.audio_url_present is False


def test_opening_generates_xiaobaihu_audio_url_and_uses_session_cache() -> None:
    class CountingTts:
        calls = 0

        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            self.calls += 1
            return "/media/tts/opening.wav"

    tts = CountingTts()
    service = OpeningService(tts_service=tts)
    request = _request_model(
        child_id="opening_cached_child",
        session_id="opening-cached-session",
    )

    first = service.create_opening(request)
    second = service.create_opening(request)

    assert first.reply.text == second.reply.text
    assert first.reply.audio_url == "/media/tts/opening.wav"
    assert second.reply.audio_url == "/media/tts/opening.wav"
    assert tts.calls == 1


def test_opening_timing_log_is_structured_and_non_sensitive(caplog) -> None:
    opening_text = "豆豆，今天可以从恐龙或画画里选一个轻松说。"
    parent_secret = "parent_message_raw_secret_do_not_log"

    class FixedOpeningModelRegistry:
        def generate(self, _request):
            from app.domain.model_types import ModelResponse, ModelTaskType

            return ModelResponse(
                task_type=ModelTaskType.CHILD_CHAT,
                response_text=opening_text,
                structured_output={},
                provider_name="fixed",
                model_name="fixed-opening",
                metadata={},
            )

    class UrlTts:
        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            return "/media/tts/opening.wav"

    child_id = "opening_timing_log_child"
    _update_policy(
        child_id,
        child_nickname="豆豆",
        parent_message_raw=parent_secret,
        communication_preferences={"child_interests": ["恐龙", "画画"]},
    )
    caplog.set_level(logging.INFO, logger="app.opening_timing")
    service = OpeningService(
        model_registry=FixedOpeningModelRegistry(),
        tts_service=UrlTts(),
    )

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-timing-log-session",
        )
    )

    assert response.reply.text == opening_text
    assert response.reply.audio_url == "/media/tts/opening.wav"
    record = _last_opening_timing_record(caplog)
    assert record.model_ms is not None
    assert record.tts_ms is not None
    assert record.total_ms >= record.model_ms
    assert record.audio_url_present is True
    assert record.fallback_used is False
    assert record.child_id_hash
    assert record.session_id_hash
    payload = _opening_record_payload(record)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "model_ms" in payload
    assert "tts_ms" in payload
    assert "total_ms" in payload
    assert "audio_url_present" in payload
    assert "fallback_used" in payload
    assert parent_secret not in serialized
    assert opening_text not in serialized
    assert parent_secret not in caplog.text
    assert opening_text not in caplog.text


def test_opening_lightly_revisits_recent_interest_seed() -> None:
    child_id = "opening_relationship_seed_child"
    _update_policy(child_id, child_nickname="豆豆")
    memory_service = _memory_service_with_interest_seed(
        child_id=child_id,
        topic="跑步比赛",
    )
    service = OpeningService(memory_service=memory_service)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-relationship-seed",
        )
    )

    assert "豆豆，" in response.reply.text
    assert "跑步比赛" in response.reply.text
    assert "想你" not in response.reply.text
    assert "每天都要" not in response.reply.text


def test_opening_fallback_respects_topic_boundary() -> None:
    child_id = "opening_relationship_boundary_child"
    _update_policy(child_id, child_nickname="豆豆")
    memory_service = _memory_service_with_interest_seed(
        child_id=child_id,
        topic="跑步比赛",
    )
    _create_topic_boundary(
        memory_service=memory_service,
        child_id=child_id,
        kind="topic_change",
        topic="换话题边界",
    )
    service = OpeningService(memory_service=memory_service)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-relationship-boundary",
        )
    )

    assert "跑步比赛" not in response.reply.text
    assert "先不聊" in response.reply.text


def test_opening_uses_latest_low_sensitivity_interest_seed() -> None:
    child_id = "opening_relationship_latest_seed_child"
    repository = InMemoryMemoryRepository()
    old_service = MemoryService(
        repository=repository,
        now_provider=lambda: datetime(2026, 5, 20, 8, 0, tzinfo=timezone.utc),
    )
    _create_interest_seed(
        memory_service=old_service,
        child_id=child_id,
        topic="恐龙",
    )
    new_service = MemoryService(
        repository=repository,
        now_provider=lambda: datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
    )
    _create_interest_seed(
        memory_service=new_service,
        child_id=child_id,
        topic="跑步比赛",
    )
    service = OpeningService(memory_service=new_service)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-relationship-latest-seed",
        )
    )

    assert "跑步比赛" in response.reply.text
    assert "恐龙" not in response.reply.text


def test_opening_does_not_revisit_medium_or_high_sensitivity_interest_seed() -> None:
    child_id = "opening_relationship_sensitivity_seed_child"
    repository = InMemoryMemoryRepository()
    low_service = MemoryService(
        repository=repository,
        now_provider=lambda: datetime(2026, 5, 20, 8, 0, tzinfo=timezone.utc),
    )
    _create_interest_seed(
        memory_service=low_service,
        child_id=child_id,
        topic="恐龙",
        sensitivity=MemorySensitivity.LOW,
    )
    medium_service = MemoryService(
        repository=repository,
        now_provider=lambda: datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
    )
    _create_interest_seed(
        memory_service=medium_service,
        child_id=child_id,
        topic="跑步比赛",
        sensitivity=MemorySensitivity.MEDIUM,
    )
    service = OpeningService(memory_service=medium_service)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-relationship-sensitivity-seed",
        )
    )

    assert "恐龙" in response.reply.text
    assert "跑步比赛" not in response.reply.text


def test_opening_without_interest_seed_keeps_existing_fallback() -> None:
    service = OpeningService(
        memory_service=MemoryService(repository=InMemoryMemoryRepository())
    )

    response = service.create_opening(
        _request_model(
            child_id="opening_no_relationship_seed",
            session_id="opening-no-relationship-seed",
        )
    )

    assert response.reply.text
    assert "上次聊到" not in response.reply.text


def test_bedtime_opening_with_interest_seed_is_low_stimulation() -> None:
    child_id = "opening_relationship_bedtime_child"
    _update_policy(child_id, child_nickname="豆豆")
    memory_service = _memory_service_with_interest_seed(
        child_id=child_id,
        topic="跑步比赛",
    )
    service = OpeningService(memory_service=memory_service)

    response = service.create_opening(
        _request_model(
            child_id=child_id,
            session_id="opening-relationship-bedtime",
            device_time="2026-05-21T20:40:00+08:00",
        )
    )

    assert "跑步比赛" in response.reply.text
    assert "明天白天再慢慢说" in response.reply.text
    assert "继续聊一点" not in response.reply.text


def _memory_service_with_interest_seed(
    *,
    child_id: str,
    topic: str,
) -> MemoryService:
    memory_service = MemoryService(repository=InMemoryMemoryRepository())
    _create_interest_seed(
        memory_service=memory_service,
        child_id=child_id,
        topic=topic,
    )
    return memory_service


def _create_interest_seed(
    *,
    memory_service: MemoryService,
    child_id: str,
    topic: str,
    sensitivity: MemorySensitivity = MemorySensitivity.LOW,
) -> None:
    memory_service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.INTEREST,
            content=f"孩子近期自然聊到{topic}，可作为低压力回访的兴趣种子。",
            tags=["relationship_memory", "interest_seed", topic],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="opening_relationship_seed_source",
                    quote_summary=f"孩子自然提到{topic}相关内容，适合短期轻回访。",
                    metadata={
                        "relationship_memory_type": "interest_seed",
                        "topic": topic,
                        "next_hook": "下次可轻轻问一个具体细节。",
                    },
                )
            ],
            sensitivity=sensitivity,
            confidence=0.8,
            importance=0.5,
        )
    )


def _create_topic_boundary(
    *,
    memory_service: MemoryService,
    child_id: str,
    kind: str,
    topic: str,
) -> None:
    memory_service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.STRATEGY,
            content="孩子明确表达想换话题，后续应尊重转场，不继续追问旧话题。",
            tags=["relationship_memory", "topic_boundary", "尊重边界"],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="opening_relationship_boundary_source",
                    quote_summary="孩子表达想换个话题或不继续当前话题。",
                    metadata={
                        "relationship_memory_type": "topic_boundary",
                        "topic": topic,
                        "boundary_kind": kind,
                        "next_hook": "下次给两个轻松方向。",
                    },
                )
            ],
            sensitivity=MemorySensitivity.LOW,
            confidence=0.84,
            importance=0.62,
        )
    )


def _request_model(
    *,
    child_id: str,
    session_id: str,
    device_time: str = "2026-05-21T16:30:00+08:00",
):
    from app.domain.schemas.conversation import (
        ClientContext,
        ConversationOpeningRequest,
    )

    return ConversationOpeningRequest(
        child_id=child_id,
        session_id=session_id,
        client_context=ClientContext(
            device_time=datetime.fromisoformat(device_time),
            timezone="Asia/Shanghai",
            app_mode="child",
        ),
    )


def _last_opening_timing_record(caplog):
    records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "conversation_opening_finished"
    ]
    assert records
    return records[-1]


def _opening_record_payload(record) -> dict[str, object]:
    keys = [
        "event",
        "request_id",
        "child_id_hash",
        "session_id_hash",
        "opening_policy_mode",
        "cache_hit",
        "model_ms",
        "tts_ms",
        "total_ms",
        "audio_url_present",
        "fallback_used",
        "model_error_type",
        "tts_error_type",
        "opening_text_chars",
    ]
    return {key: getattr(record, key, None) for key in keys}
