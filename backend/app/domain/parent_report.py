from datetime import date, datetime

from pydantic import BaseModel, Field


class ParentReport(BaseModel):
    child_id: str = Field(..., min_length=1)
    date: date
    summary: str = Field(..., min_length=1, max_length=500)
    learning_observations: list[str] = Field(default_factory=list, max_length=10)
    expression_observations: list[str] = Field(default_factory=list, max_length=10)
    emotion_observations: list[str] = Field(default_factory=list, max_length=10)
    safety_alerts: list[str] = Field(default_factory=list, max_length=10)
    suggested_parent_actions: list[str] = Field(default_factory=list, max_length=10)
    created_at: datetime
