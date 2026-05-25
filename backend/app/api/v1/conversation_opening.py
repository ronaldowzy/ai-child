from fastapi import APIRouter, Header

from app.api.v1.auth import optional_auth_account
from app.domain.schemas.conversation import (
    ConversationMessageResponse,
    ConversationOpeningRequest,
)
from app.services.opening_service import get_opening_service

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post(
    "/opening",
    response_model=ConversationMessageResponse,
    response_model_exclude_none=True,
)
def create_opening(
    request: ConversationOpeningRequest,
    authorization: str | None = Header(default=None),
) -> ConversationMessageResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        request = request.model_copy(update={"child_id": account.child_id})
    return get_opening_service().create_opening(request)
