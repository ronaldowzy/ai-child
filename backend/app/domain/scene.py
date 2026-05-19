from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import IntentType, RiskLevel
from app.domain.time import TimeContext


class SceneId(StrEnum):
    DAILY_AFTER_SCHOOL_CHECKIN = "daily.after_school_checkin"
    LEARNING_HOMEWORK_HELP = "learning.homework_help"
    DAILY_BEDTIME_REFLECTION = "daily.bedtime_reflection"
    SAFETY_GUARDIAN = "safety.guardian"
    SAFETY_GENTLE_CHECKIN = "safety.gentle_checkin"
    PRIVACY_BOUNDARY = "privacy.boundary"


class SceneTransitionType(StrEnum):
    REPLACE = "replace"
    PUSH = "push"
    POP = "pop"
    MERGE = "merge"
    END = "end"


class SceneAction(BaseModel):
    id: str
    label: str


class SceneDefinition(BaseModel):
    scene_id: SceneId
    display_name: str
    prompt_template: str
    default_transition: SceneTransitionType
    default_needs_input: str | None = None
    priority: int = 0
    is_safety_scene: bool = False


class SceneRouteRequest(BaseModel):
    child_id: str
    session_id: str
    message_id: str | None = None
    text: str
    time_context: TimeContext
    intent: IntentType
    sub_intent: str | None = None
    intent_confidence: float = 0.0
    intent_evidence: list[str] = Field(default_factory=list)
    needs_modality: bool = False
    suggested_modalities: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.NONE
    safety_requires_parent_attention: bool = False
    safety_evidence: list[str] = Field(default_factory=list)
    parent_goals: list[str] = Field(default_factory=list)
    current_stack: list[SceneId] = Field(default_factory=list)
    homework_problem_text: str | None = None
    homework_problem_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SceneRouteDecision(BaseModel):
    message_id: str | None = None
    session_id: str
    primary_intent: IntentType
    base_scene: SceneId
    active_scene: SceneId
    transition: SceneTransitionType
    scene_stack: list[SceneId]
    risk_level: RiskLevel
    confidence: float
    reason: str
    sub_scene: str | None = None
    side_context: list[str] = Field(default_factory=list)
    requires_parent_attention: bool = False
    needs_input: str | None = None
    reply_text: str
    reply_emotion: str = "warm"
    quick_actions: list[SceneAction] = Field(default_factory=list)
    signals: dict[str, Any] = Field(default_factory=dict)


class RoutingDecisionRecord(BaseModel):
    id: str
    message_id: str
    session_id: str
    primary_intent: IntentType
    active_scene: SceneId
    sub_scene: str | None = None
    risk_level: RiskLevel
    decision_json: dict[str, Any]
    signals_json: dict[str, Any]
    confidence: float
    created_at: datetime
