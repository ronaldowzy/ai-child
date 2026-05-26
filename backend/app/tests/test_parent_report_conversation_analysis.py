from datetime import date, datetime, timezone
import json

from app.domain.model_types import ModelResponse, ModelTaskType
from app.domain.parent_report import ParentReportGenerationStatus
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService


def _fixed_now() -> datetime:
    return datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)


class FakeConversationRepository:
    def __init__(self, messages=None):
        self.messages = messages or []

    def list_report_messages(self, *, child_id, report_date):
        return [m for m in self.messages if m.created_at.date() == report_date]


class SuccessfulParentReportModelRegistry:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return ModelResponse(
            task_type=ModelTaskType.PARENT_REPORT,
            response_text="",
            structured_output={
                "daily_report": {
                    "summary": "模型日报：基于当天素材生成。",
                    "topic_overview": [],
                    "conversation_summary": "今天聊了一些日常话题。",
                    "learning_observations": [],
                    "expression_observations": [],
                    "emotion_observations": [],
                    "safety_alerts": [],
                    "suggested_parent_actions": ["今晚可以轻轻问一个小细节。"],
                    "tonight_parent_bridge": "今晚可以轻轻聊点轻松的。",
                    "avoid_followup": ["不要连续追问。"],
                }
            },
            provider_name="mimo",
            model_name="mimo-v2.5-pro",
            metadata={},
        )


def _payload_from_request(request):
    content = request.messages[-1].content
    if isinstance(content, list):
        raise AssertionError("parent report test request should be text JSON")
    if content.startswith("上一次输出为空或不可解析。"):
        content = content.split("\n", 1)[1]
    return json.loads(content)


SPORT_CONVERSATION = [
    "按一下。好，说完就行。说完了以后再按一下，说完了。我要参加比赛了。",
    "我参加的是运动比赛。",
    "跑步",
    "快的感觉",
    "我每天都跑十五公里",
    "我跑完腿不会酸，我跑完的感觉是要死了。",
    "知道",
    "我是跑完才出现的，而且我跑完不疼。",
    "我就是有比赛",
    "行，我们聊点别的话题。",
    "我们明天再聊，我得睡觉了。",
]


def _message(index: int, text: str) -> ConversationReportMessage:
    return ConversationReportMessage(
        id=f"msg_child_sports_{index}",
        session_id="sports_report_session",
        actor="child",
        message_type="text",
        normalized_text=text,
        active_scene="conversation.open",
        risk_level="none",
        attachments_count=0,
        created_at=datetime(2026, 5, 22, 20, index, tzinfo=timezone.utc),
    )


def _conversation_message(
    *,
    message_id: str,
    actor: str = "child",
    text: str | None,
    active_scene: str | None = "conversation.open",
    risk_level: str | None = "none",
    attachments_count: int = 0,
    created_at: datetime = datetime(2026, 5, 18, 10, 30, tzinfo=timezone.utc),
) -> ConversationReportMessage:
    return ConversationReportMessage(
        id=message_id,
        session_id="realistic_report_session",
        actor=actor,
        message_type="text",
        normalized_text=text,
        active_scene=active_scene,
        risk_level=risk_level,
        attachments_count=attachments_count,
        created_at=created_at,
    )


def test_parent_report_extracts_sports_topic_without_learning_misroute() -> None:
    service = ParentReportService()
    analysis = service._conversation_analysis(
        [_message(index, text) for index, text in enumerate(SPORT_CONVERSATION)]
    )

    assert "运动比赛/跑步" in analysis["topics"]
    assert "学习求助" not in analysis["topics"]
    assert any("连续表达" in item for item in analysis["expression_observations"])
    assert any("换个话题" in item for item in analysis["expression_observations"])
    assert any("跑后" in item or "夸张疲惫" in item for item in analysis["emotion_observations"])
    assert not any("自伤" in item for item in analysis["safety_alerts"])
    assert not any("自伤" in item for item in analysis["emotion_observations"])


def test_parent_report_sports_actions_are_specific_and_low_pressure() -> None:
    service = ParentReportService()
    actions = service._suggested_actions(
        memories=[],
        has_learning=False,
        has_expression=True,
        has_emotion=True,
        has_safety=False,
        conversation_topics=["运动比赛/跑步"],
    )

    assert any("温和确认" in action for action in actions)
    assert any("不要否定夸张表达" in action for action in actions)
    assert any("不要追问太久" in action for action in actions)
    assert not any("最终答案" in action for action in actions)


def test_parent_report_learning_topic_requires_real_learning_help() -> None:
    service = ParentReportService()
    analysis = service._conversation_analysis(
        [
            _message(0, "行，我们聊点别的话题。"),
            _message(1, "我就是有比赛。"),
        ]
    )

    assert "学习求助" not in analysis["topics"]

    learning = service._conversation_analysis(
        [_message(2, "我有一道数学题不会做。")]
    )

    assert "学习求助" in learning["topics"]


