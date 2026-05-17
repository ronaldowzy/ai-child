from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Child AI Growth Agent Backend"
    api_v1_prefix: str = "/api/v1"
    environment: str = "dev"

    model_config = SettingsConfigDict(env_prefix="CHILD_AI_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
