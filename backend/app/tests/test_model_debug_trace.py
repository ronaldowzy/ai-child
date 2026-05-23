import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.model_types import (
    ModelDataPolicy,
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.providers.model.base import BaseModelProvider, ModelProviderError
from app.providers.model.mock_provider import MockModelProvider
from app.repositories.model_debug_trace_repository import ModelDebugTraceRepository
from app.services.model_debug_trace_service import ModelDebugTraceService
from app.services.model_registry import ModelRegistry, ModelRegistryError


class FixedTraceProvider(BaseModelProvider):
    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        return ModelResponse(
            task_type=request.task_type,
            response_text=f"trace response for {request.task_type.value}",
            structured_output={"task": request.task_type.value, "ok": True},
            provider_name=self.provider_name,
            model_name=profile.model_name if profile else "fixed-trace-model",
            metadata={"provider_meta": "saved"},
        )


class FailingTraceProvider(BaseModelProvider):
    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        raise ModelProviderError("simulated provider failure")


class FailingTraceRepository:
    def save(self, _trace: object) -> None:
        raise RuntimeError("trace database down")


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def _trace_repository() -> ModelDebugTraceRepository:
    return ModelDebugTraceRepository(session_factory=_sqlite_session_factory())


def _trace_service(
    repository: object,
    *,
    enabled: bool = True,
    max_text_chars: int = 20000,
) -> ModelDebugTraceService:
    return ModelDebugTraceService(
        repository=repository,  # type: ignore[arg-type]
        enabled=enabled,
        full_text=True,
        max_text_chars=max_text_chars,
    )


def _profile(
    *,
    profile_name: str,
    provider_name: str,
    task_type: ModelTaskType = ModelTaskType.CHILD_CHAT,
    provider_type: ModelProviderType = ModelProviderType.MOCK,
    fallback_profile_name: str | None = None,
    data_policy: ModelDataPolicy | None = None,
) -> ModelProfile:
    return ModelProfile(
        id=profile_name,
        profile_name=profile_name,
        provider_name=provider_name,
        provider_type=provider_type,
        model_name=f"{profile_name}-model",
        task_type=task_type,
        fallback_profile_name=fallback_profile_name,
        data_policy=data_policy or ModelDataPolicy(),
    )


def _registry(
    *,
    trace_service: ModelDebugTraceService,
    task_type: ModelTaskType = ModelTaskType.CHILD_CHAT,
) -> ModelRegistry:
    return ModelRegistry(
        providers={"fixed": FixedTraceProvider(provider_name="fixed")},
        profiles={
            "fixed_profile": _profile(
                profile_name="fixed_profile",
                provider_name="fixed",
                task_type=task_type,
            )
        },
        task_profile_map={task_type: "fixed_profile"},
        model_debug_trace_service=trace_service,
    )


def _request(task_type: ModelTaskType = ModelTaskType.CHILD_CHAT) -> ModelRequest:
    return ModelRequest(
        task_type=task_type,
        messages=[
            {"role": "system", "content": "完整 system prompt"},
            {"role": "user", "content": "孩子说想聊跑步比赛"},
        ],
        input_text="孩子说想聊跑步比赛",
        context={
            "conversation": {
                "child_id": "child_trace_001",
                "session_id": "session_trace_001",
            },
            "parent_policy": {"goals": ["低压力表达"]},
        },
        metadata={"contains_child_data": True, "purpose": "trace_test"},
    )


def test_trace_disabled_does_not_write_and_generate_still_returns() -> None:
    repository = _trace_repository()
    registry = _registry(
        trace_service=_trace_service(repository, enabled=False),
    )

    response = registry.generate(_request())

    assert response.response_text == "trace response for child_chat"
    assert repository.list_recent() == []


def test_trace_enabled_saves_child_chat_request_and_response() -> None:
    repository = _trace_repository()
    registry = _registry(trace_service=_trace_service(repository))

    registry.generate(_request())
    trace = repository.list_recent(limit=1)[0]

    assert trace.task_type == "child_chat"
    assert trace.profile_name == "fixed_profile"
    assert trace.provider_name == "fixed"
    assert trace.model_name == "fixed_profile-model"
    assert trace.child_id == "child_trace_001"
    assert trace.session_id == "session_trace_001"
    assert trace.child_id_hash is not None
    assert trace.request_messages_json[0]["content"] == "完整 system prompt"
    assert trace.request_input_text == "孩子说想聊跑步比赛"
    assert trace.request_context_json["parent_policy"]["goals"] == ["低压力表达"]
    assert trace.request_metadata_json["purpose"] == "trace_test"
    assert trace.response_text == "trace response for child_chat"
    assert trace.response_structured_output_json == {"task": "child_chat", "ok": True}
    assert trace.response_metadata_json == {"provider_meta": "saved"}
    assert trace.fallback_used is False
    assert trace.policy_blocked is False
    assert trace.elapsed_ms is not None


def test_opening_greeting_model_prompt_is_saved() -> None:
    repository = _trace_repository()
    registry = _registry(trace_service=_trace_service(repository))

    registry.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            messages=[
                {
                    "role": "system",
                    "content": "opening_mode：default_light\n禁止话术：小白狐想你了",
                }
            ],
            input_text="请生成开场白。",
            context={"conversation": {"child_id": "child_opening_trace"}},
            metadata={"opening_greeting": True},
        )
    )

    trace = repository.list_recent(limit=1)[0]
    assert trace.task_type == "child_chat"
    assert "opening_mode" in trace.request_messages_json[0]["content"]
    assert trace.request_metadata_json["opening_greeting"] is True


