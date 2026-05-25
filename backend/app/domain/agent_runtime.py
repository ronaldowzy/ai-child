from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import RiskLevel
from app.domain.model_types import ModelMessage
from app.domain.prompt import PromptVersion
from app.domain.scene import SceneRouteDecision
from app.domain.time import TimeContext


class AgentRuntimeSource(StrEnum):
    MODEL = "model"
    FALLBACK = "fallback"


class ConversationControlMove(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=40)


class ConversationControl(BaseModel):
    child_engagement: str = Field(default="unclear", max_length=40)
    topic_continuity: str = Field(default="unclear", max_length=40)
    topic_shift_intent: str = Field(default="unclear", max_length=40)
    reason: str | None = Field(default=None, max_length=160)
    suggested_next_moves: list[ConversationControlMove] = Field(default_factory=list)
    source: str = Field(default="model", max_length=40)

    @field_validator("child_engagement")
    @classmethod
    def _valid_engagement(cls, value: str) -> str:
        allowed = {"high", "medium", "low", "unclear"}
        return value if value in allowed else "unclear"

    @field_validator("topic_continuity")
    @classmethod
    def _valid_continuity(cls, value: str) -> str:
        allowed = {"continue", "soft_shift", "stop", "unclear"}
        return value if value in allowed else "unclear"

    @field_validator("topic_shift_intent")
    @classmethod
    def _valid_shift_intent(cls, value: str) -> str:
        allowed = {"likely", "possible", "unlikely", "explicit", "unclear"}
        return value if value in allowed else "unclear"


class AgentRuntimeRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    child_text: str = Field(..., min_length=1)
    route_decision: SceneRouteDecision
    time_context: TimeContext
    parent_policy: Any | None = None
    memory_context: list[Any] | dict[str, Any] | str | None = None
    conversation_history: list[ModelMessage] = Field(default_factory=list)
    conversation_metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRuntimeResult(BaseModel):
    reply_text: str
    source: AgentRuntimeSource
    provider_name: str | None = None
    model_name: str | None = None
    fallback_reason: str | None = None
    prompt_versions: dict[str, PromptVersion] = Field(default_factory=dict)
    model_metadata: dict[str, Any] = Field(default_factory=dict)
    output_risk_level: RiskLevel | None = None
