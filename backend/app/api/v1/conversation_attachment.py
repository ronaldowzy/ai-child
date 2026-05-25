from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from app.api.v1.auth import optional_auth_account
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
    authorization: str | None = Header(default=None),
) -> AttachmentCreateResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        request = request.model_copy(update={"child_id": account.child_id})
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
    authorization: str | None = Header(default=None),
) -> AttachmentCreateResponse:
    try:
        account = optional_auth_account(authorization)
        if account is not None:
            child_id = account.child_id
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
