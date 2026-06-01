from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import IntentType, RiskCategory, RiskLevel
from app.domain.time import TimeContext


class ConversationInput(BaseModel):
    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1, max_length=2000)
    attachments: list[str] = Field(default_factory=list)
    quick_action_id: str | None = None


class ClientContext(BaseModel):
    device_time: datetime = Field(alias="deviceTime")
    timezone: str = Field(..., min_length=1)
    app_mode: str = Field(default="child", alias="appMode")

    model_config = ConfigDict(populate_by_name=True)


class ConversationMessageRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    input: ConversationInput
    client_context: ClientContext


class ConversationOpeningRequest(BaseModel):
    child_id: str = Field(..., min_length=1, alias="childId")
    session_id: str = Field(..., min_length=1, alias="sessionId")
    client_context: ClientContext = Field(alias="clientContext")

    model_config = ConfigDict(populate_by_name=True)


class Reply(BaseModel):
    type: Literal["agent_message"] = "agent_message"
    text: str
    voice_enabled: bool = True
    audio_url: str | None = None
    emotion: str = "warm"
    agent_motion: str = "gentle_idle"


class QuickAction(BaseModel):
    id: str
    label: str


class UiAction(BaseModel):
    type: Literal["show_quick_actions"] = "show_quick_actions"
    actions: list[QuickAction]


class CompanionObjectMeta(BaseModel):
    """Minimal companion object metadata for Android rendering."""
    id: str
    name: str
    object_type: str
    light_location: str
    state: str  # active / paused / seed
    action: str  # recall / co_create / none / name_seed
    visual_kind: str = "star"


class SessionState(BaseModel):
    base_scene: str
    active_scene: str
    needs_input: str | None = None
    requires_parent_attention: bool | None = None
    companion_object: CompanionObjectMeta | None = None


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


class HealthyEngagementDebug(BaseModel):
    turn_index: int | None = None
    recent_history_turns: int
    active_scene: str
    age_band: str
    reply_char_count: int
    question_count: int
    turn_guidance_hints: list[str] = Field(default_factory=list)
    boundary_signal: str | None = None
    boundary_respected: bool | None = None
    same_topic_score: int = 0
    consecutive_recent_questions: int = 0
    child_engagement_signal: str | None = None
    topic_shift_recommended: bool | None = None
    topic_shift_reason: str | None = None
    previous_topic_revived: bool | None = None
    model_conversation_control: dict[str, Any] | None = None
    final_conversation_control: dict[str, Any] | None = None
    reply_normalized: bool = False
    first_text_ms: float | None = None
    first_audio_ms: float | None = None
    turn_total_ms: float | None = None


class ConversationDebug(BaseModel):
    time_context: TimeContext
    parent_policy: ParentPolicyDebug
    safety: SafetyDebug | None = None
    intent: IntentDebug | None = None
    healthy_engagement: HealthyEngagementDebug | None = None


class ConversationMessageResponse(BaseModel):
    reply: Reply
    ui_actions: list[UiAction]
    session_state: SessionState
    debug: ConversationDebug | None = None
