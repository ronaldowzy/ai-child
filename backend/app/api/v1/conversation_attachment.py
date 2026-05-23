from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.domain.attachment import (
    AttachmentCreateRequest,
    AttachmentCreateResponse,
    ImagePurpose,
)
from app.services.attachment_service import (
    AttachmentImageValidationError,
    AttachmentService,
    AttachmentVisionProviderBlockedError,
    REAL_IMAGE_MAX_BYTES,
    RealImageUpload,
)

router = APIRouter(prefix="/conversation", tags=["conversation"])
image_router = APIRouter(prefix="/attachments", tags=["attachments"])
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


@image_router.post(
    "/images",
    response_model=AttachmentCreateResponse,
    response_model_exclude_none=True,
)
async def upload_image_attachment(
    child_id: str = Form(...),
    session_id: str = Form(...),
    image_purpose: ImagePurpose = Form(ImagePurpose.SHARE),
    child_caption: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> AttachmentCreateResponse:
    try:
        image_bytes = await file.read(REAL_IMAGE_MAX_BYTES + 1)
        return attachment_service.create_real_image_upload(
            RealImageUpload(
                child_id=child_id,
                session_id=session_id,
                image_bytes=image_bytes,
                mime_type=file.content_type or "",
                filename=file.filename,
                image_purpose=image_purpose,
                child_caption=child_caption,
            )
        )
    except AttachmentImageValidationError as exc:
        detail = str(exc)
        if detail == "image_upload_too_large":
            raise HTTPException(status_code=413, detail=detail) from exc
        raise HTTPException(status_code=415, detail=detail) from exc
    except AttachmentVisionProviderBlockedError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
