from uuid import uuid4

from pydantic import BaseModel

from app.domain.attachment import (
    AttachmentCreateRequest,
    AttachmentCreateResponse,
    AttachmentRecord,
    AttachmentStatus,
    ImagePurpose,
    RecognizedContent,
)
from app.domain.schemas.conversation import Reply, SessionState, UiAction
from app.providers.ocr.base import OCRRequest
from app.providers.ocr.mock_ocr_provider import MockOCRProvider
from app.repositories.attachment_repository import (
    InMemoryAttachmentRepository,
    get_attachment_repository,
)
from app.services.modality_manager import ModalityManager, get_modality_manager


class HomeworkAttachmentContext(BaseModel):
    attachment_id: str
    recognized_content: RecognizedContent


class AttachmentService:
    """Business service for mock homework attachments and OCR decisions."""

    def __init__(
        self,
        *,
        repository: InMemoryAttachmentRepository | None = None,
        modality_manager: ModalityManager | None = None,
        ocr_provider: MockOCRProvider | None = None,
    ) -> None:
        self._repository = repository or get_attachment_repository()
        self._modality_manager = modality_manager or get_modality_manager()
        self._ocr_provider = ocr_provider or MockOCRProvider()

    def create_attachment(
        self, request: AttachmentCreateRequest
    ) -> AttachmentCreateResponse:
        recognized_content = self._ocr_provider.recognize(
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
                metadata={
                    "mock": True,
                    "has_file_id": bool(request.file_id),
                    "ocr_provider": decision.recognized_content.provider_name,
                    "image_purpose": (
                        decision.recognized_content.image_purpose.value
                        if decision.recognized_content.image_purpose
                        else None
                    ),
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
        )

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


_attachment_service = AttachmentService()


def get_attachment_service() -> AttachmentService:
    return _attachment_service
