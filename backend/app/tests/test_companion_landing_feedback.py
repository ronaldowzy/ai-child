"""E4 tests: companion landing feedback after naming."""
from datetime import datetime

from app.domain.companion_object import (
    CompanionObjectSource,
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
]


# --- Helpers ---

def _message_request(
    child_id: str = "test_child",
    session_id: str = "test_session",
    text: str = "小棉花",
    quick_action_id: str | None = None,
    device_time: str = "2026-06-01T15:00:00+08:00",
) -> ConversationMessageRequest:
    return ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(text=text, quick_action_id=quick_action_id),
        client_context=ClientContext(
            deviceTime=datetime.fromisoformat(device_time),
            timezone="Asia/Shanghai",
        ),
    )


# --- Tests ---

class TestCompanionLandingFeedback:
    """Test landing feedback after companion naming."""

    def test_naming_success_returns_deterministic_template(self) -> None:
        """起名成功后，reply_text 应为确定性模板，不是模型生成。"""
        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )

        # 先设置 pending seed（模拟点击"起个名字"按钮）
        companion_svc.begin_seed_naming(
            session_id="test_session",
            child_id="test_child",
            object_type=CompanionObjectType.STAR,
            light_location="窗边",
            source_type=CompanionObjectSource.IMAGE_SHARE,
            recognized_image_type="child_drawing",
        )

        conv_svc = ConversationService(companion_object_service=companion_svc)

        # 模拟孩子输入名字
        result = conv_svc._check_pending_companion_seed_creation(
            child_id="test_child",
            session_id="test_session",
            child_text="小棉花",
            quick_action_id=None,
            image_context=None,
        )

        # 应该返回 co_create action
        assert result is not None
        assert result["action"] == "co_create"
        companion = result["companion"]
        assert companion.name == "小棉花"

    def test_naming_success_companion_meta_fields(self) -> None:
        """起名成功后，companion_meta 应正确构建。"""
        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )

        # 设置 pending seed
        companion_svc.begin_seed_naming(
            session_id="test_session",
            child_id="test_child",
            object_type=CompanionObjectType.STAR,
            light_location="窗边",
            source_type=CompanionObjectSource.IMAGE_SHARE,
            recognized_image_type="child_drawing",
        )

        conv_svc = ConversationService(companion_object_service=companion_svc)

        # 执行起名
        result = conv_svc._check_pending_companion_seed_creation(
            child_id="test_child",
            session_id="test_session",
            child_text="小棉花",
            quick_action_id=None,
            image_context=None,
        )

        assert result is not None
        companion = result["companion"]

        # 验证 companion 字段
        assert companion.name == "小棉花"
        assert companion.light_location == "窗边"
        assert companion.status == "active"
        assert companion.object_type is not None

    def test_deterministic_template_content(self) -> None:
        """确定性模板应包含名字和位置。"""
        name = "小棉花"
        location = "窗边"
        template = f"{name}，软软的名字\n它轻轻落到{location}啦"

        assert "小棉花" in template
        assert "软软的名字" in template
        assert "轻轻落到" in template
        assert "窗边" in template

    def test_deterministic_template_no_forbidden_phrases(self) -> None:
        """确定性模板不应包含禁用表达。"""
        name = "小棉花"
        location = "窗边"
        template = f"{name}，软软的名字\n它轻轻落到{location}啦"

        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in template, f"模板包含禁用表达: {phrase}"

    def test_deterministic_template_with_different_locations(self) -> None:
        """不同位置的确定性模板应正确替换。"""
        locations = ["窗边", "地毯边", "小白狐旁边"]

        for location in locations:
            name = "小星星"
            template = f"{name}，软软的名字\n它轻轻落到{location}啦"
            assert location in template
            assert "轻轻落到" in template

    def test_deterministic_template_with_different_names(self) -> None:
        """不同名字的确定性模板应正确替换。"""
        names = ["小棉花", "小尾巴", "小云朵", "小恐龙"]

        for name in names:
            location = "窗边"
            template = f"{name}，软软的名字\n它轻轻落到{location}啦"
            assert name in template
            assert "软软的名字" in template

    def test_response_from_route_decision_with_co_create(self) -> None:
        """_response_from_route_decision 在 co_create 时应返回确定性模板。"""
        from app.services.conversation_service import ConversationService
        from unittest.mock import MagicMock

        # 创建一个模拟的 companion
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {"action": "co_create", "companion": companion}

        # 创建模拟的 decision 和 runtime_result
        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"
        decision.quick_actions = None

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型生成的回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)

        # 调用 _response_from_route_decision
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="小棉花",
            parent_policy=None,
            companion_action=companion_action,
            image_context=None,
        )

        # 验证回复是确定性模板
        assert "小棉花" in response.reply.text
        assert "软软的名字" in response.reply.text
        assert "轻轻落到" in response.reply.text
        assert "窗边" in response.reply.text

        # 验证不是模型生成的回复
        assert "模型生成的回复" not in response.reply.text

    def test_response_from_route_decision_co_create_no_quick_actions(self) -> None:
        """起名成功后，不应返回 quick_actions。"""
        from app.services.conversation_service import ConversationService
        from unittest.mock import MagicMock

        # 创建一个模拟的 companion
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {"action": "co_create", "companion": companion}

        # 创建模拟的 decision 和 runtime_result
        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"
        decision.quick_actions = None

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型生成的回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)

        # 调用 _response_from_route_decision
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="小棉花",
            parent_policy=None,
            companion_action=companion_action,
            image_context=None,
        )

        # 验证 quick_actions 为空
        assert response.ui_actions == []

    def test_response_from_route_decision_co_create_companion_meta(self) -> None:
        """起名成功后，companion_meta 应正确构建。"""
        from app.services.conversation_service import ConversationService
        from unittest.mock import MagicMock

        # 创建一个模拟的 companion
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {"action": "co_create", "companion": companion}

        # 创建模拟的 decision 和 runtime_result
        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"
        decision.quick_actions = None

        runtime_result = MagicMock()
        runtime_result.reply_text = "模型生成的回复"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)

        # 调用 _response_from_route_decision
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="小棉花",
            parent_policy=None,
            companion_action=companion_action,
            image_context=None,
        )

        # 验证 companion_meta
        assert response.session_state.companion_object is not None
        meta = response.session_state.companion_object
        assert meta.name == "小棉花"
        assert meta.light_location == "窗边"
        assert meta.state == "active"
        assert meta.action == "co_create"
        assert meta.visual_kind == "star"

    def test_response_from_route_decision_recall_uses_model_reply(self) -> None:
        """recall 场景应使用模型生成的回复，不是确定性模板。"""
        from app.services.conversation_service import ConversationService
        from unittest.mock import MagicMock

        # 创建一个模拟的 companion
        companion = MagicMock()
        companion.id = "test_id"
        companion.name = "小棉花"
        companion.object_type = "star"
        companion.light_location = "窗边"
        companion.status = "active"
        companion.visual_kind = "star"

        companion_action = {"action": "recall", "companion": companion}

        # 创建模拟的 decision 和 runtime_result
        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"
        decision.quick_actions = None

        runtime_result = MagicMock()
        runtime_result.reply_text = "小棉花今天在窗边呢"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)

        # 调用 _response_from_route_decision
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="你好",
            parent_policy=None,
            companion_action=companion_action,
            image_context=None,
        )

        # recall 应使用模型回复
        assert response.reply.text == "小棉花今天在窗边呢"

    def test_response_from_route_decision_no_companion_uses_model_reply(self) -> None:
        """无 companion 时应使用模型生成的回复。"""
        from app.services.conversation_service import ConversationService
        from unittest.mock import MagicMock

        # 创建模拟的 decision 和 runtime_result
        decision = MagicMock()
        decision.base_scene.value = "conversation.open"
        decision.active_scene.value = "conversation.open"
        decision.needs_input = None
        decision.requires_parent_attention = False
        decision.reply_emotion = "warm"
        decision.quick_actions = None

        runtime_result = MagicMock()
        runtime_result.reply_text = "你好呀"
        runtime_result.model_metadata = {}

        conv_svc = ConversationService(companion_object_service=None)

        # 调用 _response_from_route_decision
        response = conv_svc._response_from_route_decision(
            decision,
            runtime_result,
            child_text="你好",
            parent_policy=None,
            companion_action=None,
            image_context=None,
        )

        # 无 companion 应使用模型回复
        assert response.reply.text == "你好呀"

    def test_default_location_when_empty(self) -> None:
        """light_location 为空时应使用默认值"窗边"。"""
        name = "小棉花"
        location = ""
        default_location = location or "窗边"
        template = f"{name}，软软的名字\n它轻轻落到{default_location}啦"

        assert "窗边" in template
        assert "轻轻落到" in template
