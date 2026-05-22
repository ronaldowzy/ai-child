from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelTaskType(StrEnum):
    CHILD_CHAT = "child_chat"
    INTENT_CLASSIFICATION = "intent_classification"
    SAFETY_CLASSIFICATION = "safety_classification"
    MEMORY_EXTRACTION = "memory_extraction"
    PARENT_REPORT = "parent_report"
    VISION = "vision"
    OCR = "ocr"


class ModelProviderType(StrEnum):
    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai_compatible"


class ModelMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]]


class ModelRequest(BaseModel):
    task_type: ModelTaskType
    messages: list[ModelMessage] = Field(default_factory=list)
    input_text: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    task_type: ModelTaskType
    response_text: str
    structured_output: dict[str, Any] = Field(default_factory=dict)
    provider_name: str
    model_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelCapabilities(BaseModel):
    text: bool = True
    vision: bool = False
    structured_output: bool = True
    tool_calling: bool = False
    embedding: bool = False
    audio_input: bool = False
    audio_output: bool = False


class ModelDataPolicy(BaseModel):
    allow_child_data: bool = False
    allow_image: bool = False
    allow_audio: bool = False
    external_transmission: bool = False
    retention_policy_checked: bool = False


class ModelDefaultParams(BaseModel):
    temperature: float = 0.0
    max_tokens: int = 800
    timeout_ms: int = 5000


class ModelProfile(BaseModel):
    id: str
    profile_name: str
    provider_name: str
    provider_type: ModelProviderType = ModelProviderType.MOCK
    model_name: str
    task_type: ModelTaskType
    capabilities: ModelCapabilities = Field(default_factory=ModelCapabilities)
    data_policy: ModelDataPolicy = Field(default_factory=ModelDataPolicy)
    default_params: ModelDefaultParams = Field(default_factory=ModelDefaultParams)
    enabled: bool = True
    fallback_profile_name: str | None = None
