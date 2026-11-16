from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: SecretStr
    openai_api_key: SecretStr
    app_env: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    primary_model: str = "openai/gpt-oss-120b"
    fallback_model: str = "gpt-5-mini"
    request_timeout_seconds: float = 30.0
    max_retries: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
