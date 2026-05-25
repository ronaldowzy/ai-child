from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse

from app.api.v1.auth import optional_auth_account
from app.core.config import get_settings
from app.domain.schemas.conversation_stream import ConversationStreamRequest
from app.services.conversation_stream_service import ConversationStreamService

router = APIRouter(prefix="/conversation", tags=["conversation"])
conversation_stream_service = ConversationStreamService(
    debug_enabled=get_settings().environment == "dev"
)


@router.post("/stream")
def stream_conversation(
    request: ConversationStreamRequest,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        request = request.model_copy(update={"child_id": account.child_id})
    return StreamingResponse(
        conversation_stream_service.stream_ndjson(request),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
