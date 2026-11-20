from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal
from pydantic import SecretStr


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
    guard_model: str = "meta-llama/llama-prompt-guard-2-86m"
    guard_timeout_seconds: float = 5.0
    policy_path: str = "policies/default.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
