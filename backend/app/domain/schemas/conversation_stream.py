from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.schemas.conversation import ConversationMessageRequest


class ConversationStreamOptions(BaseModel):
    protocol_version: Literal["stream.v0.1"] = "stream.v0.1"
    text_granularity: Literal["sentence"] = "sentence"
    include_tts: bool = True
    audio_delivery: Literal["url"] = "url"
    client_turn_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
    )


class ConversationStreamRequest(ConversationMessageRequest):
    stream_options: ConversationStreamOptions = Field(
        default_factory=ConversationStreamOptions
    )


class ConversationStreamEvent(BaseModel):
    event_id: str
    turn_id: str
    seq: int = Field(..., ge=1)
    type: str
    created_at: datetime
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
