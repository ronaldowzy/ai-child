from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MemoryType(StrEnum):
    INTEREST = "interest"
    LEARNING_PATTERN = "learning_pattern"
    EXPRESSION_PATTERN = "expression_pattern"
    EMOTION_OBSERVATION = "emotion_observation"
    EVENT = "event"
    SAFETY = "safety"
    PARENT_RULE = "parent_rule"
    STRATEGY = "strategy"


class MemorySensitivity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryEvidence(BaseModel):
    source: str = Field(..., min_length=1, max_length=80)
    session_id: str | None = Field(default=None, min_length=1, max_length=120)
    quote_summary: str = Field(..., min_length=1, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryBase(BaseModel):
    child_id: str = Field(..., min_length=1, max_length=120)
    memory_type: MemoryType
    content: str = Field(..., min_length=1, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=12)
    evidence: list[MemoryEvidence] = Field(..., min_length=1, max_length=5)
    confidence: float = Field(..., ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity: MemorySensitivity = MemorySensitivity.LOW
    visible_to_parent: bool = True
    visible_to_child: bool = False
    requires_parent_attention: bool = False
    expires_at: datetime | None = None
    embedding_id: str | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        normalized: list[str] = []
        for tag in tags:
            clean_tag = tag.strip()
            if clean_tag and clean_tag not in normalized:
                normalized.append(clean_tag[:40])
        return normalized


class MemoryCreateRequest(MemoryBase):
    pass


class MemoryUpdateRequest(BaseModel):
    memory_type: MemoryType | None = None
    content: str | None = Field(default=None, min_length=1, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=12)
    evidence: list[MemoryEvidence] | None = Field(default=None, min_length=1, max_length=5)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    sensitivity: MemorySensitivity | None = None
    visible_to_parent: bool | None = None
    visible_to_child: bool | None = None
    requires_parent_attention: bool | None = None
    expires_at: datetime | None = None
    embedding_id: str | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str] | None) -> list[str] | None:
        if tags is None:
            return None
        normalized: list[str] = []
        for tag in tags:
            clean_tag = tag.strip()
            if clean_tag and clean_tag not in normalized:
                normalized.append(clean_tag[:40])
        return normalized


class MemoryItem(MemoryBase):
    id: str
    created_at: datetime
    updated_at: datetime


class MemoryDeleteResponse(BaseModel):
    deleted: bool
