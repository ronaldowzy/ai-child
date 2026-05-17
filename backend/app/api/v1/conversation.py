from fastapi import APIRouter

from app.domain.schemas.conversation import (
    ConversationMessageRequest,
    ConversationMessageResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversation", tags=["conversation"])
conversation_service = ConversationService()


@router.post("/message", response_model=ConversationMessageResponse)
def create_message(
    request: ConversationMessageRequest,
) -> ConversationMessageResponse:
    return conversation_service.handle_message(request)
