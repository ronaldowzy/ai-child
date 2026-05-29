from app.domain.scene import SceneAction, SceneId, SceneRouteDecision
from app.services.topic_seed_service import TopicSeedService


class QuickActionService:
    """Build child-facing quick actions.

    Hard scenes keep their scene actions. Open conversation gets lightweight,
    contextual suggestions instead of the old fixed after-school menu.
    """

    def __init__(self, *, topic_seed_service: TopicSeedService | None = None) -> None:
        self._topic_seed_service = topic_seed_service or TopicSeedService()

    def actions_for(
        self,
        *,
        decision: SceneRouteDecision,
        child_text: str,
        reply_text: str,
        parent_policy: object | None = None,
        conversation_control: dict[str, object] | None = None,
    ) -> list[SceneAction]:
        if decision.quick_actions:
            return decision.quick_actions
        if decision.active_scene != SceneId.OPEN_CONVERSATION:
            return []
        return self._open_conversation_actions(
            child_text=child_text,
            reply_text=reply_text,
            parent_policy=parent_policy,
            conversation_control=conversation_control,
        )

    def _open_conversation_actions(
        self,
        *,
        child_text: str,
        reply_text: str,
        parent_policy: object | None,
        conversation_control: dict[str, object] | None,
    ) -> list[SceneAction]:
        # Priority 1: stop control
        if self._is_stop_control(conversation_control):
            return self._control_actions(conversation_control)

        # Priority 2: model conversation_control suggested moves (if safe)
        control_actions = self._control_actions(conversation_control)
        if control_actions:
            return control_actions

        # Priority 3: show-and-tell action for image/object sharing
        if self._is_show_and_tell(child_text):
            return self._show_and_tell_actions(parent_policy, conversation_control)

        # Priority 4: profile-aware topic choices (when soft_shift or shift likely)
        if self._should_offer_topic_choices(conversation_control, reply_text):
            topic_actions = self._topic_choice_actions(
                parent_policy=parent_policy,
                conversation_control=conversation_control,
            )
            if topic_actions:
                return topic_actions

        # Priority 5: if profile has interests, always prefer topic choices
        if self._has_profile_interests(parent_policy):
            topic_actions = self._topic_choice_actions(
                parent_policy=parent_policy,
                conversation_control=conversation_control,
            )
            if topic_actions:
                return topic_actions

        # Priority 6: topic choices from seeds (no profile interests)
        topic_actions = self._topic_choice_actions(
            parent_policy=parent_policy,
            conversation_control=conversation_control,
        )
        if topic_actions:
            return topic_actions

        # Last resort: minimal stop/continue (only when nothing else works)
        return self._minimal_fallback_actions()

    def _is_stop_control(
        self,
        conversation_control: dict[str, object] | None,
    ) -> bool:
        return bool(
            conversation_control
            and conversation_control.get("topic_continuity") == "stop"
        )

    def _should_offer_topic_choices(
        self,
        conversation_control: dict[str, object] | None,
        reply_text: str,
    ) -> bool:
        if not conversation_control:
            return False
        if conversation_control.get("topic_continuity") == "stop":
            return False
        if conversation_control.get("topic_continuity") == "soft_shift":
            return True
        if conversation_control.get("topic_shift_intent") in {"likely", "explicit"}:
            return True
        return "换个轻松" in reply_text or "新话题" in reply_text

    def _topic_choice_actions(
        self,
        *,
        parent_policy: object | None,
        conversation_control: dict[str, object] | None,
    ) -> list[SceneAction]:
        labels = self._topic_seed_service.topic_choice_labels(
            parent_policy,
            recent_topic=str(conversation_control.get("recent_topic") or "")
            if conversation_control
            else None,
            limit=self._topic_choice_limit(parent_policy),
        )
        return [
            SceneAction(id=f"topic_choice_{index}", label=label)
            for index, label in enumerate(labels, start=1)
        ]

    def _is_show_and_tell(self, child_text: str) -> bool:
        normalized = child_text.lower().replace(" ", "")
        markers = ("给你看", "拍给你", "我画了", "我做了", "你看这个", "我的", "积木", "玩具")
        return any(marker in normalized for marker in markers)

    def _show_and_tell_actions(
        self,
        parent_policy: object | None,
        conversation_control: dict[str, object] | None,
    ) -> list[SceneAction]:
        actions = [SceneAction(id="share_photo", label="给小白狐看看")]
        # Add one profile-aware topic choice if available
        topic_actions = self._topic_choice_actions(
            parent_policy=parent_policy,
            conversation_control=conversation_control,
        )
        if topic_actions:
            actions.append(topic_actions[0])
        return actions[:2]

    def _has_profile_interests(self, parent_policy: object | None) -> bool:
        if parent_policy is None:
            return False
        if isinstance(parent_policy, dict):
            preferences = parent_policy.get("communication_preferences")
        else:
            preferences = getattr(parent_policy, "communication_preferences", None)
        if not isinstance(preferences, dict):
            return False
        interests = preferences.get("child_interests")
        return isinstance(interests, list) and len(interests) > 0

    def _minimal_fallback_actions(self) -> list[SceneAction]:
        return [
            SceneAction(id="continue", label="继续说"),
            SceneAction(id="stop", label="今天不聊了"),
        ]

    def _topic_choice_limit(self, parent_policy: object | None) -> int:
        if parent_policy is None:
            return 3
        if isinstance(parent_policy, dict):
            preferences = parent_policy.get("communication_preferences")
        else:
            preferences = getattr(parent_policy, "communication_preferences", None)
        if not isinstance(preferences, dict):
            return 3
        support_style = preferences.get("support_style_preferences")
        if isinstance(support_style, list) and "offer_two_choices" in support_style:
            return 2
        return 3

    def _control_actions(
        self,
        conversation_control: dict[str, object] | None,
    ) -> list[SceneAction]:
        if not conversation_control:
            return []
        raw_moves = conversation_control.get("suggested_next_moves")
        if not isinstance(raw_moves, list):
            return []
        actions: list[SceneAction] = []
        for index, item in enumerate(raw_moves[:3], start=1):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            action_id = str(item.get("id") or f"control_{index}").strip()
            if not label or self._unsafe_label(label):
                continue
            actions.append(SceneAction(id=action_id, label=label))
        return actions

    def _unsafe_label(self, label: str) -> bool:
        normalized = label.lower().replace(" ", "")
        return any(
            marker in normalized
            for marker in ("积分", "签到", "排行榜", "抽卡", "充值", "购买", "热搜")
        )


_quick_action_service = QuickActionService()


def get_quick_action_service() -> QuickActionService:
    return _quick_action_service
