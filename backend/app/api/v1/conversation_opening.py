from fastapi import APIRouter

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
) -> ConversationMessageResponse:
    return get_opening_service().create_opening(request)
