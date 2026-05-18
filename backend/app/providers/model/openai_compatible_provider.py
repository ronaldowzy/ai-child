import os

from app.domain.model_types import ModelProfile, ModelRequest, ModelResponse
from app.providers.model.base import (
    BaseModelProvider,
    ModelProviderConfigurationError,
    ModelProviderDisabledError,
)


class OpenAICompatibleProvider(BaseModelProvider):
    def __init__(
        self,
        *,
        provider_name: str = "openai_compatible",
        base_url_env: str | None = None,
        api_key_env: str | None = None,
        model_name_env: str | None = None,
        enabled: bool = False,
    ) -> None:
        super().__init__(provider_name=provider_name, enabled=enabled)
        self.base_url_env = base_url_env
        self.api_key_env = api_key_env
        self.model_name_env = model_name_env

    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        if not self.enabled:
            raise ModelProviderDisabledError(
                f"Provider {self.provider_name} is disabled"
            )

        self._validate_environment()
        raise ModelProviderConfigurationError(
            "OpenAICompatibleProvider is an interface skeleton only in v0.1"
        )

    def _validate_environment(self) -> None:
        missing = [
            env_name
            for env_name in (self.base_url_env, self.api_key_env, self.model_name_env)
            if env_name and not os.getenv(env_name)
        ]
        if missing:
            raise ModelProviderConfigurationError(
                f"Missing required model environment variables: {', '.join(missing)}"
            )
