"""E5 tests: add-a-friend companion extension after recall."""
from datetime import datetime
from unittest.mock import MagicMock

from app.domain.companion_object import (
    CompanionObject,
    CompanionObjectSource,
    CompanionObjectStatus,
    CompanionObjectType,
)
from app.domain.schemas.conversation import (
    ConversationInput,
    ConversationMessageRequest,
    ClientContext,
)
from app.services.companion_object_service import (
    CompanionObjectService,
)
from app.services.conversation_service import ConversationService
from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository


# --- 禁用表达列表 ---
FORBIDDEN_PHRASES = [
    "保存成功",
    "已加入你的小屋",
    "任务完成",
    "明天一定要来看",
    "它会等你",
    "你获得了",
    "解锁了",
    "新朋友",
    "新客人",
    "收集成功",
    "收集",
    "朋友数量",
    "列表",
]


# --- Helpers ---

def _create_active_companion(
    svc: CompanionObjectService,
    *,
    child_id: str = "test_child",
    name: str = "小棉花",
    light_location: str = "窗边",
) -> CompanionObject:
    return svc.create(
        __import__("app.domain.companion_object", fromlist=["CompanionObjectCreateRequest"])
        .CompanionObjectCreateRequest(
            child_id=child_id,
            name=name,
            object_type=CompanionObjectType.STAR,
            source_type=CompanionObjectSource.FIRST_OPEN,
            safe_summary=f"这颗星星叫{name}",
            light_location=light_location,
        )
    )


def _message_request(
    child_id: str = "test_child",
    session_id: str = "test_session",
    text: str = "小棉花",
    quick_action_id: str | None = None,
) -> ConversationMessageRequest:
    return ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(text=text, quick_action_id=quick_action_id),
        client_context=ClientContext(
            deviceTime=datetime.fromisoformat("2026-06-01T15:00:00+08:00"),
            timezone="Asia/Shanghai",
        ),
    )


# --- Tests ---

