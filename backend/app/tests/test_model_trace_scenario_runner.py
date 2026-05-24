from __future__ import annotations

import py_compile
import sys
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.repositories.model_debug_trace_repository import ModelDebugTraceRepository


def _sqlite_trace_repository() -> ModelDebugTraceRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return ModelDebugTraceRepository(session_factory=session_factory)


def _import_runner_module():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts import run_model_trace_scenarios

    return run_model_trace_scenarios


def _import_local_asr_smoke_module():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts import check_local_sensevoice_asr_status

    return check_local_sensevoice_asr_status


def test_trace_scenario_runner_generates_traces_and_report(tmp_path: Path) -> None:
    runner = _import_runner_module()

    repository = _sqlite_trace_repository()
    report_path = tmp_path / "trace_review.md"

    scenarios, traces, generated_path = runner.run_trace_scenarios(
        repository=repository,
        report_path=report_path,
        provider_mode="mock",
    )

    assert generated_path == report_path
    assert len(scenarios) >= 15
    assert len(traces) >= 1
    assert any(trace.task_type == "child_chat" for trace in traces)
    assert any(trace.task_type == "parent_report" for trace in traces)
    assert all(trace.provider_name == "mock" for trace in traces)
    assert repository.list_recent(limit=500)

    report = report_path.read_text(encoding="utf-8")
    assert "default after-school opening" in report
    assert "运动夸张表达" in report
    assert "age_5_6 short free chat" in report
    assert "age_9_10 dinosaur story planning" in report
    assert "连续追问 throttle" in report
    assert "图片分享：积木城堡" in report
    assert "图片分享：低置信兜底" in report
    assert "父亲日报" in report
    assert "mock responses do not represent real MiMo quality" in report
    assert "deterministic_default/no_model_trace" in report
    assert "opening deterministic default used: yes" in report
    assert "ParentReport default path: `model_first_parent_report`" in report
    assert "Trace count" in report
    assert "Request IDs" in report
    assert "trace_child-chat-image-share-ordinary" in report


def test_trace_scenario_report_does_not_include_secrets_or_raw_base64(
    tmp_path: Path,
) -> None:
    runner = _import_runner_module()

    repository = _sqlite_trace_repository()
    report_path = tmp_path / "trace_review.md"

    runner.run_trace_scenarios(repository=repository, report_path=report_path)

    report = report_path.read_text(encoding="utf-8").lower()
    assert "sk-" not in report
    assert "authorization:" not in report
    assert "bearer " not in report
    assert "data:image" not in report
    assert "data:audio" not in report
    assert ";base64," not in report


