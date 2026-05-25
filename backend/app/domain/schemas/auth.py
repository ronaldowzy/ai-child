from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChildAccountProfileInput(BaseModel):
    child_nickname: str | None = Field(default=None, max_length=80)
    child_display_name: str | None = Field(default=None, max_length=120)
    child_age: int | None = Field(default=None, ge=5, le=10)
    child_grade: str | None = Field(default=None, max_length=80)
    child_call_preference: str | None = Field(default=None, max_length=120)
    child_interests: list[str] = Field(default_factory=list, max_length=12)
    topic_boundaries: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("child_interests", "topic_boundaries")
    @classmethod
    def _compact_string_list(cls, value: list[str]) -> list[str]:
        compacted: list[str] = []
        for item in value:
            text = str(item).strip()
            if text and text not in compacted:
                compacted.append(text[:40])
        return compacted


class AuthRegisterRequest(ChildAccountProfileInput):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=160)

    @field_validator("username")
    @classmethod
    def _normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class AuthLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=160)

    @field_validator("username")
    @classmethod
    def _normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class AuthAccountProfile(BaseModel):
    child_account_id: str
    child_id: str
    username: str
    created_by_guardian: bool = True
    child_nickname: str | None = None
    child_display_name: str | None = None
    child_age: int | None = None
    child_grade: str | None = None
    child_call_preference: str | None = None
    child_interests: list[str] = Field(default_factory=list)
    topic_boundaries: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AuthSessionResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_at: datetime
    account: AuthAccountProfile


class AuthMeResponse(BaseModel):
    account: AuthAccountProfile


class AuthLogoutResponse(BaseModel):
    revoked: bool = True


class AuthAccountRecordData(BaseModel):
    id: str
    child_id: str
    username: str
    password_hash: str
    created_by_guardian: bool = True
    last_login_at: datetime | None = None


class AuthSessionRecordData(BaseModel):
    id: str
    child_account_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


def profile_preferences_from_input(
    profile: ChildAccountProfileInput,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preferences = dict(existing or {})
    if profile.child_age is not None:
        preferences["child_age"] = profile.child_age
    if profile.child_grade is not None:
        preferences["child_grade"] = profile.child_grade.strip()
    if profile.child_call_preference is not None:
        preferences["child_call_preference"] = profile.child_call_preference.strip()
    preferences["child_interests"] = list(profile.child_interests)
    preferences["topic_boundaries"] = list(profile.topic_boundaries)
    preferences["child_profile_schema"] = "task09_account_v0_1"
    return preferences
