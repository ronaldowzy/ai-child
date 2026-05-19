from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import RiskLevel
from app.domain.prompt import PromptVersion
from app.domain.scene import SceneRouteDecision
from app.domain.time import TimeContext


class AgentRuntimeSource(StrEnum):
    MODEL = "model"
    FALLBACK = "fallback"


class AgentRuntimeRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    child_text: str = Field(..., min_length=1)
    route_decision: SceneRouteDecision
    time_context: TimeContext
    parent_policy: Any | None = None
    memory_context: list[Any] | dict[str, Any] | str | None = None
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
