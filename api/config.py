"""API settings, read from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local-development default (same values as docker-compose.yml and .env.example).
DEFAULT_DATABASE_URL = "postgresql+psycopg://asistente:asistente_local@localhost:5432/asistente"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore", populate_by_name=True)

    name: str = "asistente-patrimonial"
    version: str = "0.1.0"
    environment: str = "local"
    # Read from DATABASE_URL (no APP_ prefix), as set by docker-compose.yml.
    database_url: str = Field(default=DEFAULT_DATABASE_URL, validation_alias="DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
