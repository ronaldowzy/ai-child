from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.domain.schemas.asr import AsrAudioFormat, AsrProviderName


class AsrProviderError(RuntimeError):
    """Base error for ASR provider failures."""


class AsrProviderDisabledError(AsrProviderError):
    pass


class AsrProviderConfigurationError(AsrProviderError):
    pass


class AsrProviderTimeoutError(AsrProviderError):
    pass


class AsrProviderHttpError(AsrProviderError):
    pass


class AsrProviderRequest(BaseModel):
    audio_data_uri: str
    audio_format: AsrAudioFormat
    language: str = "zh-CN"
    duration_ms: int | None = None
    prompt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AsrProviderResult(BaseModel):
    transcript: str
    provider: AsrProviderName
    model: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    duration_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAsrProvider(ABC):
    def __init__(
        self,
        *,
        provider_name: AsrProviderName,
        enabled: bool = True,
    ) -> None:
        self.provider_name = provider_name
        self.enabled = enabled

    @abstractmethod
    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        raise NotImplementedError
