import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.domain.attachment import (
    AttachmentCreateRequest,
    AttachmentCreateResponse,
    AttachmentRecord,
    AttachmentStatus,
    AttachmentType,
    ImagePurpose,
    RecognizedContent,
)
from app.domain.model_types import ModelMessage, ModelRequest, ModelTaskType
from app.domain.schemas.conversation import Reply, SessionState, UiAction
from app.providers.ocr.base import OCRRequest
from app.providers.ocr.mock_ocr_provider import MockOCRProvider
from app.repositories.attachment_repository import (
    InMemoryAttachmentRepository,
    get_attachment_repository,
)
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.modality_manager import ModalityManager, get_modality_manager


ALLOWED_REAL_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
REAL_IMAGE_MAX_BYTES = AttachmentCreateRequest.MAX_IMAGE_BYTES


class AttachmentImageValidationError(ValueError):
    pass


class AttachmentVisionProviderBlockedError(RuntimeError):
    def __init__(self, reason: str, *, status_code: int = 502) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True)
class RealImageUpload:
    child_id: str
    session_id: str
    image_bytes: bytes
    mime_type: str
    filename: str | None = None
    image_purpose: ImagePurpose = ImagePurpose.SHARE
    child_caption: str | None = None


class HomeworkAttachmentContext(BaseModel):
    attachment_id: str
    recognized_content: RecognizedContent

    def to_prompt_context(self) -> dict[str, str | None]:
        return {
            "attachment_id": self.attachment_id,
            "image_purpose": (
                self.recognized_content.image_purpose.value
                if self.recognized_content.image_purpose
                else None
            ),
            "recognized_type": self.recognized_content.type,
            "recognized_text": self.recognized_content.text,
            "child_caption": self.recognized_content.child_caption,
        }


class ImageAttachmentContext(BaseModel):
    attachment_id: str
    image_purpose: ImagePurpose | None = None
    recognized_type: str
    recognized_text: str | None = None
    child_caption: str | None = None

    def to_prompt_context(self) -> dict[str, str | None]:
        return {
            "attachment_id": self.attachment_id,
            "image_purpose": self.image_purpose.value if self.image_purpose else None,
            "recognized_type": self.recognized_type,
            "recognized_text": self.recognized_text,
            "child_caption": self.child_caption,
        }


logger = logging.getLogger("app.attachment")


