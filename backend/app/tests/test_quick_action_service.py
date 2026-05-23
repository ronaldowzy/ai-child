from app.domain.enums import IntentType, RiskLevel
from app.domain.scene import SceneId, SceneRouteDecision, SceneTransitionType
from app.services.quick_action_service import QuickActionService


def test_open_conversation_quick_actions_follow_child_topic() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="恐龙很有意思。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="我想聊恐龙",
        reply_text="恐龙很有意思。",
    )

    assert [action.id for action in actions] == [
        "talk_tyrannosaurus",
        "talk_triceratops",
        "dino_extinction",
    ]


def test_non_open_conversation_keeps_scene_actions() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_learning_session",
        primary_intent=IntentType.LEARNING_HELP,
        base_scene=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        active_scene=SceneId.LEARNING_HOMEWORK_HELP,
        transition=SceneTransitionType.PUSH,
        scene_stack=[SceneId.LEARNING_HOMEWORK_HELP],
        risk_level=RiskLevel.NONE,
        confidence=0.9,
        reason="learning_help",
        needs_input="problem_content",
        reply_text="我们先看题意。",
        quick_actions=[],
    )

    assert service.actions_for(
        decision=decision,
        child_text="我有一道题不会",
        reply_text="我们先看题意。",
    ) == []


def test_open_conversation_quick_actions_offer_child_agency() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_agency_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="你可以接着说，也可以换个轻松话题。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="我今天想说跑步比赛",
        reply_text="你可以接着说，也可以换个轻松话题。",
    )

    assert [action.label for action in actions] == [
        "继续说",
        "换个话题",
        "今天不聊了",
    ]


def test_open_conversation_quick_actions_can_offer_story_without_gamification() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_story_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="我们可以轻轻编个故事。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="我想编个故事",
        reply_text="我们可以轻轻编个故事。",
    )

    assert [action.label for action in actions] == [
        "继续说",
        "讲个小故事",
        "今天不聊了",
    ]
    assert all("积分" not in action.label and "签到" not in action.label for action in actions)
