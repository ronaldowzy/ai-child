from fastapi import APIRouter

from app.domain.attachment import AttachmentCreateRequest, AttachmentCreateResponse
from app.services.attachment_service import AttachmentService

router = APIRouter(prefix="/conversation", tags=["conversation"])
attachment_service = AttachmentService()


@router.post(
    "/attachment",
    response_model=AttachmentCreateResponse,
    response_model_exclude_none=True,
)
def create_attachment(
    request: AttachmentCreateRequest,
) -> AttachmentCreateResponse:
    return attachment_service.create_attachment(request)
