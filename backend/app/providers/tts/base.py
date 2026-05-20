from abc import ABC, abstractmethod

from app.domain.tts import TtsProviderRequest, TtsProviderResult


class TtsProviderError(RuntimeError):
    pass


class TtsProviderConfigurationError(TtsProviderError):
    pass


class TtsProviderTimeoutError(TtsProviderError):
    pass


class BaseTtsProvider(ABC):
    def __init__(self, *, provider_name: str, enabled: bool = True) -> None:
        self.provider_name = provider_name
        self.enabled = enabled

    @abstractmethod
    def generate(self, request: TtsProviderRequest) -> TtsProviderResult:
        raise NotImplementedError
