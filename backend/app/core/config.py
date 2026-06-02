from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Child AI Growth Agent Backend"
    api_v1_prefix: str = "/api/v1"
    environment: str = "dev"
    model_provider: str = "mimo"
    vision_provider: str = "mimo"
    mimo_enabled: bool = False
    mimo_api_key: str = ""
    mimo_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    mimo_model: str = "mimo-v2.5-pro"
    mimo_allow_child_data: bool = False
    mimo_allow_image: bool = False
    mimo_retention_policy_checked: bool = False
    tts_provider: str = "mimo"
    tts_fallback_provider: str = ""
    tts_enable_local_fallback: bool = False
    conversation_tts_enabled: bool = False
    mimo_tts_enabled: bool = False
    mimo_tts_api_key: str = ""
    mimo_tts_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    mimo_tts_model: str = "mimo-v2.5-tts-voiceclone"
    mimo_tts_timeout_ms: int = 30000
    conversation_stream_tts_soft_timeout_ms: int = 15000
    tts_prewarm_enabled: bool = False
    mimo_tts_allow_child_text: bool = False
    mimo_tts_retention_policy_checked: bool = False
    sherpa_onnx_tts_enabled: bool = False
    sherpa_onnx_tts_model_dir: str = (
        "backend/models/tts/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia"
    )
    sherpa_onnx_tts_vocoder_path: str = (
        "backend/models/tts/vocos_24khz.onnx"
    )
    sherpa_onnx_tts_num_threads: int = 2
    sherpa_onnx_tts_num_steps: int = 4
    sherpa_onnx_tts_voice_reference_text: str = ""
    xiaobaihu_voice_sample_path: str = (
        "backend/assets/voices/xiaobaohu_voice_v01.wav"
    )
    tts_cache_dir: str = "backend/storage/tts_cache"
    tts_public_base_url: str = "/media/tts"
    tts_max_text_chars: int = 600
    asr_provider: str = "local_sensevoice"
    asr_fallback_provider: str = "mimo"
    local_sensevoice_enabled: bool = False
    local_sensevoice_model_path: str = (
        "backend/models/asr/sensevoice/model.int8.onnx"
    )
    local_sensevoice_tokens_path: str = "backend/models/asr/sensevoice/tokens.txt"
    local_sensevoice_num_threads: int = 4
    local_sensevoice_use_itn: bool = True
    local_sensevoice_language: str = "zh"
    mimo_asr_enabled: bool = False
    mimo_asr_api_key: str = ""
    mimo_asr_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    mimo_asr_model: str = "mimo-v2.5"
    mimo_asr_timeout_ms: int = 30000
    mimo_asr_allow_child_audio: bool = False
    mimo_asr_retention_policy_checked: bool = False
    mimo_asr_no_training_confirmed: bool = False
    database_url: str = (
        "postgresql+psycopg://child_ai:child_ai@localhost:5432/child_ai_dev"
    )
    model_debug_trace_full_text: bool = True
    model_debug_trace_max_text_chars: int = 20000
    allow_mock_runtime: bool = False
    allow_auth_memory_fallback: bool = False
    opening_model_soft_timeout_ms: int = 3000
    opening_tts_soft_timeout_ms: int = 15000

    model_config = SettingsConfigDict(env_prefix="CHILD_AI_", extra="ignore")

    @property
    def effective_mimo_asr_api_key(self) -> str:
        return (
            self.mimo_asr_api_key
            or self.mimo_api_key
            or self.mimo_tts_api_key
        )

    def resolve_repo_path(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return repo_root() / candidate


@lru_cache
def get_settings() -> Settings:
    return Settings()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
