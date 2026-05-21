from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.domain.schemas.conversation_stream import ConversationStreamRequest
from app.services.conversation_stream_service import ConversationStreamService

router = APIRouter(prefix="/conversation", tags=["conversation"])
conversation_stream_service = ConversationStreamService(
    debug_enabled=get_settings().environment == "dev"
)


@router.post("/stream")
def stream_conversation(request: ConversationStreamRequest) -> StreamingResponse:
    return StreamingResponse(
        conversation_stream_service.stream_ndjson(request),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