class AttachmentService:
    """Business service for image attachments and OCR/vision decisions."""

    def __init__(
        self,
        *,
        repository: InMemoryAttachmentRepository | None = None,
        modality_manager: ModalityManager | None = None,
        ocr_provider: MockOCRProvider | None = None,
        model_registry: ModelRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository or get_attachment_repository()
        self._modality_manager = modality_manager or get_modality_manager()
        self._ocr_provider = ocr_provider or MockOCRProvider()
        self._model_registry = model_registry or get_model_registry()
        self._settings = settings or get_settings()
        self._image_storage_dir = self._settings.resolve_repo_path(
            "backend/storage/attachments/images"
        )

    def create_attachment(
        self, request: AttachmentCreateRequest
    ) -> AttachmentCreateResponse:
        logger.info(
            "create_attachment: childId=%s, type=%s, purpose=%s",
            request.child_id,
            request.attachment_type,
            request.image_purpose,
        )
        recognized_content = self._recognize(request)
        logger.info(
            "create_attachment: recognized type=%s, confidence=%.2f, purpose=%s",
            recognized_content.type,
            recognized_content.confidence,
            recognized_content.image_purpose,
        )
        decision = self._modality_manager.decide_image_attachment(recognized_content)
        attachment = self._repository.save(
            AttachmentRecord(
                id=f"att_{uuid4().hex}",
                child_id=request.child_id,
                session_id=request.session_id,
                attachment_type=request.attachment_type,
                image_purpose=request.image_purpose,
                file_id=request.file_id,
                status=decision.status,
                recognized_content=decision.recognized_content,
                metadata=self._safe_attachment_metadata(
                    request=request,
                    recognized_content=decision.recognized_content,
                ),
            )
        )

        return AttachmentCreateResponse(
            attachment_id=attachment.id,
            recognized_content=attachment.recognized_content,
            reply=Reply(text=decision.reply_text, emotion=decision.reply_emotion),
            ui_actions=[
                UiAction(actions=decision.quick_actions)
            ]
            if decision.quick_actions
            else [],
            session_state=SessionState(
                base_scene="conversation.open",
                active_scene=decision.active_scene,
                needs_input=decision.needs_input,
            ),
        )

    def create_real_image_upload(
        self,
        upload: RealImageUpload,
    ) -> AttachmentCreateResponse:
        logger.info(
            "create_real_image_upload: childId=%s, purpose=%s, size=%dbytes, mime=%s",
            upload.child_id,
            upload.image_purpose,
            len(upload.image_bytes),
            upload.mime_type,
        )
        mime_type = upload.mime_type.lower().split(";", 1)[0].strip()
        if mime_type not in ALLOWED_REAL_IMAGE_MIME_TYPES:
            raise AttachmentImageValidationError("unsupported_image_mime_type")
        if not upload.image_bytes:
            raise AttachmentImageValidationError("empty_image_upload")
        if len(upload.image_bytes) > REAL_IMAGE_MAX_BYTES:
            raise AttachmentImageValidationError("image_upload_too_large")

        attachment_id = f"att_{uuid4().hex}"
        file_path = self._store_real_image(
            attachment_id=attachment_id,
            image_bytes=upload.image_bytes,
            mime_type=mime_type,
        )
        request = AttachmentCreateRequest(
            child_id=upload.child_id,
            session_id=upload.session_id,
            attachment_type=AttachmentType.IMAGE,
            image_purpose=upload.image_purpose,
            image_data_uri=self._to_image_data_uri(upload.image_bytes, mime_type),
            child_caption=upload.child_caption,
            metadata={
                "real_image_upload": True,
                "mime_type": mime_type,
                "size_bytes": len(upload.image_bytes),
                "filename_present": bool(upload.filename),
            },
        )
        try:
            recognized_content = self._recognize_with_model_vision(
                request,
                require_real_provider=True,
            )
        except AttachmentVisionProviderBlockedError:
            raise
        except Exception as exc:
            raise AttachmentVisionProviderBlockedError(
                "vision_provider_unavailable",
                status_code=502,
            ) from exc
        decision = self._modality_manager.decide_image_attachment(recognized_content)
        attachment = self._repository.save(
            AttachmentRecord(
                id=attachment_id,
                child_id=upload.child_id,
                session_id=upload.session_id,
                attachment_type=AttachmentType.IMAGE,
                image_purpose=upload.image_purpose,
                file_id=None,
                status=decision.status,
                recognized_content=decision.recognized_content,
                metadata={
                    "mock": False,
                    "source": "real_image_upload",
                    "mime_type": mime_type,
                    "size_bytes": len(upload.image_bytes),
                    "local_path": str(file_path),
                    "image_data_uri_stored": False,
                    "ocr_provider": decision.recognized_content.provider_name,
                    "image_purpose": upload.image_purpose.value,
                },
            )
        )

        return AttachmentCreateResponse(
            attachment_id=attachment.id,
            recognized_content=attachment.recognized_content,
            reply=Reply(text=decision.reply_text, emotion=decision.reply_emotion),
            ui_actions=[
                UiAction(actions=decision.quick_actions)
            ]
            if decision.quick_actions
            else [],
            session_state=SessionState(
                base_scene="conversation.open",
                active_scene=decision.active_scene,
                needs_input=decision.needs_input,
            ),
            mime_type=mime_type,
            size_bytes=len(upload.image_bytes),
            created_at=attachment.created_at,
        )

    def _recognize(self, request: AttachmentCreateRequest) -> RecognizedContent:
        if request.image_data_uri and self._should_use_model_vision():
            return self._recognize_with_model_vision(request)

        return self._ocr_provider.recognize(
            OCRRequest(
                attachment_type=request.attachment_type,
                image_purpose=request.image_purpose,
                file_id=request.file_id,
                mock_ocr_text=request.mock_ocr_text,
                mock_vision_text=request.mock_vision_text,
                child_caption=request.child_caption,
                mock_confidence=request.mock_confidence,
                metadata=request.metadata,
            )
        )

    def _should_use_model_vision(self) -> bool:
        configured_provider = (self._settings.vision_provider or "").strip().lower()
        if configured_provider == "mimo":
            return True
        return (
            configured_provider in {"", "mock"}
            and (self._settings.model_provider or "").strip().lower() == "mimo"
        ) or os.getenv("CHILD_AI_VISION_PROVIDER", "").strip().lower() == "mimo"

    def _recognize_with_model_vision(
        self,
        request: AttachmentCreateRequest,
        *,
        require_real_provider: bool = False,
    ) -> RecognizedContent:
        prompt = self._vision_prompt(request)
        response = self._model_registry.generate(
            ModelRequest(
                task_type=ModelTaskType.VISION,
                input_text=prompt,
                messages=[ModelMessage(role="user", content=prompt)],
                context={
                    "conversation": {
                        "child_id": request.child_id,
                        "session_id": request.session_id,
                    }
                },
                metadata={
                    "contains_image": True,
                    "contains_child_data": True,
                    "image_data_uri": request.image_data_uri,
                },
            )
        )
        if require_real_provider:
            metadata = response.metadata or {}
            if metadata.get("policy_blocked"):
                raise AttachmentVisionProviderBlockedError(
                    "vision_policy_blocked",
                    status_code=403,
                )
            if response.provider_name != "mimo" or metadata.get("fallback_used"):
                raise AttachmentVisionProviderBlockedError(
                    "vision_provider_unavailable",
                    status_code=502,
                )
        vision_output = self._parse_vision_output(response.response_text)
        confidence = response.structured_output.get(
            "confidence",
            vision_output.get("confidence", 0.75),
        )
        fallback_action = response.structured_output.get("fallback_action")
        recognized_text = (
            vision_output.get("context_summary")
            or vision_output.get("child_summary")
            or response.response_text
        )
        recognized_type = vision_output.get("recognized_type")
        recognized_type_value = recognized_type if isinstance(recognized_type, str) else None
        return RecognizedContent(
            type=(
                recognized_type_value
                if recognized_type_value
                in {
                    "homework_problem",
                    "image_observation",
                    "privacy_sensitive",
                    "unsafe_unknown",
                }
                else self._recognized_type(
                    text=recognized_text,
                    attachment_type=request.attachment_type,
                    image_purpose=request.image_purpose,
                )
            ),
            text=self._truncate_vision_text(recognized_text),
            confidence=confidence if isinstance(confidence, float | int) else 0.75,
            provider_name=response.provider_name,
            image_purpose=request.image_purpose,
            child_caption=request.child_caption,
            fallback_action=(
                fallback_action if isinstance(fallback_action, str) else None
            ),
        )

    def _vision_prompt(self, request: AttachmentCreateRequest) -> str:
        purpose = request.image_purpose.value if request.image_purpose else "unknown"
        caption = request.child_caption or ""
        return (
            "你是小白狐的图片理解模块。请返回严格 JSON，不要 Markdown。"
            "字段：child_summary, context_summary, recognized_type。"
            "child_summary 是一句孩子可理解的短摘要，不超过80个中文字符；"
            "context_summary 是供后续对话使用的受控图片上下文，保留关键物体、文字、场景和孩子可能想问的点，不超过500个中文字符。"
            "recognized_type 只能是 image_observation、homework_problem、privacy_sensitive 或 unsafe_unknown。"
            "不要输出作业最终答案。若图片像作业题，只提取题目内容和要求；"
            "不要做模板化隐私提醒，也不要猜测图片里有未明确出现的风险；"
            "除非图片用途明确为隐私敏感，否则按普通图片继续描述。"
            f"图片用途: {purpose}。孩子补充说明: {caption[:120]}"
        )

    def _parse_vision_output(self, response_text: str) -> dict[str, object]:
        stripped = response_text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`").strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return parsed

    def _recognized_type(
        self,
        *,
        text: str,
        attachment_type: object,
        image_purpose: ImagePurpose | None,
    ) -> str:
        if image_purpose == ImagePurpose.PRIVACY_SENSITIVE:
            return "privacy_sensitive"
        if image_purpose == ImagePurpose.UNSAFE_UNKNOWN:
            return "unsafe_unknown"
        if (
            image_purpose == ImagePurpose.LEARNING_HOMEWORK
            or attachment_type == AttachmentType.HOMEWORK_PHOTO
        ):
            return "homework_problem"

        normalized = text.lower()
        homework_keywords = ("题目", "作业", "算式", "应用题", "选择题", "练习")
        if any(keyword in normalized for keyword in homework_keywords):
            return "homework_problem"
        return "image_observation"

    def _truncate_vision_text(self, text: str) -> str:
        stripped = text.strip()
        return stripped[:500]

    def _to_image_data_uri(self, image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _store_real_image(
        self,
        *,
        attachment_id: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> Path:
        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }[mime_type]
        self._image_storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._image_storage_dir / f"{attachment_id}{suffix}"
        file_path.write_bytes(image_bytes)
        return file_path

    def _safe_attachment_metadata(
        self,
        *,
        request: AttachmentCreateRequest,
        recognized_content: RecognizedContent,
    ) -> dict[str, object]:
        return {
            "mock": recognized_content.provider_name.startswith("mock"),
            "has_file_id": bool(request.file_id),
            "has_image_data_uri": bool(request.image_data_uri),
            "image_data_uri_stored": False if request.image_data_uri else None,
            "ocr_provider": recognized_content.provider_name,
            "image_purpose": (
                recognized_content.image_purpose.value
                if recognized_content.image_purpose
                else None
            ),
        }

    def get_ready_homework_context(
        self,
        attachment_ids: list[str],
        *,
        child_id: str,
        session_id: str,
    ) -> HomeworkAttachmentContext | None:
        for attachment_id in attachment_ids:
            attachment = self._repository.get(attachment_id)
            if (
                attachment
                and attachment.child_id == child_id
                and attachment.session_id == session_id
                and attachment.status == AttachmentStatus.OCR_READY
                and attachment.recognized_content.type == "homework_problem"
                and attachment.recognized_content.image_purpose
                in {None, ImagePurpose.LEARNING_HOMEWORK}
                and attachment.recognized_content.text
            ):
                return HomeworkAttachmentContext(
                    attachment_id=attachment.id,
                    recognized_content=attachment.recognized_content,
                )
        return None

    def get_image_context(
        self,
        attachment_ids: list[str],
        *,
        child_id: str,
        session_id: str,
    ) -> ImageAttachmentContext | None:
        for attachment_id in attachment_ids:
            attachment = self._repository.get(attachment_id)
            if (
                attachment
                and attachment.child_id == child_id
                and attachment.session_id == session_id
                and attachment.status in {AttachmentStatus.IMAGE_READY, AttachmentStatus.OCR_READY}
            ):
                return ImageAttachmentContext(
                    attachment_id=attachment.id,
                    image_purpose=attachment.recognized_content.image_purpose,
                    recognized_type=attachment.recognized_content.type,
                    recognized_text=attachment.recognized_content.text,
                    child_caption=attachment.recognized_content.child_caption,
                )
        return None


_attachment_service = AttachmentService()


def get_attachment_service() -> AttachmentService:
    return _attachment_service