def test_parent_report_summary_keeps_sports_mainline() -> None:
    service = ParentReportService()
    messages = [
        _message(index, text) for index, text in enumerate(SPORT_CONVERSATION)
    ]
    analysis = service._conversation_analysis(messages)
    summary = service._summary(
        memories=[],
        conversation_messages=messages,
        conversation_topics=analysis["topics"],
        conversation_state=analysis["state_summary"],
        has_learning=bool(analysis["learning_observations"]),
        has_expression=bool(analysis["expression_observations"]),
        has_emotion=bool(analysis["emotion_observations"]),
        has_safety=bool(analysis["safety_alerts"]),
    )

    assert "运动比赛/跑步" in summary
    assert "学习支持" not in summary
    assert any("不应误判为学习求助" in item for item in analysis["state_summary"])
    assert date(2026, 5, 22) == messages[0].created_at.date()


def test_parent_report_extracts_game_topic_content_bridge() -> None:
    service = ParentReportService()
    analysis = service._conversation_analysis(
        [
            _message(0, "我和朋友玩 CS 的地图。"),
            _message(1, "队友配合还行，最后我们输了。"),
            _message(2, "嗯，随便。"),
        ]
    )

    assert "游戏/CS" in analysis["topics"]
    game_topic = next(item for item in analysis["topic_overview"] if item.topic == "游戏/CS")
    assert "地图" in game_topic.summary
    assert "队友或朋友配合" in game_topic.summary
    assert "输赢感受" in game_topic.summary
    assert "游戏/CS" in analysis["conversation_summary"][0]
    assert "输赢感受" in analysis["conversation_summary"][0]
    assert any("时长盘问" in item for item in analysis["avoid_followup"])


REALISTIC_CONVERSATION = [
    "我明天要参加比赛，有点紧张。",
    "是学校里的跑步比赛，我怕跑不好。",
    "我拍了一张图给你看，这是我画的画。",
    "你觉得这个颜色怎么样？",
    "好，我要去英语打卡了，一会再聊。",
]


def test_parent_report_realistic_conversation_covers_key_topics() -> None:
    service = ParentReportService()
    messages = [
        ConversationReportMessage(
            id=f"msg_realistic_{index}",
            session_id="realistic_report_session",
            actor="child" if index % 2 == 0 else "agent",
            message_type="text" if index != 2 else "text",
            normalized_text=text,
            active_scene="conversation.open",
            risk_level="none",
            attachments_count=1 if index == 2 else 0,
            created_at=datetime(2026, 5, 22, 20, index, tzinfo=timezone.utc),
        )
        for index, text in enumerate(REALISTIC_CONVERSATION)
    ]

    analysis = service._conversation_analysis(
        [msg for msg in messages if msg.actor == "child"]
    )

    assert "运动比赛/跑步" in analysis["topics"]
    assert "图片分享" in analysis["topics"]
    assert any("运动比赛" in item or "跑步" in item for item in analysis["expression_observations"])
    assert any("图片" in item for item in analysis["expression_observations"])
    summary_text = analysis["conversation_summary"][0]
    assert "运动比赛" in summary_text or "图片" in summary_text

    overview_topics = [item.topic for item in analysis["topic_overview"]]
    assert len(overview_topics) >= 2
    assert "运动比赛/跑步" in overview_topics
    assert "图片分享" in overview_topics

    assert any("追问" in item for item in analysis["avoid_followup"])
    assert any("图片" in item or "作业" in item for item in analysis["avoid_followup"])


def test_parent_report_realistic_conversation_payload_includes_short_content_hint() -> None:
    class CapturingModelRegistry(SuccessfulParentReportModelRegistry):
        payload: dict | None = None

        def generate(self, request):
            self.payload = _payload_from_request(request)
            return super().generate(request)

    model_registry = CapturingModelRegistry()
    service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_realistic_1",
                    text="我明天要参加比赛，有点紧张。",
                ),
                _conversation_message(
                    message_id="msg_realistic_2",
                    text="我拍了一张图给你看，这是我画的画。",
                    attachments_count=1,
                ),
                _conversation_message(
                    message_id="msg_realistic_3",
                    text="好，我要去英语打卡了，一会再聊。",
                ),
            ]
        ),
        model_registry=model_registry,
        now_provider=_fixed_now,
    )

    report = service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.generation_status == ParentReportGenerationStatus.MODEL_GENERATED
    snippets = model_registry.payload.get("conversation_snippets", [])
    assert len(snippets) >= 1
    for snippet in snippets:
        assert "short_content_hint" in snippet
        hint = snippet["short_content_hint"]
        assert isinstance(hint, str)
        assert len(hint) <= 40
        assert "逐字" not in hint

    report_json = report.model_dump_json()
    assert "接一句" not in report_json
    assert "桥接" not in report_json
