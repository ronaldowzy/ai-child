"""D2 integration tests: companion object in conversation runtime."""
from datetime import datetime

from app.domain.companion_object import (
    CompanionObjectSource,
    CompanionObjectType,
)
from app.domain.schemas.conversation import (
    CompanionObjectMeta,
    ConversationInput,
    ConversationMessageRequest,
    ConversationOpeningRequest,
    ClientContext,
)
from app.services.companion_object_service import (
    CompanionObjectCreateRequest,
    CompanionObjectService,
)
from app.services.opening_service import OpeningService
from app.services.conversation_service import ConversationService


# --- Helpers ---

def _opening_request(
    child_id: str = "test_child",
    session_id: str = "test_session",
    device_time: str = "2026-05-30T15:00:00+08:00",
) -> ConversationOpeningRequest:
    return ConversationOpeningRequest(
        childId=child_id,
        sessionId=session_id,
        clientContext=ClientContext(
            deviceTime=datetime.fromisoformat(device_time),
            timezone="Asia/Shanghai",
        ),
    )


def _message_request(
    child_id: str = "test_child",
    session_id: str = "test_session",
    text: str = "你好",
    device_time: str = "2026-05-30T15:00:00+08:00",
) -> ConversationMessageRequest:
    return ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(text=text),
        client_context=ClientContext(
            deviceTime=datetime.fromisoformat(device_time),
            timezone="Asia/Shanghai",
        ),
    )


def _create_companion(
    service: CompanionObjectService,
    child_id: str = "test_child",
    name: str = "小棉花",
    object_type: CompanionObjectType = CompanionObjectType.STAR,
    source_type: CompanionObjectSource = CompanionObjectSource.FIRST_OPEN,
    light_location: str = "窗边",
) -> object:
    return service.create(
        CompanionObjectCreateRequest(
            child_id=child_id,
            name=name,
            object_type=object_type,
            source_type=source_type,
            safe_summary=f"孩子起名了{object_type.value}叫{name}",
            light_location=light_location,
        )
    )


# --- Opening tests ---

