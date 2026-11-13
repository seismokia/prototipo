"""API settings, read from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")

    name: str = "asistente-patrimonial"
    version: str = "0.1.0"
    environment: str = "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
