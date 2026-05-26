from app.domain.enums import IntentType, RiskLevel
from app.domain.scene import SceneId, SceneRouteDecision, SceneTransitionType
from app.services.quick_action_service import QuickActionService


def _decision(
    *,
    session_id: str = "quick_action_session",
    reply_text: str = "恐龙很有意思。",
    quick_actions: list | None = None,
) -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id=session_id,
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.8,
        reason="open_conversation",
        needs_input=None,
        reply_text=reply_text,
        quick_actions=quick_actions or [],
    )


def test_open_conversation_quick_actions_follow_child_topic() -> None:
    service = QuickActionService()
    decision = _decision()

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
    decision = _decision(reply_text="你可以接着说，也可以换个轻松话题。")

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


def test_open_conversation_topic_choices_filter_boundaries() -> None:
    service = QuickActionService()
    decision = _decision(reply_text="我们可以换个轻松话题。")

    actions = service.actions_for(
        decision=decision,
        child_text="嗯",
        reply_text="我们可以换个轻松话题。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画", "跑步"],
                "topic_boundaries": ["不要聊跑步"],
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


def test_model_control_actions_take_priority() -> None:
    """Model conversation_control suggested moves should take priority."""
    service = QuickActionService()
    decision = _decision(reply_text="我们可以换个轻松话题。")

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

    # Model control actions take priority over profile choices
    assert [action.label for action in actions] == ["继续聊游戏"]


def test_stop_control_does_not_offer_topic_choice_fallbacks() -> None:
    service = QuickActionService()
    decision = _decision(reply_text="好，我们先停一下。想休息也可以。")

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
    decision = _decision(reply_text="我们可以换个轻松话题。")

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
    decision = _decision(reply_text="我们可以换个轻松话题。")

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


# --- Quick action v2 tests ---


def test_show_and_tell_creates_share_photo_action() -> None:
    """Show-and-tell text should produce share_photo action."""
    service = QuickActionService()
    decision = _decision(reply_text="让我看看！")

    actions = service.actions_for(
        decision=decision,
        child_text="你看这个，我画的小狐狸。",
        reply_text="让我看看！",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["画画", "跑步"],
            }
        },
    )

    labels = [action.label for action in actions]
    assert "拍给小白狐看" in labels, f"Should have share_photo: {labels}"


def test_profile_interests_priority_over_keyword_fallback() -> None:
    """When profile has interests, topic choices should appear, not fixed menus."""
    service = QuickActionService()
    decision = _decision(reply_text="恐龙很有意思。")

    actions = service.actions_for(
        decision=decision,
        child_text="我想聊恐龙",
        reply_text="恐龙很有意思。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画"],
            }
        },
    )

    labels = [action.label for action in actions]
    # Should have profile-aware topic choices
    assert "聊恐龙" in labels or "聊画画" in labels, (
        f"Should have profile-aware labels: {labels}"
    )
    # Should NOT have old fixed menu
    assert "讲个小故事" not in labels, f"Should not have old fixed menu: {labels}"


def test_no_old_fixed_menu_when_profile_interests_exist() -> None:
    """Old fixed menu should not appear when profile interests exist."""
    service = QuickActionService()
    decision = _decision(reply_text="有意思。")

    actions = service.actions_for(
        decision=decision,
        child_text="我今天看到一个好玩的",
        reply_text="有意思。",
        parent_policy={
            "communication_preferences": {
                "child_interests": ["恐龙", "画画"],
            }
        },
    )

    labels = [action.label for action in actions]
    assert "讲个小故事" not in labels, f"Should not have old fixed menu: {labels}"
    assert "换个话题" not in labels, f"Should not have old fixed menu: {labels}"


def test_seed_topics_without_profile() -> None:
    """Without profile, seed topics should be used."""
    service = QuickActionService()
    decision = _decision(reply_text="好的。")

    actions = service.actions_for(
        decision=decision,
        child_text="嗯",
        reply_text="好的。",
    )

    labels = [action.label for action in actions]
    # Should return seed topics (from topic_seed_packs_v0_1.json)
    assert len(actions) >= 1, f"Should have at least 1 action: {labels}"
    assert all("积分" not in lbl and "排行榜" not in lbl for lbl in labels), (
        f"Should not have unsafe labels: {labels}"
    )
