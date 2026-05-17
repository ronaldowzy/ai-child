from fastapi import APIRouter

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
) -> ConversationMessageResponse:
    return conversation_service.handle_message(request)
