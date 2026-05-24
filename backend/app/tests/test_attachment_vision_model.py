import pytest

from app.core.config import Settings
from app.domain.attachment import AttachmentCreateRequest, AttachmentType, ImagePurpose
from app.domain.model_types import ModelRequest, ModelResponse
from app.repositories.attachment_repository import InMemoryAttachmentRepository
from app.services.attachment_service import AttachmentService


IMAGE_DATA_URI = "data:image/png;base64,ZmFrZV9pbWFnZV9ieXRlcw=="


class FailingModelRegistry:
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise AssertionError("model vision path should not be called")


class CapturingModelRegistry:
    def __init__(
        self,
        *,
        provider_name: str = "mimo",
        response_text: str = "图片里是一只测试用的玩具，不包含真实儿童信息。",
    ) -> None:
        self.request: ModelRequest | None = None
        self.provider_name = provider_name
        self.response_text = response_text

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.request = request
        return ModelResponse(
            task_type=request.task_type,
            response_text=self.response_text,
            structured_output={},
            provider_name=self.provider_name,
            model_name="mimo-v2.5",
        )


def _request(**overrides: object) -> AttachmentCreateRequest:
    payload = {
        "child_id": "child_attachment_vision_test",
        "session_id": "session_attachment_vision_test",
        "attachment_type": AttachmentType.IMAGE,
        "image_purpose": ImagePurpose.ASK_WHAT_IS_THIS,
        "image_data_uri": IMAGE_DATA_URI,
        "child_caption": "这是一张 smoke 测试图。",
    }
    payload.update(overrides)
    return AttachmentCreateRequest(**payload)


def test_attachment_service_defaults_to_mock_ocr_with_image_data_uri() -> None:
    repository = InMemoryAttachmentRepository()
    service = AttachmentService(
        repository=repository,
        model_registry=FailingModelRegistry(),
        settings=Settings(model_provider="mock", vision_provider="mock"),
    )

    response = service.create_attachment(
        _request(mock_vision_text="孩子分享了一张测试图片。")
    )
    attachment = repository.get(response.attachment_id)

    assert response.recognized_content.provider_name == "mock_ocr"
    assert attachment is not None
    assert attachment.metadata["has_image_data_uri"] is True
    assert attachment.metadata["image_data_uri_stored"] is False
    assert IMAGE_DATA_URI not in str(attachment.metadata)


def test_attachment_service_uses_model_vision_when_explicitly_enabled() -> None:
    registry = CapturingModelRegistry()
    repository = InMemoryAttachmentRepository()
    service = AttachmentService(
        repository=repository,
        model_registry=registry,
        settings=Settings(model_provider="mock", vision_provider="mimo"),
    )

    response = service.create_attachment(_request())
    attachment = repository.get(response.attachment_id)

    assert registry.request is not None
    assert registry.request.metadata["contains_image"] is True
    assert registry.request.metadata["image_data_uri"] == IMAGE_DATA_URI
    assert response.recognized_content.provider_name == "mimo"
    assert response.recognized_content.type == "image_observation"
    assert attachment is not None
    assert attachment.metadata["mock"] is False
    assert IMAGE_DATA_URI not in str(attachment.metadata)


def test_model_vision_keeps_richer_context_without_child_facing_echo() -> None:
    registry = CapturingModelRegistry(
        response_text=(
            '{"child_summary":"我看到这张图里有一个红色玩具。",'
            '"context_summary":"图片里有一个红色玩具车，旁边有蓝色积木和一张写着2+3的问题卡片；孩子可能想问玩具或卡片内容。",'
            '"recognized_type":"image_observation"}'
        )
    )
    repository = InMemoryAttachmentRepository()
    service = AttachmentService(
        repository=repository,
        model_registry=registry,
        settings=Settings(model_provider="mock", vision_provider="mimo"),
    )

    response = service.create_attachment(_request())
    attachment = repository.get(response.attachment_id)

    assert attachment is not None
    assert "蓝色积木" in attachment.recognized_content.text
    assert "问题卡片" in attachment.recognized_content.text
    assert "红色玩具车" in response.reply.text
    assert "蓝色积木" not in response.reply.text
    assert "问题卡片" not in response.reply.text


def test_model_vision_does_not_treat_privacy_words_as_route_signal() -> None:
    repository = InMemoryAttachmentRepository()

    class PrivacyWordsRegistry(CapturingModelRegistry):
        def generate(self, request: ModelRequest) -> ModelResponse:
            self.request = request
            return ModelResponse(
                task_type=request.task_type,
                response_text="图片里是一张纸，文字里出现地址、电话、学校名这些词。",
                structured_output={},
                provider_name="mimo",
                model_name="mimo-v2.5",
            )

    service = AttachmentService(
        repository=repository,
        model_registry=PrivacyWordsRegistry(),
        settings=Settings(model_provider="mock", vision_provider="mimo"),
    )

    response = service.create_attachment(_request())

    assert response.recognized_content.type == "image_observation"
    assert response.session_state.active_scene == "conversation.open"
    assert "隐私信息" not in response.reply.text


def test_attachment_request_rejects_unsupported_image_data_uri() -> None:
    with pytest.raises(ValueError, match="png, jpeg, or webp"):
        _request(image_data_uri="data:text/plain;base64,ZmFrZQ==")
