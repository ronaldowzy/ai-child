from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Child AI Growth Agent Backend"
    api_v1_prefix: str = "/api/v1"
    environment: str = "dev"
    tts_provider: str = "mock"
    conversation_tts_enabled: bool = False
    mimo_tts_enabled: bool = False
    mimo_tts_api_key: str = ""
    mimo_tts_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    mimo_tts_model: str = "mimo-v2.5-tts-voiceclone"
    mimo_tts_timeout_ms: int = 30000
    conversation_stream_tts_soft_timeout_ms: int = 8000
    mimo_tts_allow_child_text: bool = False
    mimo_tts_retention_policy_checked: bool = False
    xiaobaihu_voice_sample_path: str = (
        "backend/assets/voices/xiaobaohu_voice_v01.wav"
    )
    tts_cache_dir: str = "backend/storage/tts_cache"
    tts_public_base_url: str = "/media/tts"
    tts_max_text_chars: int = 600
    asr_provider: str = "mock"
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

    model_config = SettingsConfigDict(env_prefix="CHILD_AI_", extra="ignore")

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
