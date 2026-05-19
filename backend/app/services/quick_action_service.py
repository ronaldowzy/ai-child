from app.domain.scene import SceneAction, SceneId, SceneRouteDecision


class QuickActionService:
    """Build child-facing quick actions.

    Hard scenes keep their scene actions. Open conversation gets lightweight,
    contextual suggestions instead of the old fixed after-school menu.
    """

    def actions_for(
        self,
        *,
        decision: SceneRouteDecision,
        child_text: str,
        reply_text: str,
    ) -> list[SceneAction]:
        if decision.quick_actions:
            return decision.quick_actions
        if decision.active_scene != SceneId.OPEN_CONVERSATION:
            return []
        return self._open_conversation_actions(child_text=child_text, reply_text=reply_text)

    def _open_conversation_actions(
        self,
        *,
        child_text: str,
        reply_text: str,
    ) -> list[SceneAction]:
        text = child_text.strip()
        normalized = text.lower().replace(" ", "")

        if "恐龙" in normalized:
            return [
                SceneAction(id="talk_tyrannosaurus", label="聊霸王龙"),
                SceneAction(id="talk_triceratops", label="聊三角龙"),
                SceneAction(id="dino_extinction", label="恐龙怎么灭绝"),
            ]
        if "开心" in normalized or "高兴" in normalized:
            return self._actions("说开心原因", "发生了什么", "换个小话题")
        if "画" in normalized:
            return self._actions("说画面", "加个角色", "换种颜色")
        if "游戏" in normalized:
            return self._actions("说玩法", "说角色", "休息一下")

        topic = self._topic_hint(text)
        if topic:
            compact_topic = topic[:4]
            return self._actions(
                f"{compact_topic}哪里有趣",
                f"为什么想到{compact_topic}",
                "换个话题",
            )

        if "为什么" in reply_text or "为什么" in text:
            return self._actions("说我的想法", "举个例子", "换个问法")
        return self._actions("接着说", "问个问题", "换个小话题")

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