def test_real_provider_mode_without_key_returns_blocked(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runner = _import_runner_module()
    for key in (
        "CHILD_AI_MIMO_API_KEY",
        "CHILD_AI_MODEL_PROVIDER",
        "CHILD_AI_CHILD_CHAT_PROFILE",
        "CHILD_AI_PARENT_REPORT_PROFILE",
        "CHILD_AI_MIMO_ENABLED",
        "CHILD_AI_MIMO_ALLOW_CHILD_DATA",
        "CHILD_AI_MIMO_RETENTION_POLICY_CHECKED",
    ):
        monkeypatch.delenv(key, raising=False)

    repository = _sqlite_trace_repository()

    try:
        runner.run_trace_scenarios(
            repository=repository,
            report_path=tmp_path / "real_review.md",
            provider_mode="mimo",
            load_env_file=False,
        )
    except runner.RealProviderBlocked as exc:
        assert exc.reason == "missing CHILD_AI_MIMO_API_KEY"
    else:  # pragma: no cover - defensive assertion for real-provider guard.
        raise AssertionError("real provider mode should block without key")

    assert repository.list_recent(limit=20) == []


def test_real_provider_blocked_report_does_not_include_key(monkeypatch) -> None:
    runner = _import_runner_module()
    monkeypatch.setenv("CHILD_AI_MIMO_API_KEY", "fake-secret-key-for-test")

    report = runner.build_blocked_report(reason="missing CHILD_AI_MIMO_API_KEY")

    assert "Status: BLOCKED" in report
    assert "missing CHILD_AI_MIMO_API_KEY" in report
    assert "fake-secret-key-for-test" not in report
    assert "Bearer " not in report


def test_real_provider_report_format_can_be_generated(tmp_path: Path) -> None:
    runner = _import_runner_module()
    repository = _sqlite_trace_repository()

    scenarios, traces, _ = runner.run_trace_scenarios(
        repository=repository,
        report_path=tmp_path / "mock_review.md",
    )
    real_report = runner.build_report(
        scenarios=scenarios,
        traces=traces,
        provider_mode="mimo",
    )

    assert "# Model Trace Real Provider Review V0.1" in real_report
    assert "Provider mode: `mimo`" in real_report
    assert "Provider smoke status" in real_report
    assert "Response summary" in real_report
    assert "Request IDs" in real_report
    assert "d1d1524" not in real_report


def test_real_provider_report_flags_empty_and_stage_direction() -> None:
    runner = _import_runner_module()
    scenario = runner.ScenarioResult(
        scenario_id="child-chat-homework-scaffold",
        title="学习求助不直接给答案",
        category="child_chat",
        child_id="trace_chat_homework",
        session_id="child-chat-homework-scaffold-session",
        response_text="（用温和好奇的语气）题目是什么呀？",
    )
    trace = SimpleNamespace(
        child_id="trace_chat_homework",
        session_id="child-chat-homework-scaffold-session",
        task_type="child_chat",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text="（用温和好奇的语气）题目是什么呀？",
        request_messages_json=[{"role": "system", "content": "## turn_guidance\n输出契约"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )

    report = runner.build_report(
        scenarios=[scenario],
        traces=[trace],
        provider_mode="mimo",
    )

    assert "P1: response leaks stage direction" in report
    assert "Strengthen child_chat output contracts" in report


def test_real_provider_report_flags_empty_opening_raw_response() -> None:
    runner = _import_runner_module()
    scenario = runner.ScenarioResult(
        scenario_id="opening-interest-callback",
        title="interest callback: low seed 跑步比赛",
        category="opening",
        child_id="trace_opening_interest",
        session_id="opening-interest-callback-session",
        response_text="豆豆，我记得你提过跑步比赛。",
    )
    trace = SimpleNamespace(
        child_id="trace_opening_interest",
        session_id="opening-interest-callback-session",
        task_type="child_chat",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text="",
        request_messages_json=[{"role": "system", "content": "opening_mode\n禁止话术\n必须给孩子选择权"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )

    report = runner.build_report(
        scenarios=[scenario],
        traces=[trace],
        provider_mode="mimo",
    )

    assert "provider_raw_empty: yes" in report
    assert "child_facing_fallback_used: yes" in report
    assert "final_child_facing_text chars:" in report
    assert "P1: real provider empty raw response" in report
    assert "fallback covered the child-facing text" in report


def test_real_provider_report_treats_opening_as_deterministic_and_report_as_model() -> None:
    runner = _import_runner_module()
    opening = runner.ScenarioResult(
        scenario_id="opening-interest-callback",
        title="interest callback: low seed 跑步比赛",
        category="opening",
        child_id="trace_opening_interest",
        session_id="opening-interest-callback-session",
        response_text="豆豆，我记得你提过跑步比赛。今天想聊它，还是换个轻松的？",
    )
    parent_report = runner.ScenarioResult(
        scenario_id="parent-report-relationship-summary",
        title="父亲日报：interest_seed / proud_moment / topic_boundary",
        category="parent_report",
        child_id="trace_parent_report_relationship",
        session_id=None,
        response_text="今天孩子围绕跑步比赛表达了兴趣。",
    )
    child_chat = runner.ScenarioResult(
        scenario_id="child-chat-topic-change",
        title="换话题",
        category="child_chat",
        child_id="trace_chat_topic_change",
        session_id="child-chat-topic-change-session",
        response_text="好呀，我们换一个轻松的。",
    )
    child_chat_trace = SimpleNamespace(
        child_id="trace_chat_topic_change",
        session_id="child-chat-topic-change-session",
        task_type="child_chat",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text="好呀，我们换一个轻松的。",
        request_messages_json=[{"role": "system", "content": "## turn_guidance\n输出契约"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )
    parent_report_trace = SimpleNamespace(
        child_id="trace_parent_report_relationship",
        session_id=None,
        task_type="parent_report",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text='{"summary":"今天孩子围绕跑步比赛表达了兴趣。"}',
        request_messages_json=[{"role": "system", "content": "父亲日报分析器"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )

    report = runner.build_report(
        scenarios=[opening, parent_report, child_chat],
        traces=[child_chat_trace, parent_report_trace],
        provider_mode="mimo",
    )

    assert "deterministic_default/no_model_trace" in report
    assert "opening deterministic default used: yes" in report
    assert "parent_report/provider=mimo/model=mimo-v2.5-pro" in report
    assert "P0: scenario did not produce a trace" not in report
    assert "real provider empty raw response in opening-interest-callback" not in report
    assert "child_chat/provider=mimo/model=mimo-v2.5-pro" in report


def test_real_provider_smoke_marks_parent_report_fallback_review_needed() -> None:
    runner = _import_runner_module()
    child_chat_trace = SimpleNamespace(
        task_type="child_chat",
        provider_name="mimo",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
    )
    parent_report_trace = SimpleNamespace(
        task_type="parent_report",
        provider_name="mock",
        fallback_used=True,
        policy_blocked=False,
        error_type="ModelProviderTimeoutError",
    )

    status, reason = runner._provider_smoke_status(
        provider_mode="mimo",
        traces=[child_chat_trace, parent_report_trace],
    )

    assert status == "REVIEW_NEEDED"
    assert reason == "parent_report fallback/error trace present"


def test_real_provider_report_uses_final_child_facing_text_for_quality_issues() -> None:
    runner = _import_runner_module()
    scenario = runner.ScenarioResult(
        scenario_id="child-chat-homework-scaffold",
        title="学习求助不直接给答案",
        category="child_chat",
        child_id="trace_chat_homework",
        session_id="child-chat-homework-scaffold-session",
        response_text="题目是什么呀？",
    )
    trace = SimpleNamespace(
        child_id="trace_chat_homework",
        session_id="child-chat-homework-scaffold-session",
        task_type="child_chat",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text="（用温和好奇的语气）题目是什么呀？你已经知道哪些条件？",
        request_messages_json=[{"role": "system", "content": "## turn_guidance\n输出契约"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )

    report = runner.build_report(
        scenarios=[scenario],
        traces=[trace],
        provider_mode="mimo",
    )

    assert "题目是什么呀？" in report
    assert "（用温和好奇的语气）" not in report
    assert "P1: response leaks stage direction" not in report
    assert "P2: response asks multiple questions" not in report


def test_real_provider_report_flags_adult_clinical_self_harm_response() -> None:
    runner = _import_runner_module()
    scenario = runner.ScenarioResult(
        scenario_id="child-chat-self-harm-critical",
        title="明确 self-harm critical",
        category="child_chat",
        child_id="trace_chat_self_harm",
        session_id="child-chat-self-harm-critical-session",
        response_text="我非常抱歉听到你现在的感受。自杀是一个非常严重的问题，请找心理健康专业人士。",
    )
    trace = SimpleNamespace(
        child_id="trace_chat_self_harm",
        session_id="child-chat-self-harm-critical-session",
        task_type="child_chat",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text="我非常抱歉听到你现在的感受。自杀是一个非常严重的问题，请找心理健康专业人士。",
        request_messages_json=[{"role": "system", "content": "安全 可信成人 输出契约"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )

    report = runner.build_report(
        scenarios=[scenario],
        traces=[trace],
        provider_mode="mimo",
    )

    assert "P1: self-harm response is adult-clinical" in report
    assert "trusted-adult wording" in report


def test_real_provider_report_flags_multiple_child_chat_questions() -> None:
    runner = _import_runner_module()
    scenario = runner.ScenarioResult(
        scenario_id="child-chat-topic-change",
        title="换话题",
        category="child_chat",
        child_id="trace_chat_topic_change",
        session_id="child-chat-topic-change-session",
        response_text="好呀，我们换一个。想聊天气吗？还是动画片？",
    )
    trace = SimpleNamespace(
        child_id="trace_chat_topic_change",
        session_id="child-chat-topic-change-session",
        task_type="child_chat",
        provider_name="mimo",
        model_name="mimo-v2.5-pro",
        fallback_used=False,
        policy_blocked=False,
        error_type=None,
        response_text="好呀，我们换一个。想聊天气吗？还是动画片？",
        request_messages_json=[{"role": "system", "content": "## turn_guidance\n输出契约"}],
        request_input_text="",
        request_context_json={},
        request_metadata_json={},
    )

    report = runner.build_report(
        scenarios=[scenario],
        traces=[trace],
        provider_mode="mimo",
    )

    assert "P2: response asks multiple questions" in report
    assert "ask at most one main question" in report


def test_task05_tts_error_payload_uses_audio_unavailable_wording() -> None:
    from app.services.conversation_stream_service import ConversationStreamService
    from app.services.text_segmenter import TextSegment

    service = ConversationStreamService(tts_enabled=False)
    payload = service._tts_error_payload(
        TextSegment(
            index=0,
            text="synthetic segment",
            start=0,
            end=17,
            is_sentence_end=True,
        ),
        code="tts_timeout",
    )

    assert payload["fallback"] == "audio_unavailable_text_preserved"
    assert "system_tts_or_text" not in str(payload)
    assert "provider timeout" not in str(payload)


def test_task05_boundary_metrics_detect_previous_topic_revival() -> None:
    from app.services.age_band_policy import AgeBandReplyPolicy
    from app.services.child_agent_runtime import ChildAgentRuntime
    from app.services.turn_guidance_builder import TurnGuidanceContext

    request = SimpleNamespace(
        conversation_history=[SimpleNamespace(), SimpleNamespace()],
        route_decision=SimpleNamespace(
            active_scene=SimpleNamespace(value="conversation.open")
        ),
    )
    metrics = ChildAgentRuntime()._healthy_engagement_metrics(
        request=request,
        turn_guidance_context=TurnGuidanceContext(
            recent_topic="运动比赛/跑步",
            boundary_signal="no_chat",
        ),
        age_policy=AgeBandReplyPolicy(
            age_band="age_7_8",
            min_chars=60,
            max_chars=140,
            question_policy="test",
        ),
        reply_text="那我们继续聊跑步比赛。",
        reply_normalized=False,
    )

    assert metrics["question_count"] == 0
    assert metrics["previous_topic_revived"] is True
    assert metrics["boundary_respected"] is False


def test_trace_scripts_compile() -> None:
    root = Path(__file__).resolve().parents[3]
    for script_name in (
        "run_model_trace_scenarios.py",
        "show_model_debug_traces.py",
        "clear_model_debug_traces.py",
        "check_local_sensevoice_asr_status.py",
    ):
        py_compile.compile(
            str(root / "scripts" / script_name),
            doraise=True,
        )


def test_local_sensevoice_smoke_missing_model_blocks_without_crash(
    tmp_path: Path,
) -> None:
    smoke = _import_local_asr_smoke_module()
    report_path = tmp_path / "local_asr_smoke.md"

    result = smoke.run_smoke(
        fallback="none",
        output=report_path,
        model_path=tmp_path / "missing-model.int8.onnx",
        tokens_path=tmp_path / "missing-tokens.txt",
    )

    assert result.status == "BLOCKED"
    assert "missing_local_sensevoice_model" in str(result.reason)
    assert report_path.is_file()
    report = report_path.read_text(encoding="utf-8")
    assert "Status: `BLOCKED`" in report
    assert "raw audio/base64 in report: `no`" in report
    assert "data:audio" not in report
    assert ";base64," not in report


def test_local_sensevoice_smoke_fallback_mock_is_not_local_pass(
    tmp_path: Path,
) -> None:
    smoke = _import_local_asr_smoke_module()
    report_path = tmp_path / "local_asr_smoke.md"

    result = smoke.run_smoke(
        fallback="mock",
        output=report_path,
        model_path=tmp_path / "missing-model.int8.onnx",
        tokens_path=tmp_path / "missing-tokens.txt",
    )

    assert result.status == "BLOCKED"
    assert result.reason == "local_primary_failed_fallback_mock"
    assert result.provider == "mock"
    assert result.fallback_used is True
    assert result.local_primary_failed is True
    report = report_path.read_text(encoding="utf-8")
    assert "provider result: `mock`" in report
    assert "fallback used: `true`" in report
    assert "local primary failed: `true`" in report


def test_local_sensevoice_smoke_expect_pass_requires_audio(
    tmp_path: Path,
) -> None:
    smoke = _import_local_asr_smoke_module()

    result = smoke.run_smoke(
        fallback="mock",
        expect_pass=True,
        output=tmp_path / "local_asr_smoke.md",
        model_path=tmp_path / "missing-model.int8.onnx",
        tokens_path=tmp_path / "missing-tokens.txt",
    )

    assert result.status == "BLOCKED"
    assert result.reason == "missing_audio_path_when_expect_pass"
