from fastapi import APIRouter, Header

from app.api.v1.auth import optional_auth_account
from app.domain.schemas.conversation import (
    ConversationMessageRequest,
    ConversationMessageResponse,
)
from app.core.config import get_settings
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversation", tags=["conversation"])
conversation_service = ConversationService(
    debug_enabled=get_settings().environment == "dev"
)


@router.post(
    "/message",
    response_model=ConversationMessageResponse,
    response_model_exclude_none=True,
)
def create_message(
    request: ConversationMessageRequest,
    authorization: str | None = Header(default=None),
) -> ConversationMessageResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        request = request.model_copy(update={"child_id": account.child_id})
    return conversation_service.handle_message(request)