class TestOpeningCompanionRecall:
    """Test companion recall at opening."""

    def test_opening_first_time_no_companion(self) -> None:
        """First opening with no companion: low-pressure greeting."""
        svc = OpeningService(companion_object_service=None)
        response = svc.create_opening(_opening_request())
        assert response.reply.text
        assert response.session_state.companion_object is None
        # Default quick action, not companion actions
        action_ids = [
            a.id for ua in response.ui_actions for a in ua.actions
        ]
        assert "start_voice" in action_ids

    def test_opening_with_active_companion_recall(self) -> None:
        """Opening with active companion: recall mode with companion metadata."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        # Should have companion recall
        assert response.session_state.companion_object is not None
        meta = response.session_state.companion_object
        assert meta.name == "小棉花"
        assert meta.light_location == "窗边"
        assert meta.action == "recall"
        assert meta.state == "active"

        # Should have companion actions
        action_ids = [
            a.id for ua in response.ui_actions for a in ua.actions
        ]
        assert "companion_continue" in action_ids
        assert "companion_skip" in action_ids

        # Reply should mention the companion
        assert "小棉花" in response.reply.text
        assert "窗边" in response.reply.text

    def test_opening_bedtime_no_recall(self) -> None:
        """Bedtime opening: never recall companion."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(
            _opening_request(device_time="2026-05-30T21:00:00+08:00")
        )

        # Should NOT have companion recall at bedtime
        assert response.session_state.companion_object is None

    def test_opening_paused_companion_no_recall(self) -> None:
        """Paused companion: no active recall."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)
        # Simulate skip twice -> PAUSED
        active = companion_svc.get_active_by_child("test_child")
        companion_svc.mark_skipped(active.id, session_id="s1")
        active2 = companion_svc.get_active_by_child("test_child")
        if active2:
            companion_svc.mark_skipped(active2.id, session_id="s2")

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        # PAUSED companion should not be recalled
        assert response.session_state.companion_object is None


class TestCompanionSessionState:
    """Test SessionState companion_object field."""

    def test_companion_meta_in_session_state(self) -> None:
        """SessionState contains minimal companion metadata."""
        meta = CompanionObjectMeta(
            id="abc123",
            name="小棉花",
            object_type="star",
            light_location="窗边",
            state="active",
            action="recall",
        )
        assert meta.id == "abc123"
        assert meta.name == "小棉花"
        assert meta.object_type == "star"
        assert meta.light_location == "窗边"
        assert meta.state == "active"
        assert meta.action == "recall"

    def test_companion_meta_no_sensitive_fields(self) -> None:
        """CompanionObjectMeta should not have sensitive fields."""
        meta = CompanionObjectMeta(
            id="abc123",
            name="小棉花",
            object_type="star",
            light_location="窗边",
            state="active",
            action="recall",
        )
        # Should not have safe_summary, recall_count, skip_count
        assert not hasattr(meta, "safe_summary")
        assert not hasattr(meta, "recall_count")
        assert not hasattr(meta, "skip_count")
        assert not hasattr(meta, "history")


class TestConversationCompanionSkip:
    """Test companion skip detection in conversation."""

    def test_skip_signal_marks_skipped(self) -> None:
        """Skip signals like '先聊别的' mark companion as skipped."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository
        from app.domain.scene import SceneId

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        conv_svc = ConversationService(companion_object_service=companion_svc)
        result = conv_svc._check_companion_action(
            child_id="test_child",
            session_id="test_session",
            child_text="先聊别的",
            scene_id=SceneId.OPEN_CONVERSATION,
        )

        assert result is not None
        assert result["action"] == "skip"
        # Companion should be skipped
        updated = companion_svc.get_active_by_child("test_child")
        assert updated is None or updated.skip_count > 0

    def test_learning_scene_no_companion_action(self) -> None:
        """Learning scene: no companion action processing."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository
        from app.domain.scene import SceneId

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        conv_svc = ConversationService(companion_object_service=companion_svc)
        result = conv_svc._check_companion_action(
            child_id="test_child",
            session_id="test_session",
            child_text="先聊别的",
            scene_id=SceneId.LEARNING_HOMEWORK_HELP,
        )

        # Should NOT process companion action in learning scene
        assert result is None

    def test_safety_scene_no_companion_action(self) -> None:
        """Safety scene: no companion action processing."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository
        from app.domain.scene import SceneId

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        conv_svc = ConversationService(companion_object_service=companion_svc)
        result = conv_svc._check_companion_action(
            child_id="test_child",
            session_id="test_session",
            child_text="先聊别的",
            scene_id=SceneId.SAFETY_GUARDIAN,
        )

        assert result is None

    def test_privacy_scene_no_companion_action(self) -> None:
        """Privacy scene: no companion action processing."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository
        from app.domain.scene import SceneId

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        conv_svc = ConversationService(companion_object_service=companion_svc)
        result = conv_svc._check_companion_action(
            child_id="test_child",
            session_id="test_session",
            child_text="先聊别的",
            scene_id=SceneId.PRIVACY_BOUNDARY,
        )

        assert result is None


class TestForbiddenPhrases:
    """Test that forbidden phrases don't appear in companion recall."""

    def test_no_dependency_phrases_in_recall(self) -> None:
        """Recall output should not contain dependency phrases."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        text = response.reply.text
        forbidden = [
            "我一直在等你", "你终于来了", "小白狐想你了",
            "明天一定要来", "你不来小白狐会想你",
            "连续来了", "打卡", "奖励", "任务完成",
        ]
        for phrase in forbidden:
            assert phrase not in text, f"Forbidden phrase '{phrase}' found in: {text}"


class TestStarNamingSeed:
    """Test first-open star naming seed."""

    def test_first_open_returns_star_seed(self) -> None:
        """First open with no companion history: star naming seed."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        # Should have star seed
        assert response.session_state.companion_object is not None
        meta = response.session_state.companion_object
        assert meta.state == "seed"
        assert meta.action == "name_seed"
        assert meta.name == "小星星"
        assert meta.light_location == "窗边"

        # Should have star seed text
        assert "小星星" in response.reply.text
        assert "名字" in response.reply.text

        # Should have naming action
        action_ids = [a.id for ua in response.ui_actions for a in ua.actions]
        assert "companion_name" in action_ids

    def test_bedtime_no_star_seed(self) -> None:
        """Bedtime: no star naming seed."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(
            _opening_request(device_time="2026-05-30T21:00:00+08:00")
        )

        # Should NOT have star seed at bedtime
        assert response.session_state.companion_object is None

    def test_existing_companion_no_star_seed(self) -> None:
        """Existing companion: no star seed (should recall instead)."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc)

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        # Should have recall, not star seed
        assert response.session_state.companion_object is not None
        assert response.session_state.companion_object.state == "active"
        assert response.session_state.companion_object.action == "recall"

    def test_default_opening_button_is_start_voice(self) -> None:
        """Default opening button should be '按一下开始说'."""
        opening_svc = OpeningService(companion_object_service=None)
        response = opening_svc.create_opening(_opening_request())

        action_labels = [a.label for ua in response.ui_actions for a in ua.actions]
        assert "按一下开始说" in action_labels
        assert "我想说话" not in action_labels

    def test_recall_text_no_forbidden_phrases(self) -> None:
        """Recall text should not contain forbidden phrases."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc, name="小棉花", light_location="窗边")

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        text = response.reply.text
        forbidden = [
            "我一直在等你", "你终于来了", "小白狐想你了",
            "明天一定要来", "你不来小白狐会想你",
        ]
        for phrase in forbidden:
            assert phrase not in text, f"Forbidden phrase '{phrase}' found in: {text}"

    def test_recall_text_matches_master_copy(self) -> None:
        """Recall text should match master-copy format."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        _create_companion(companion_svc, name="小棉花", light_location="窗边")

        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        text = response.reply.text
        # Should match master-copy: "{name}今天在{location}呢\n要不要给它加一个朋友？"
        assert "小棉花今天在窗边呢" in text
        assert "要不要给它加一个朋友？" in text

    def test_star_seed_text_matches_master_copy(self) -> None:
        """Star seed text should match master-copy."""
        from app.services.companion_object_service import CompanionObjectService
        from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository

        companion_svc = CompanionObjectService(
            repository=InMemoryCompanionObjectRepository(),
        )
        opening_svc = OpeningService(companion_object_service=companion_svc)
        response = opening_svc.create_opening(_opening_request())

        text = response.reply.text
        # Should match master-copy: "窗边这颗小星星还没有名字\n要不要给它起一个？"
        assert "窗边这颗小星星还没有名字" in text
        assert "要不要给它起一个？" in text
