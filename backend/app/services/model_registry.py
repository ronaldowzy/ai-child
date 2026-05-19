from collections.abc import Mapping
import os

from app.domain.model_types import (
    ModelCapabilities,
    ModelDataPolicy,
    ModelDefaultParams,
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.providers.model.base import (
    BaseModelProvider,
    ModelProviderDisabledError,
    ModelProviderError,
)
from app.providers.model.mock_provider import MockModelProvider
from app.providers.model.openai_compatible_provider import OpenAICompatibleProvider
from app.services.model_data_policy_guard import (
    ModelDataPolicyBlockedError,
    ModelDataPolicyGuard,
)


class ModelRegistryError(RuntimeError):
    pass


class ModelProfileNotFoundError(ModelRegistryError):
    pass


class ModelProviderNotFoundError(ModelRegistryError):
    pass


class ModelRegistry:
    def __init__(
        self,
        *,
        providers: Mapping[str, BaseModelProvider] | None = None,
        profiles: Mapping[str, ModelProfile] | None = None,
        task_profile_map: Mapping[ModelTaskType | str, str] | None = None,
        data_policy_guard: ModelDataPolicyGuard | None = None,
    ) -> None:
        self._providers = dict(providers or self._default_providers())
        self._profiles = dict(profiles or self._default_profiles())
        self._task_profile_map = self._normalize_task_profile_map(
            task_profile_map or self._default_task_profile_map()
        )
        self._data_policy_guard = data_policy_guard or ModelDataPolicyGuard()

    def select(self, task_type: ModelTaskType | str) -> BaseModelProvider:
        profile = self.select_profile(task_type)
        return self._provider_for_profile(profile)

    def select_profile(self, task_type: ModelTaskType | str) -> ModelProfile:
        normalized_task_type = ModelTaskType(task_type)
        profile_name = self._task_profile_map.get(normalized_task_type)
        if not profile_name:
            raise ModelProfileNotFoundError(
                f"No model profile configured for task_type={normalized_task_type}"
            )

        profile = self._get_profile(profile_name)
        try:
            self._provider_for_profile(profile)
        except (ModelProviderDisabledError, ModelRegistryError):
            fallback_profile = self._fallback_profile_for(profile, normalized_task_type)
            if fallback_profile is None:
                raise
            return fallback_profile
        return profile

    def generate(self, request: ModelRequest) -> ModelResponse:
        primary_profile = self._get_primary_profile(request.task_type)
        try:
            provider = self._provider_for_profile(primary_profile)
            self._data_policy_guard.validate(
                request=request,
                profile=primary_profile,
            )
            return provider.generate(request, profile=primary_profile)
        except ModelDataPolicyBlockedError as exc:
            fallback_profile = self._mock_fallback_profile_for(
                primary_profile, request.task_type
            )
            if fallback_profile is None:
                raise ModelRegistryError(
                    "Model data policy blocked provider call without an enabled "
                    f"mock fallback: {exc}"
                ) from exc

            fallback_provider = self._provider_for_profile(fallback_profile)
            response = fallback_provider.generate(request, profile=fallback_profile)
            response.metadata.update(
                {
                    "fallback_used": True,
                    "policy_blocked": True,
                    "failed_profile": primary_profile.profile_name,
                    "failed_provider": primary_profile.provider_name,
                    "failure_type": exc.__class__.__name__,
                }
            )
            return response
        except (ModelProviderError, ModelRegistryError) as exc:
            fallback_profile = self._fallback_profile_for(
                primary_profile, request.task_type
            )
            if fallback_profile is None:
                raise ModelRegistryError(
                    f"Model generation failed without fallback: {exc}"
                ) from exc

            fallback_provider = self._provider_for_profile(fallback_profile)
            response = fallback_provider.generate(request, profile=fallback_profile)
            response.metadata.update(
                {
                    "fallback_used": True,
                    "failed_profile": primary_profile.profile_name,
                    "failed_provider": primary_profile.provider_name,
                    "failure_type": exc.__class__.__name__,
                }
            )
            return response

    def _get_primary_profile(self, task_type: ModelTaskType | str) -> ModelProfile:
        normalized_task_type = ModelTaskType(task_type)
        profile_name = self._task_profile_map.get(normalized_task_type)
        if not profile_name:
            raise ModelProfileNotFoundError(
                f"No model profile configured for task_type={normalized_task_type}"
            )
        return self._get_profile(profile_name)

    def _get_profile(self, profile_name: str) -> ModelProfile:
        profile = self._profiles.get(profile_name)
        if profile is None:
            raise ModelProfileNotFoundError(
                f"Model profile {profile_name} is not registered"
            )
        return profile

    def _provider_for_profile(self, profile: ModelProfile) -> BaseModelProvider:
        if not profile.enabled:
            raise ModelProviderDisabledError(
                f"Model profile {profile.profile_name} is disabled"
            )

        provider = self._providers.get(profile.provider_name)
        if provider is None:
            raise ModelProviderNotFoundError(
                f"Provider {profile.provider_name} is not registered"
            )
        if not provider.enabled:
            raise ModelProviderDisabledError(
                f"Provider {provider.provider_name} is disabled"
            )
        return provider

    def _fallback_profile_for(
        self, profile: ModelProfile, task_type: ModelTaskType
    ) -> ModelProfile | None:
        if profile.fallback_profile_name:
            fallback = self._profiles.get(profile.fallback_profile_name)
            if fallback is not None and fallback.enabled:
                return fallback

        mock_profile_name = self._default_task_profile_map().get(task_type)
        if mock_profile_name and mock_profile_name != profile.profile_name:
            fallback = self._profiles.get(mock_profile_name)
            if fallback is not None and fallback.enabled:
                return fallback
        return None

    def _mock_fallback_profile_for(
        self, profile: ModelProfile, task_type: ModelTaskType
    ) -> ModelProfile | None:
        if profile.fallback_profile_name:
            fallback = self._enabled_mock_profile(profile.fallback_profile_name)
            if fallback is not None:
                return fallback

        mock_profile_name = self._default_task_profile_map().get(task_type)
        if mock_profile_name and mock_profile_name != profile.profile_name:
            return self._enabled_mock_profile(mock_profile_name)
        return None

    def _enabled_mock_profile(self, profile_name: str) -> ModelProfile | None:
        profile = self._profiles.get(profile_name)
        if (
            profile is None
            or not profile.enabled
            or profile.provider_type != ModelProviderType.MOCK
        ):
            return None

        provider = self._providers.get(profile.provider_name)
        if provider is None or not provider.enabled:
            return None
        return profile

    def _normalize_task_profile_map(
        self, task_profile_map: Mapping[ModelTaskType | str, str]
    ) -> dict[ModelTaskType, str]:
        return {
            ModelTaskType(task_type): profile_name
            for task_type, profile_name in task_profile_map.items()
        }

    def _default_providers(self) -> dict[str, BaseModelProvider]:
        return {
            "mock": MockModelProvider(provider_name="mock"),
            "mimo": OpenAICompatibleProvider(
                provider_name="mimo",
                base_url_env="CHILD_AI_MIMO_BASE_URL",
                api_key_env="CHILD_AI_MIMO_API_KEY",
                model_name_env="CHILD_AI_MIMO_MODEL",
                default_base_url="https://token-plan-cn.xiaomimimo.com/v1",
                default_model_name="mimo-v2.5pro",
                enabled=self._env_bool("CHILD_AI_MIMO_ENABLED", default=False),
            ),
        }

    def _default_task_profile_map(self) -> dict[ModelTaskType, str]:
        child_chat_profile = os.getenv("CHILD_AI_CHILD_CHAT_PROFILE")
        if not child_chat_profile and os.getenv("CHILD_AI_MODEL_PROVIDER") == "mimo":
            child_chat_profile = "mimo_child_chat"

        return {
            ModelTaskType.CHILD_CHAT: child_chat_profile or "child_chat_primary",
            ModelTaskType.INTENT_CLASSIFICATION: "intent_classifier_mock",
            ModelTaskType.SAFETY_CLASSIFICATION: "safety_classifier_mock",
            ModelTaskType.MEMORY_EXTRACTION: "memory_extractor_mock",
            ModelTaskType.PARENT_REPORT: "parent_report_mock",
            ModelTaskType.VISION: "vision_mock",
            ModelTaskType.OCR: "ocr_mock",
        }

    def _default_profiles(self) -> dict[str, ModelProfile]:
        return {
            "child_chat_primary": self._mock_profile(
                profile_name="child_chat_primary",
                model_name="mock-child-chat-v0",
                task_type=ModelTaskType.CHILD_CHAT,
                temperature=0.4,
            ),
            "mimo_child_chat": self._mimo_profile(
                profile_name="mimo_child_chat",
                model_name=os.getenv("CHILD_AI_MIMO_MODEL", "mimo-v2.5pro"),
                task_type=ModelTaskType.CHILD_CHAT,
                temperature=0.4,
            ),
            "intent_classifier_mock": self._mock_profile(
                profile_name="intent_classifier_mock",
                model_name="mock-intent-classifier-v0",
                task_type=ModelTaskType.INTENT_CLASSIFICATION,
            ),
            "safety_classifier_mock": self._mock_profile(
                profile_name="safety_classifier_mock",
                model_name="mock-safety-classifier-v0",
                task_type=ModelTaskType.SAFETY_CLASSIFICATION,
            ),
            "memory_extractor_mock": self._mock_profile(
                profile_name="memory_extractor_mock",
                model_name="mock-memory-extractor-v0",
                task_type=ModelTaskType.MEMORY_EXTRACTION,
            ),
            "parent_report_mock": self._mock_profile(
                profile_name="parent_report_mock",
                model_name="mock-parent-report-v0",
                task_type=ModelTaskType.PARENT_REPORT,
            ),
            "vision_mock": self._mock_profile(
                profile_name="vision_mock",
                model_name="mock-vision-v0",
                task_type=ModelTaskType.VISION,
                vision=True,
            ),
            "ocr_mock": self._mock_profile(
                profile_name="ocr_mock",
                model_name="mock-ocr-v0",
                task_type=ModelTaskType.OCR,
                vision=True,
            ),
        }

    def _mimo_profile(
        self,
        *,
        profile_name: str,
        model_name: str,
        task_type: ModelTaskType,
        temperature: float = 0.0,
    ) -> ModelProfile:
        return ModelProfile(
            id=profile_name,
            profile_name=profile_name,
            provider_name="mimo",
            provider_type=ModelProviderType.OPENAI_COMPATIBLE,
            model_name=model_name,
            task_type=task_type,
            capabilities=ModelCapabilities(),
            data_policy=ModelDataPolicy(
                allow_child_data=self._env_bool(
                    "CHILD_AI_MIMO_ALLOW_CHILD_DATA", default=False
                ),
                allow_image=self._env_bool(
                    "CHILD_AI_MIMO_ALLOW_IMAGE", default=False
                ),
                allow_audio=self._env_bool(
                    "CHILD_AI_MIMO_ALLOW_AUDIO", default=False
                ),
                external_transmission=True,
                retention_policy_checked=self._env_bool(
                    "CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", default=False
                ),
            ),
            default_params=ModelDefaultParams(
                temperature=temperature,
                max_tokens=int(os.getenv("CHILD_AI_MIMO_MAX_TOKENS", "800")),
                timeout_ms=int(os.getenv("CHILD_AI_MIMO_TIMEOUT_MS", "5000")),
            ),
            enabled=self._env_bool("CHILD_AI_MIMO_ENABLED", default=False),
            fallback_profile_name="child_chat_primary",
        )

    def _mock_profile(
        self,
        *,
        profile_name: str,
        model_name: str,
        task_type: ModelTaskType,
        temperature: float = 0.0,
        vision: bool = False,
    ) -> ModelProfile:
        return ModelProfile(
            id=profile_name,
            profile_name=profile_name,
            provider_name="mock",
            provider_type=ModelProviderType.MOCK,
            model_name=model_name,
            task_type=task_type,
            capabilities=ModelCapabilities(vision=vision),
            data_policy=ModelDataPolicy(
                allow_child_data=True,
                allow_image=vision,
                allow_audio=False,
                external_transmission=False,
                retention_policy_checked=True,
            ),
            default_params=ModelDefaultParams(
                temperature=temperature,
                max_tokens=800,
                timeout_ms=3000,
            ),
        )

    def _env_bool(self, env_name: str, *, default: bool) -> bool:
        raw_value = os.getenv(env_name)
        if raw_value is None:
            return default
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}


_model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    return _model_registry
