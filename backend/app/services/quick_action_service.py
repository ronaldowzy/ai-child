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
        control_actions = self._control_actions(conversation_control)
        if self._should_offer_topic_choices(conversation_control, reply_text):
            topic_actions = self._topic_choice_actions(
                parent_policy=parent_policy,
                conversation_control=conversation_control,
            )
            if topic_actions:
                return topic_actions
        if control_actions:
            return control_actions

        text = child_text.strip()
        normalized = text.lower().replace(" ", "")

        if "恐龙" in normalized:
            return self._topic_choice_actions(
                parent_policy=parent_policy,
                conversation_control=conversation_control,
            ) or self._actions("聊恐龙", "换个轻松话题", "今天不聊了")
        if "开心" in normalized or "高兴" in normalized:
            return self._actions("继续说", "换个话题", "今天不聊了")
        if "画" in normalized:
            return [
                SceneAction(id="share_photo", label="拍给小白狐看"),
                *self._actions("继续说", "讲个小故事")[:2],
            ]
        if any(marker in normalized for marker in ("给你看", "拍", "积木", "玩具")):
            return [
                SceneAction(id="share_photo", label="拍给小白狐看"),
                *self._actions("聊聊它", "编个故事")[:2],
            ]
        if "游戏" in normalized:
            return self._actions("继续说", "换个话题", "今天不聊了")
        if any(marker in normalized for marker in ("故事", "想象", "编一个", "编个")):
            return self._actions("继续说", "讲个小故事", "今天不聊了")

        topic = self._topic_hint(text)
        if topic:
            return self._actions(
                "继续说",
                "换个话题",
                "今天不聊了",
            )

        if "为什么" in reply_text or "为什么" in text:
            return self._actions("继续说", "换个说法", "今天不聊了")
        return self._topic_choice_actions(
            parent_policy=parent_policy,
            conversation_control=conversation_control,
        ) or self._actions("继续说", "讲个小故事", "今天不聊了")

    def _should_offer_topic_choices(
        self,
        conversation_control: dict[str, object] | None,
        reply_text: str,
    ) -> bool:
        if not conversation_control:
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
            limit=3,
        )
        return [
            SceneAction(id=f"topic_choice_{index}", label=label)
            for index, label in enumerate(labels, start=1)
        ]

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

    def _topic_hint(self, text: str) -> str:
        prefixes = ("我想聊", "我喜欢", "我今天看到", "我在想", "我想说")
        for prefix in prefixes:
            if text.startswith(prefix) and len(text) > len(prefix):
                return text[len(prefix) :].strip("，。！？ ")
        if len(text) <= 12 and not any(marker in text for marker in ("吗", "？", "?")):
            return text.strip("，。！？ ")
        return ""

    def _actions(self, *labels: str) -> list[SceneAction]:
        return [
            SceneAction(id=f"dynamic_{index}", label=label)
            for index, label in enumerate(labels[:3], start=1)
        ]


_quick_action_service = QuickActionService()


def get_quick_action_service() -> QuickActionService:
    return _quick_action_service
