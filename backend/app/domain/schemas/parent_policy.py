from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.time import TimeScheduleEntry, default_daily_schedule


def default_parent_goals() -> list[str]:
    return [
        "鼓励孩子每天说一件学校小事",
        "学习问题先引导思路，不直接给答案",
    ]


def default_communication_preferences() -> dict[str, Any]:
    return {
        "tone": "warm_calm",
        "expression_support": "offer_choices_before_open_questions",
        "avoid_labels": True,
    }


def default_safety_rules() -> dict[str, Any]:
    return {
        "no_secret_requests": True,
        "encourage_trusted_adult_for_high_risk": True,
        "homework_answer_policy": "scaffold_not_direct_answer",
    }


class ParentSchedule(BaseModel):
    daily_schedule: list[TimeScheduleEntry] = Field(
        default_factory=default_daily_schedule
    )


class ParentPolicy(BaseModel):
    child_id: str = Field(..., min_length=1)
    goals: list[str] = Field(default_factory=default_parent_goals)
    communication_preferences: dict[str, Any] = Field(
        default_factory=default_communication_preferences
    )
    safety_rules: dict[str, Any] = Field(default_factory=default_safety_rules)
    schedule: ParentSchedule = Field(default_factory=ParentSchedule)
    version: int = 1
    created_at: datetime
    updated_at: datetime


class ParentPolicyUpdateRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    goals: list[str] | None = None
    communication_preferences: dict[str, Any] | None = None
    safety_rules: dict[str, Any] | None = None
    schedule: ParentSchedule | None = None


class ParentPolicyResponse(ParentPolicy):
    pass
