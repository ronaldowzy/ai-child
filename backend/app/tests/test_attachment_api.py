from fastapi.testclient import TestClient

from app.api.v1 import conversation_attachment as attachment_api
from app.core.config import Settings
from app.domain.attachment import (
    AttachmentCreateRequest,
    AttachmentType,
    ImagePurpose,
    RecognizedContent,
)
from app.domain.model_types import ModelRequest, ModelResponse
from app.main import app
from app.repositories.attachment_repository import (
    InMemoryAttachmentRepository,
    get_attachment_repository,
)
from app.services.attachment_service import AttachmentService
from app.services.conversation_history_service import ConversationHistoryService
from app.services.modality_manager import ModalityManager


client = TestClient(app)


def setup_function() -> None:
    get_attachment_repository().clear()
    attachment_api.attachment_service = AttachmentService()


class CapturingVisionRegistry:
    def __init__(
        self,
        *,
        provider_name: str = "mimo",
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.request: ModelRequest | None = None
        self.provider_name = provider_name
        self.metadata = metadata or {}

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.request = request
        return ModelResponse(
            task_type=request.task_type,
            response_text=(
                '{"child_summary":"我看到一张测试图片。",'
                '"context_summary":"图片里有一张非儿童测试图，适合聊看到的形状和颜色。",'
                '"recognized_type":"image_observation"}'
            ),
            structured_output={},
            provider_name=self.provider_name,
            model_name="mimo-v2.5",
            metadata=self.metadata,
        )


def test_conversation_attachment_accepts_high_confidence_homework_photo() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_high_session",
            "attachment_type": "image",
            "image_purpose": "learning_homework",
            "file_id": "mock_homework_photo",
            "mock_ocr_text": "小明有24个苹果，平均分给6个同学，每人几个？",
            "mock_vision_text": "小明有24个苹果，平均分给6个同学，每人几个？",
            "mock_confidence": 0.93,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["attachment_id"].startswith("att_")
    assert body["recognized_content"]["type"] == "homework_problem"
    assert body["recognized_content"]["text"] == (
        "小明有24个苹果，平均分给6个同学，每人几个？"
    )
    assert body["recognized_content"]["confidence"] == 0.93
    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert body["session_state"]["needs_input"] == "problem_statement_confirm"
    assert "对一下题目" in body["reply"]["text"]
    assert "答案是" not in body["reply"]["text"]


def test_generic_image_attachment_records_short_term_history() -> None:
    history = ConversationHistoryService()
    service = AttachmentService(
        repository=InMemoryAttachmentRepository(),
        conversation_history_service=history,
    )

    response = service.create_attachment(
        AttachmentCreateRequest(
            child_id="child_attachment_history_test",
            session_id="attachment_history_session",
            attachment_type=AttachmentType.IMAGE,
            image_purpose=ImagePurpose.SHARE,
            file_id="mock_share_photo",
            mock_ocr_text="这是一只小猫玩偶。",
            child_caption="我给小白狐看了一张图",
            mock_confidence=0.92,
        )
    )

    messages = history.get_recent_model_messages(
        session_id="attachment_history_session",
        limit=6,
    )

    assert response.recognized_content.type == "image_observation"
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content == "我给小白狐看了一张图"
    assert messages[1].content == response.reply.text


def test_homework_attachment_does_not_pre_record_history_before_followup() -> None:
    history = ConversationHistoryService()
    service = AttachmentService(
        repository=InMemoryAttachmentRepository(),
        conversation_history_service=history,
    )

    response = service.create_attachment(
        AttachmentCreateRequest(
            child_id="child_attachment_homework_history_test",
            session_id="attachment_homework_history_session",
            attachment_type=AttachmentType.IMAGE,
            image_purpose=ImagePurpose.LEARNING_HOMEWORK,
            file_id="mock_homework_photo",
            mock_ocr_text="小明有24个苹果，平均分给6个同学，每人几个？",
            child_caption="这是题目",
            mock_confidence=0.93,
        )
    )

    messages = history.get_recent_model_messages(
        session_id="attachment_homework_history_session",
        limit=6,
    )

    assert response.recognized_content.type == "homework_problem"
    assert messages == []


def test_image_upload_endpoint_accepts_real_multipart_and_uses_mimo_vision(
    monkeypatch,
) -> None:
    registry = CapturingVisionRegistry(provider_name="mimo")
    repository = InMemoryAttachmentRepository()
    monkeypatch.setattr(
        attachment_api,
        "attachment_service",
        AttachmentService(
            repository=repository,
            model_registry=registry,
            settings=Settings(model_provider="mimo", vision_provider="mimo"),
        ),
    )

    response = client.post(
        "/api/v1/attachments/images",
        data={
            "child_id": "child_real_image_upload_test",
            "session_id": "real_image_upload_session",
            "image_purpose": "share",
            "child_caption": "我拍了一张图片给小白狐看。",
        },
        files={"file": ("sample.jpg", b"not-a-real-child-photo", "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    attachment = repository.get(body["attachment_id"])

    assert body["attachment_id"].startswith("att_")
    assert body["mime_type"] == "image/jpeg"
    assert body["size_bytes"] == len(b"not-a-real-child-photo")
    assert body["recognized_content"]["provider_name"] == "mimo"
    assert body["recognized_content"]["text"].startswith("图片里有一张非儿童测试图")
    assert registry.request is not None
    assert registry.request.metadata["contains_image"] is True
    assert registry.request.metadata["contains_child_data"] is True
    assert registry.request.metadata["image_data_uri"].startswith("data:image/jpeg;base64,")
    assert attachment is not None
    assert attachment.metadata["source"] == "real_image_upload"
    assert attachment.metadata["image_data_uri_stored"] is False
    assert "data:image" not in str(attachment.metadata)


def test_image_upload_rejects_unsupported_mime(monkeypatch) -> None:
    monkeypatch.setattr(
        attachment_api,
        "attachment_service",
        AttachmentService(
            repository=InMemoryAttachmentRepository(),
            model_registry=CapturingVisionRegistry(),
            settings=Settings(model_provider="mimo", vision_provider="mimo"),
        ),
    )

    response = client.post(
        "/api/v1/attachments/images",
        data={
            "child_id": "child_real_image_upload_test",
            "session_id": "real_image_upload_session",
        },
        files={"file": ("sample.txt", b"text", "text/plain")},
    )

    assert response.status_code == 415


def test_image_upload_does_not_mark_mock_vision_as_real_success(monkeypatch) -> None:
    monkeypatch.setattr(
        attachment_api,
        "attachment_service",
        AttachmentService(
            repository=InMemoryAttachmentRepository(),
            model_registry=CapturingVisionRegistry(
                provider_name="mock",
                metadata={"fallback_used": True},
            ),
            settings=Settings(model_provider="mimo", vision_provider="mimo"),
        ),
    )

    response = client.post(
        "/api/v1/attachments/images",
        data={
            "child_id": "child_real_image_upload_test",
            "session_id": "real_image_upload_session",
        },
        files={"file": ("sample.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "vision_provider_unavailable"


def test_image_upload_returns_policy_blocked_when_vision_policy_blocks(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        attachment_api,
        "attachment_service",
        AttachmentService(
            repository=InMemoryAttachmentRepository(),
            model_registry=CapturingVisionRegistry(
                provider_name="mimo",
                metadata={"policy_blocked": True},
            ),
            settings=Settings(model_provider="mimo", vision_provider="mimo"),
        ),
    )

    response = client.post(
        "/api/v1/attachments/images",
        data={
            "child_id": "child_real_image_upload_test",
            "session_id": "real_image_upload_session",
        },
        files={"file": ("sample.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "vision_policy_blocked"


def test_conversation_attachment_low_confidence_requests_retry_or_speech() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_low_session",
            "attachment_type": "homework_photo",
            "file_id": "bad_photo_homework",
            "mock_confidence": 0.31,
        },
    )

    assert response.status_code == 200
    body = response.json()
    action_ids = {
        action["id"]
        for action_group in body["ui_actions"]
        for action in action_group["actions"]
    }

    assert "text" not in body["recognized_content"]
    assert body["recognized_content"]["confidence"] == 0.31
    assert body["recognized_content"]["fallback_action"] == "retake_or_speak_problem"
    assert body["session_state"]["needs_input"] == "problem_content"
    assert action_ids == {"take_photo", "speak_problem"}
    assert "没看清楚" in body["reply"]["text"]


def test_conversation_attachment_accepts_generic_image_share() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_share_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_toy_photo",
            "mock_vision_text": "孩子搭了一个积木城堡",
            "child_caption": "你看我搭的这个",
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["image_purpose"] == "share"
    assert body["session_state"]["active_scene"] == "conversation.open"
    # E3: 确定性模板回复
    assert "起个名字" in body["reply"]["text"]
    assert "我看到" in body["reply"]["text"]
    assert body["reply"]["emotion"] == "encourage"
    assert "这道题" not in body["reply"]["text"]
    # E3: 只有一个 quick action: companion_name
    action_ids = {
        action["id"]
        for action_group in body["ui_actions"]
        for action in action_group["actions"]
    }
    assert "companion_name" in action_ids
    assert "tell_story" not in action_ids
    assert "say_what_happened" not in action_ids


def test_generic_image_low_confidence_does_not_pretend_to_see_detail() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_low_image_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_unclear_toy_photo",
            "mock_vision_text": "一个积木城堡",
            "child_caption": "你看我搭的这个",
            "mock_confidence": 0.41,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "conversation.open"
    # E3: 低置信度使用 master-copy 失败文案
    assert "这张图还没看到" in body["reply"]["text"]
    assert "积木城堡" not in body["reply"]["text"]
    # E3: 低置信度返回"再试一次"和"先不看"
    action_ids = {
        action["id"]
        for action_group in body["ui_actions"]
        for action in action_group["actions"]
    }
    assert "retake_photo" in action_ids
    assert "skip_photo" in action_ids
    assert "companion_name" not in action_ids


def test_generic_photo_with_homework_like_text_stays_image_context() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_share_homework_like_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "camera_photo_with_text",
            "mock_vision_text": "图片里有一张纸，上面像是数学题目和一些数字。",
            "child_caption": "我拍了一张图片给小白狐看。",
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["type"] == "homework_problem"
    assert body["recognized_content"]["image_purpose"] == "share"
    assert body["session_state"]["active_scene"] == "conversation.open"
    assert body["session_state"].get("needs_input") is None
    # With share purpose and high confidence, treats as normal image share, not homework
    assert "这道题是在问什么" not in body["reply"]["text"]


def test_generic_image_attachment_reply_does_not_echo_long_vision_text() -> None:
    long_vision_text = (
        "这是一段很长的图片识别内容，里面包含许多面向开发者的细节、"
        "分类判断、画面分析、可能风险和孩子不需要直接看到的上下文。"
    ) * 5

    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_long_vision_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_long_photo",
            "mock_vision_text": long_vision_text,
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["text"].startswith("这是一段很长的图片识别内容")
    # E3: 回复使用确定性模板，detail 截断到 20 字
    assert "我看到" in body["reply"]["text"]
    assert "分类判断" not in body["reply"]["text"]
    assert "要不要给它起个名字" in body["reply"]["text"]


def test_image_detail_helper_strips_labels_and_blocks_private_details() -> None:
    manager = ModalityManager()
    safe_detail = manager._child_visible_image_detail(
        RecognizedContent(
            type="image_observation",
            text="child_summary: 图里有一个窗边的灯。context_summary: 后面还有很多细节。",
            confidence=0.92,
            provider_name="mock_ocr",
            image_purpose=ImagePurpose.SHARE,
        )
    )
    private_detail = manager._child_visible_image_detail(
        RecognizedContent(
            type="image_observation",
            text="图片描述：纸上写着电话 138 0000 0000 和学校名字。",
            confidence=0.92,
            provider_name="mock_ocr",
            image_purpose=ImagePurpose.SHARE,
        )
    )

    assert safe_detail == "一个窗边的灯"
    assert private_detail is None


def test_generic_image_context_can_continue_in_conversation() -> None:
    child_id = "child_attachment_context_test"
    session_id = "attachment_context_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_blocks_photo",
            "mock_vision_text": "孩子搭了一个积木城堡",
            "child_caption": "你看我搭的这个",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我们继续聊刚才那张图片",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "conversation.open"
    assert "积木城堡" in body["reply"]["text"]
    assert "这道题" not in body["reply"]["text"]


def test_homework_like_share_image_context_reaches_conversation_prompt() -> None:
    child_id = "child_attachment_homework_like_context_test"
    session_id = "attachment_homework_like_context_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "camera_homework_like_photo",
            "mock_vision_text": "图片里有一张纸，上面像是数学题目和一些数字。",
            "child_caption": "我拍了一张图片给小白狐看。",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我们继续聊刚才那张图片",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "conversation.open"
    assert "数学题目" in body["reply"]["text"]


def test_conversation_attachment_privacy_image_routes_to_boundary() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_privacy_session",
            "attachment_type": "image",
            "image_purpose": "privacy_sensitive",
            "file_id": "mock_address_photo",
            "mock_vision_text": "照片里有家庭地址和电话号码",
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["type"] == "privacy_sensitive"
    assert body["session_state"]["active_scene"] == "privacy.boundary"
    assert "隐私信息" in body["reply"]["text"]


def test_privacy_image_context_still_routes_to_boundary_on_followup() -> None:
    child_id = "child_attachment_privacy_context_test"
    session_id = "attachment_privacy_context_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "privacy_sensitive",
            "file_id": "mock_address_photo_followup",
            "mock_vision_text": "照片里有家庭地址和电话号码",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我们继续聊刚才那张图片",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "privacy.boundary"
    assert body["debug"]["intent"]["intent"] == "privacy_question"


def test_share_image_followup_does_not_repeat_name_prompt_action() -> None:
    child_id = "child_attachment_followup_test"
    session_id = "attachment_followup_no_repeat_name_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_toy_photo",
            "mock_vision_text": "孩子搭了一个积木城堡",
            "child_caption": "你看我搭的这个",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我想跟你继续聊这个",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    action_ids = {
        action["id"]
        for action_group in body["ui_actions"]
        for action in action_group["actions"]
    }

    assert "companion_name" not in action_ids
