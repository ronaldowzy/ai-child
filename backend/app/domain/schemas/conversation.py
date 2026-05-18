from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.enums import IntentType, RiskCategory, RiskLevel
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
    requires_parent_attention: bool | None = None


class SafetyDebug(BaseModel):
    risk_level: RiskLevel
    primary_category: RiskCategory
    categories: list[RiskCategory]
    requires_parent_attention: bool
    evidence: list[str]
    safe_response_hint: str


class IntentDebug(BaseModel):
    intent: IntentType
    sub_intent: str | None = None
    emotion: str
    risk_level: RiskLevel
    needs_modality: bool
    suggested_modalities: list[str]
    confidence: float
    evidence: list[str]


class ParentPolicyDebug(BaseModel):
    goals: list[str]
    communication_preferences: dict[str, Any]
    safety_rules: dict[str, Any]


class ConversationDebug(BaseModel):
    time_context: TimeContext
    parent_policy: ParentPolicyDebug
    safety: SafetyDebug | None = None
    intent: IntentDebug | None = None


class ConversationMessageResponse(BaseModel):
    reply: Reply
    ui_actions: list[UiAction]
    session_state: SessionState
    debug: ConversationDebug | None = None
