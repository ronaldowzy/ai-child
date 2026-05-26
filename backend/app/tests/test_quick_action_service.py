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
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
            }
        },
    )

    assert [action.label for action in actions] == [
        "聊恐龙",
        "聊画画",
        "聊跑步",
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
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
            }
        },
        conversation_control={
            "topic_continuity": "soft_shift",
            "topic_shift_intent": "likely",
        },
    )

    assert [action.label for action in actions] == [
        "聊恐龙",
        "聊画画",
        "聊跑步",
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


def test_open_conversation_topic_choices_filter_boundaries() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_boundary_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="我们可以换个轻松话题。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="嗯",
        reply_text="我们可以换个轻松话题。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
                "topic_boundaries": ["跑步"],
            }
        },
        conversation_control={
            "topic_continuity": "soft_shift",
            "topic_shift_intent": "likely",
        },
    )

    labels = [action.label for action in actions]
    assert labels[:2] == ["聊恐龙", "聊画画"]
    assert all("跑步" not in label for label in labels)


def test_model_soft_shift_profile_choices_override_old_keyword_fallbacks() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_soft_shift_keyword_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="我们可以换个轻松话题。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="CS 游戏为什么又输了",
        reply_text="我们可以换个轻松话题。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
            }
        },
        conversation_control={
            "topic_continuity": "soft_shift",
            "topic_shift_intent": "likely",
            "suggested_next_moves": [
                {"id": "continue_game", "label": "继续聊游戏"}
            ],
        },
    )

    assert [action.label for action in actions] == [
        "聊恐龙",
        "聊画画",
        "聊跑步",
    ]


def test_stop_control_does_not_offer_topic_choice_fallbacks() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_stop_control_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="好，我们先停一下。想休息也可以。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="不聊了。",
        reply_text="好，我们先停一下。想休息也可以。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
            }
        },
        conversation_control={
            "topic_continuity": "stop",
            "topic_shift_intent": "explicit",
            "suggested_next_moves": [],
        },
    )

    assert actions == []


def test_open_conversation_topic_choices_use_curated_seeds_without_interests() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_seed_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="我们可以换个轻松话题。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="嗯",
        reply_text="我们可以换个轻松话题。",
        parent_policy={"communication_preferences": {"child_age": 8}},
        conversation_control={
            "topic_continuity": "soft_shift",
            "topic_shift_intent": "likely",
        },
    )

    assert len(actions) >= 1
    assert all("热搜" not in action.label and "排行榜" not in action.label for action in actions)


def test_open_conversation_topic_choices_offer_two_choices_limits_to_two() -> None:
    service = QuickActionService()
    decision = SceneRouteDecision(
        session_id="quick_action_offer_two_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text="我们可以换个轻松话题。",
        quick_actions=[],
    )

    actions = service.actions_for(
        decision=decision,
        child_text="嗯",
        reply_text="我们可以换个轻松话题。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
                "support_style_preferences": ["offer_two_choices"],
            }
        },
        conversation_control={
            "topic_continuity": "soft_shift",
            "topic_shift_intent": "likely",
        },
    )

    assert len(actions) == 2
    assert [action.label for action in actions] == ["聊恐龙", "聊画画"]
