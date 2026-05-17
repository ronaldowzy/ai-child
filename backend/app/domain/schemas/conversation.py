from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.time import TimeContext


class ConversationInput(BaseModel):
    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1, max_length=2000)
    attachments: list[str] = Field(default_factory=list)


class ClientContext(BaseModel):
    device_time: datetime
    timezone: str = Field(..., min_length=1)
    app_mode: str = "child"


class ConversationMessageRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    input: ConversationInput
    client_context: ClientContext


class Reply(BaseModel):
    type: Literal["agent_message"] = "agent_message"
    text: str
    voice_enabled: bool = True
    emotion: str = "warm"


class QuickAction(BaseModel):
    id: str
    label: str


class UiAction(BaseModel):
    type: Literal["show_quick_actions"] = "show_quick_actions"
    actions: list[QuickAction]


class SessionState(BaseModel):
    base_scene: str
    active_scene: str
    needs_input: str | None = None


class ParentPolicyDebug(BaseModel):
    goals: list[str]
    communication_preferences: dict[str, Any]
    safety_rules: dict[str, Any]


class ConversationDebug(BaseModel):
    time_context: TimeContext
    parent_policy: ParentPolicyDebug


class ConversationMessageResponse(BaseModel):
    reply: Reply
    ui_actions: list[UiAction]
    session_state: SessionState
    debug: ConversationDebug | None = None