class TestPendingCompanionExtension:
    """Test PendingCompanionExtension lifecycle."""

    def test_begin_and_get_extension(self) -> None:
        """begin_extension 后 get_pending_extension 应返回。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        svc.begin_extension(
            session_id="s1",
            child_id="c1",
            companion_id="comp1",
            companion_name="小棉花",
        )
        ext = svc.get_pending_extension(session_id="s1", child_id="c1")
        assert ext is not None
        assert ext.companion_id == "comp1"
        assert ext.companion_name == "小棉花"

    def test_get_extension_wrong_child(self) -> None:
        """不同 child_id 不应返回 extension。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        svc.begin_extension(
            session_id="s1",
            child_id="c1",
            companion_id="comp1",
            companion_name="小棉花",
        )
        assert svc.get_pending_extension(session_id="s1", child_id="c2") is None

    def test_clear_extension(self) -> None:
        """clear 后应返回 None。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        svc.begin_extension(
            session_id="s1",
            child_id="c1",
            companion_id="comp1",
            companion_name="小棉花",
        )
        svc.clear_pending_extension(session_id="s1")
        assert svc.get_pending_extension(session_id="s1", child_id="c1") is None


class TestUpdateSafeSummaryAppend:
    """Test update_safe_summary_append."""

    def test_append_to_existing_summary(self) -> None:
        """追加应保留原有摘要并附加新内容。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        updated = svc.update_safe_summary_append(
            companion.id,
            "孩子给小屋小客人加了一个小伙伴：小云朵",
        )
        assert updated is not None
        assert "这颗星星叫小棉花" in updated.safe_summary
        assert "孩子给小屋小客人加了一个小伙伴：小云朵" in updated.safe_summary
        assert "；" in updated.safe_summary

    def test_append_format(self) -> None:
        """追加格式应为 '原摘要；新内容'。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        updated = svc.update_safe_summary_append(
            companion.id,
            "孩子给小屋小客人加了一个小伙伴：小云朵",
        )
        assert updated is not None
        assert updated.safe_summary.startswith("这颗星星叫小棉花；")

    def test_append_truncation(self) -> None:
        """超过 200 字时应截断。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        long_text = "孩子给小屋小客人加了一个小伙伴：" + "很长的名字" * 50
        updated = svc.update_safe_summary_append(companion.id, long_text)
        assert updated is not None
        assert len(updated.safe_summary) <= 200

    def test_append_nonexistent_companion(self) -> None:
        """companion 不存在时应返回 None。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        result = svc.update_safe_summary_append("nonexistent", "test")
        assert result is None

    def test_append_preserves_companion_fields(self) -> None:
        """追加不应改变 companion 其他字段。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        updated = svc.update_safe_summary_append(
            companion.id,
            "孩子给小屋小客人加了一个小伙伴：小云朵",
        )
        assert updated is not None
        assert updated.name == "小棉花"
        assert updated.status == CompanionObjectStatus.ACTIVE
        assert updated.object_type == CompanionObjectType.STAR

    def test_append_does_not_create_second_active(self) -> None:
        """追加不应创建第二个 active companion。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.update_safe_summary_append(
            companion.id,
            "孩子给小屋小客人加了一个小伙伴：小云朵",
        )
        active = svc.get_active_by_child("test_child")
        assert active is not None
        assert active.id == companion.id
        assert active.name == "小棉花"


class TestCompanionContinueCreatesExtension:
    """Test that clicking '加一个朋友' creates pending extension."""

    def test_companion_continue_returns_guidance(self) -> None:
        """点击 companion_continue 应返回 co_create_guidance。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_active_companion(svc, name="小棉花")
        conv_svc = ConversationService(companion_object_service=svc)

        result = conv_svc._check_companion_action(
            child_id="test_child",
            session_id="test_session",
            child_text="",
            quick_action_id="companion_continue",
            scene_id=MagicMock(value="conversation.open"),
        )

        assert result is not None
        assert result["action"] == "co_create_guidance"
        assert result["companion"].name == "小棉花"

    def test_companion_continue_creates_pending_extension(self) -> None:
        """点击 companion_continue 应在 service 中建立 pending extension。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        conv_svc = ConversationService(companion_object_service=svc)

        conv_svc._check_companion_action(
            child_id="test_child",
            session_id="test_session",
            child_text="",
            quick_action_id="companion_continue",
            scene_id=MagicMock(value="conversation.open"),
        )

        ext = svc.get_pending_extension(session_id="test_session", child_id="test_child")
        assert ext is not None
        assert ext.companion_id == companion.id
        assert ext.companion_name == "小棉花"


class TestExtensionNameInput:
    """Test that saying a name during extension updates companion."""

    def test_child_says_name_updates_safe_summary(self) -> None:
        """孩子说名字后，safe_summary 应被追加。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="小云朵",
            quick_action_id=None,
        )

        assert result is not None
        assert result["action"] == "extension_done"
        assert result["friend_name"] == "小云朵"
        updated = result["companion"]
        assert "小云朵" in updated.safe_summary
        assert "孩子给小屋小客人加了一个小伙伴：小云朵" in updated.safe_summary

    def test_child_says_name_does_not_create_new_companion(self) -> None:
        """孩子说名字后，不应创建新 companion。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="小云朵",
            quick_action_id=None,
        )

        active = svc.get_active_by_child("test_child")
        assert active is not None
        assert active.id == companion.id
        assert active.name == "小棉花"

    def test_extension_clears_pending_after_completion(self) -> None:
        """完成后 pending extension 应被清除。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="小云朵",
            quick_action_id=None,
        )

        ext = svc.get_pending_extension(session_id="test_session", child_id="test_child")
        assert ext is None

    def test_extension_returns_companion_meta_active_co_create(self) -> None:
        """extension_done 应返回 companion_meta(state=active, action=co_create)。"""
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {
            "action": "extension_done",
            "companion": companion,
            "friend_name": "小云朵",
        }

        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="小云朵",
            parent_policy=None,
            companion_action=companion_action,
        )

        assert response.session_state.companion_object is not None
        meta = response.session_state.companion_object
        assert meta.state == "active"
        assert meta.action == "co_create"


