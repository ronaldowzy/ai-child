from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ParentReportGenerationStatus(StrEnum):
    MODEL_GENERATED = "model_generated"
    MODEL_BLOCKED = "model_blocked"
    MODEL_FAILED = "model_failed"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    LEGACY = "legacy"


class ParentReport(BaseModel):
    child_id: str = Field(..., min_length=1)
    date: date
    summary: str = Field(..., min_length=1, max_length=500)
    learning_observations: list[str] = Field(default_factory=list, max_length=10)
    expression_observations: list[str] = Field(default_factory=list, max_length=10)
    emotion_observations: list[str] = Field(default_factory=list, max_length=10)
    safety_alerts: list[str] = Field(default_factory=list, max_length=10)
    suggested_parent_actions: list[str] = Field(default_factory=list, max_length=10)
    tonight_parent_bridge: str | None = Field(default=None, max_length=280)
    created_at: datetime
    generation_status: ParentReportGenerationStatus = ParentReportGenerationStatus.LEGACY
    generated_by: str = Field(default="legacy", max_length=80)
    generation_error_code: str | None = Field(default=None, max_length=120)
    material_fingerprint: str | None = Field(default=None, max_length=120)
