from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AsrAudioFormat(StrEnum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"


class AsrMode(StrEnum):
    CONFIRM_BEFORE_SEND = "confirm_before_send"


class AsrProviderName(StrEnum):
    MOCK = "mock"
    MIMO = "mimo"


class AsrTranscriptStatus(StrEnum):
    OK = "ok"
    NEEDS_RETRY = "needs_retry"
    BLOCKED = "blocked"
    FAILED = "failed"


class AsrAudioPayload(BaseModel):
    data: str = Field(..., min_length=1, max_length=35_000_000)
    format: AsrAudioFormat = AsrAudioFormat.WAV
    sample_rate_hz: int | None = Field(
        default=None,
        alias="sampleRateHz",
        ge=8000,
        le=96000,
    )
    channel_count: int | None = Field(
        default=None,
        alias="channelCount",
        ge=1,
        le=2,
    )
    duration_ms: int | None = Field(
        default=None,
        alias="durationMs",
        ge=1,
        le=30_000,
    )

    model_config = ConfigDict(populate_by_name=True)


class AsrTranscriptionRequest(BaseModel):
    child_id: str | None = Field(default=None, alias="childId", max_length=128)
    session_id: str | None = Field(default=None, alias="sessionId", max_length=128)
    audio: AsrAudioPayload
    language: str = Field(default="zh-CN", min_length=2, max_length=16)
    mode: AsrMode = AsrMode.CONFIRM_BEFORE_SEND
    client_context: dict[str, Any] = Field(
        default_factory=dict,
        alias="clientContext",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class AsrTranscriptionResponse(BaseModel):
    status: AsrTranscriptStatus
    transcript: str | None = Field(default=None, max_length=2000)
    requires_confirmation: bool = Field(default=True, alias="requiresConfirmation")
    provider: AsrProviderName
    model: str
    language: str = "zh-CN"
    duration_ms: int | None = Field(default=None, alias="durationMs")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    error_code: str | None = Field(default=None, alias="errorCode")
    fallback_action: str | None = Field(default=None, alias="fallbackAction")

    model_config = ConfigDict(populate_by_name=True)