class TestExtensionDeterministicFeedback:
    """Test deterministic feedback templates for extension."""

    def test_extension_done_returns_deterministic_template(self) -> None:
        """extension_done 应返回确定性反馈模板。"""
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {
            "action": "extension_done",
            "companion": companion,
            "friend_name": "小云朵",
        }

        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="小云朵",
            parent_policy=None,
            companion_action=companion_action,
        )

        assert "小云朵" in response.reply.text
        assert "也来小屋里待一会儿啦" in response.reply.text
        assert "模型回复" not in response.reply.text

    def test_extension_done_no_quick_actions(self) -> None:
        """extension_done 后不应返回 quick_actions。"""
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {
            "action": "extension_done",
            "companion": companion,
            "friend_name": "小云朵",
        }

        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="小云朵",
            parent_policy=None,
            companion_action=companion_action,
        )

        assert response.ui_actions == []

    def test_guidance_returns_deterministic_template(self) -> None:
        """co_create_guidance 应返回确定性引导话术。"""
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {
            "action": "co_create_guidance",
            "companion": companion,
        }

        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="",
            parent_policy=None,
            companion_action=companion_action,
        )

        assert "那我们给它找一个小伙伴" in response.reply.text
        assert "你可以说一个名字，也可以给我看看" in response.reply.text

    def test_guidance_returns_quick_actions(self) -> None:
        """co_create_guidance 应返回 [companion_friend_name, companion_friend_image, companion_skip]。"""
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {
            "action": "co_create_guidance",
            "companion": companion,
        }

        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="",
            parent_policy=None,
            companion_action=companion_action,
        )

        assert len(response.ui_actions) == 1
        actions = response.ui_actions[0].actions
        ids = [a.id for a in actions]
        labels = [a.label for a in actions]
        assert "companion_friend_name" in ids
        assert "companion_friend_image" in ids
        assert "companion_skip" in ids
        assert "说个名字" in labels
        assert "给小白狐看看" in labels
        assert "先聊别的" in labels


class TestExtensionNoForbiddenPhrases:
    """Test that extension templates don't contain forbidden phrases."""

    def test_guidance_no_forbidden_phrases(self) -> None:
        """引导话术不应包含禁用表达。"""
        text = "那我们给它找一个小伙伴\n你可以说一个名字，也可以给我看看"
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in text, f"引导话术包含禁用表达: {phrase}"

    def test_completion_no_forbidden_phrases(self) -> None:
        """完成话术不应包含禁用表达。"""
        names = ["小棉花", "小云朵", "小恐龙"]
        for name in names:
            text = f"{name}，也来小屋里待一会儿啦"
            for phrase in FORBIDDEN_PHRASES:
                assert phrase not in text, f"完成话术包含禁用表达: {phrase}"


class TestExtensionSkip:
    """Test skip during extension flow."""

    def test_quick_action_skip_clears_extension(self) -> None:
        """点击 companion_skip 应清除 extension。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="",
            quick_action_id="companion_skip",
        )

        assert result is not None
        assert result["action"] == "skip"
        ext = svc.get_pending_extension(session_id="test_session", child_id="test_child")
        assert ext is None

    def test_text_skip_signal_clears_extension(self) -> None:
        """孩子说'先聊别的'应清除 extension。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="先聊别的",
            quick_action_id=None,
        )

        assert result is not None
        assert result["action"] == "skip"

    def test_short_flat_reply_during_extension(self) -> None:
        """孩子说'不知道'应清除 extension（通过 _SKIP_SIGNALS）。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="不知道",
            quick_action_id=None,
        )

        assert result is not None
        assert result["action"] == "skip"


class TestExtensionImmediateNaming:
    """Test quick action + name in the same turn."""

    def test_quick_action_friend_name_with_name_text_completes_extension(self) -> None:
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="叫小云朵",
            quick_action_id="companion_friend_name",
        )

        assert result is not None
        assert result["action"] == "extension_done"
        assert result["friend_name"] == "小云朵"
        ext = svc.get_pending_extension(session_id="test_session", child_id="test_child")
        assert ext is None


class TestExtensionNoNameReturnsNone:
    """Test that non-name input during extension returns None."""

    def test_long_text_not_name_returns_none(self) -> None:
        """长文本不是名字，应返回 None。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="我想说一个很长很长的故事关于一个小恐龙",
            quick_action_id=None,
        )

        assert result is None

    def test_empty_text_returns_none(self) -> None:
        """空文本应返回 None。"""
        svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        companion = _create_active_companion(svc, name="小棉花")
        svc.begin_extension(
            session_id="test_session",
            child_id="test_child",
            companion_id=companion.id,
            companion_name="小棉花",
        )

        conv_svc = ConversationService(companion_object_service=svc)
        result = conv_svc._check_pending_companion_extension(
            child_id="test_child",
            session_id="test_session",
            child_text="",
            quick_action_id=None,
        )

        assert result is None
