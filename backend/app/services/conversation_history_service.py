from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.model_types import ModelMessage


class ConversationHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationHistoryService:
    """Short-term, in-memory conversation history for open conversation.

    This is not long-term memory and is intentionally not persisted. It gives the
    model recent turn context without storing full transcripts in the memory
    system or parent report.
    """

    def __init__(self, *, max_messages_per_session: int = 12) -> None:
        self._max_messages_per_session = max_messages_per_session
        self._messages_by_session: dict[str, list[ConversationHistoryMessage]] = {}

    def get_recent_model_messages(
        self,
        *,
        session_id: str,
        limit: int = 6,
    ) -> list[ModelMessage]:
        messages = self._messages_by_session.get(session_id, [])
        recent = messages[-limit:]
        return [
            ModelMessage(
                role="assistant" if message.role == "assistant" else "user",
                content=message.text,
            )
            for message in recent
        ]

    def record_turn(
        self,
        *,
        session_id: str,
        child_text: str,
        agent_text: str,
    ) -> None:
        messages = self._messages_by_session.setdefault(session_id, [])
        if child_text.strip():
            messages.append(
                ConversationHistoryMessage(role="user", text=child_text.strip())
            )
        if agent_text.strip():
            messages.append(
                ConversationHistoryMessage(
                    role="assistant",
                    text=agent_text.strip(),
                )
            )
        if len(messages) > self._max_messages_per_session:
            del messages[: len(messages) - self._max_messages_per_session]

    def reset_session(self, session_id: str) -> None:
        self._messages_by_session.pop(session_id, None)


_conversation_history_service = ConversationHistoryService()


def get_conversation_history_service() -> ConversationHistoryService:
    return _conversation_history_service