def test_parent_report_request_and_response_are_saved() -> None:
    repository = _trace_repository()
    registry = _registry(
        trace_service=_trace_service(repository),
        task_type=ModelTaskType.PARENT_REPORT,
    )

    registry.generate(
        ModelRequest(
            task_type=ModelTaskType.PARENT_REPORT,
            messages=[
                {"role": "system", "content": "父亲日报 system prompt"},
                {"role": "user", "content": "{\"topics\":[\"跑步比赛\"]}"},
            ],
            input_text="生成父亲日报",
            context={"conversation": {"child_id": "child_report_trace"}},
            metadata={"report_date": "2026-05-23"},
        )
    )

    trace = repository.list_recent(limit=1)[0]
    assert trace.task_type == "parent_report"
    assert trace.request_messages_json[0]["content"] == "父亲日报 system prompt"
    assert trace.response_text == "trace response for parent_report"


def test_provider_fallback_records_fallback_used_and_error_type() -> None:
    repository = _trace_repository()
    registry = ModelRegistry(
        providers={
            "broken": FailingTraceProvider(provider_name="broken"),
            "mock": MockModelProvider(provider_name="mock"),
        },
        profiles={
            "broken_profile": _profile(
                profile_name="broken_profile",
                provider_name="broken",
                fallback_profile_name="mock_profile",
            ),
            "mock_profile": _profile(
                profile_name="mock_profile",
                provider_name="mock",
            ),
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "broken_profile"},
        model_debug_trace_service=_trace_service(repository),
    )

    response = registry.generate(_request())
    trace = repository.list_recent(limit=1)[0]

    assert response.provider_name == "mock"
    assert trace.profile_name == "broken_profile"
    assert trace.provider_name == "mock"
    assert trace.fallback_used is True
    assert trace.error_type == "ModelProviderError"


def test_policy_blocked_fallback_records_policy_blocked() -> None:
    repository = _trace_repository()
    registry = ModelRegistry(
        providers={
            "external": FixedTraceProvider(provider_name="external"),
            "mock": MockModelProvider(provider_name="mock"),
        },
        profiles={
            "external_profile": _profile(
                profile_name="external_profile",
                provider_name="external",
                provider_type=ModelProviderType.OPENAI_COMPATIBLE,
                fallback_profile_name="mock_profile",
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_child_data=False,
                    retention_policy_checked=True,
                ),
            ),
            "mock_profile": _profile(
                profile_name="mock_profile",
                provider_name="mock",
            ),
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "external_profile"},
        model_debug_trace_service=_trace_service(repository),
    )

    response = registry.generate(_request())
    trace = repository.list_recent(limit=1)[0]

    assert response.provider_name == "mock"
    assert trace.policy_blocked is True
    assert trace.fallback_used is True
    assert trace.error_type == "ModelDataPolicyBlockedError"


def test_final_model_error_is_recorded_before_raise() -> None:
    repository = _trace_repository()
    registry = ModelRegistry(
        providers={"broken": FailingTraceProvider(provider_name="broken")},
        profiles={
            "broken_profile": _profile(
                profile_name="broken_profile",
                provider_name="broken",
            )
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "broken_profile"},
        model_debug_trace_service=_trace_service(repository),
    )

    with pytest.raises(ModelRegistryError):
        registry.generate(_request())

    trace = repository.list_recent(limit=1)[0]
    assert trace.provider_name == "broken"
    assert trace.fallback_used is False
    assert trace.error_type == "ModelRegistryError"
    assert trace.response_text is None


def test_trace_repository_failure_does_not_block_generate() -> None:
    registry = _registry(
        trace_service=_trace_service(FailingTraceRepository()),
    )

    response = registry.generate(_request())

    assert response.response_text == "trace response for child_chat"


def test_trace_sanitizes_api_key_authorization_and_base64_payload() -> None:
    repository = _trace_repository()
    registry = _registry(
        trace_service=_trace_service(repository, max_text_chars=500),
    )
    base64_payload = "A" * 180

    registry.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请看这张测试图"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_payload}"
                            },
                        },
                    ],
                }
            ],
            input_text=f"Authorization: Bearer fake-token-value {base64_payload}",
            context={
                "conversation": {
                    "child_id": "child_trace_001",
                    "session_id": "session_trace_001",
                },
                "authorization": "Bearer fake-token-value",
            },
            metadata={
                "api_key": "test-api-key",
                "image_data_uri": f"data:image/png;base64,{base64_payload}",
            },
        )
    )

    trace = repository.list_recent(limit=1)[0]
    payload = json.dumps(trace.model_dump(mode="json"), ensure_ascii=False)
    assert "test-api-key" not in payload
    assert "fake-token-value" not in payload
    assert base64_payload not in payload
    assert "[redacted]" in payload
    assert "[raw_media_omitted]" in payload


def test_repository_clear_removes_traces() -> None:
    repository = _trace_repository()
    registry = _registry(trace_service=_trace_service(repository))

    registry.generate(_request())
    assert len(repository.list_recent()) == 1

    deleted = repository.clear()

    assert deleted == 1
    assert repository.list_recent() == []


def test_db_metadata_contains_model_debug_trace_table() -> None:
    assert "model_debug_traces" in Base.metadata.tables
