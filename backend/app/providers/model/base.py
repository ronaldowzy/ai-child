from abc import ABC, abstractmethod

from app.domain.model_types import ModelProfile, ModelRequest, ModelResponse


class ModelProviderError(RuntimeError):
    """Base error for model provider failures that can trigger fallback."""


class ModelProviderDisabledError(ModelProviderError):
    pass


class ModelProviderTimeoutError(ModelProviderError):
    pass


class ModelProviderConfigurationError(ModelProviderError):
    pass


class BaseModelProvider(ABC):
    def __init__(self, *, provider_name: str, enabled: bool = True) -> None:
        self.provider_name = provider_name
        self.enabled = enabled

    @abstractmethod
    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        raise NotImplementedError
