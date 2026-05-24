from datetime import date, datetime, timezone

from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.services.parent_report_service import ParentReportService


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
            _message(0, "我想聊 CS 的地图。"),
            _message(1, "队友配合还行。"),
            _message(2, "嗯，随便。"),
        ]
    )

    assert "游戏/CS" in analysis["topics"]
    assert any(item.topic == "游戏/CS" for item in analysis["topic_overview"])
    assert "游戏/CS" in analysis["conversation_summary"][0]
    assert any("时长盘问" in item for item in analysis["avoid_followup"])
