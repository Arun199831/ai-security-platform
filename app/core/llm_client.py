import logging
from dataclasses import dataclass
from functools import lru_cache

from openai import APIConnectionError, InternalServerError, OpenAI, RateLimitError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Temporary failures where trying the other provider makes sense.
# (APITimeoutError is a subclass of APIConnectionError.)
TRANSIENT_ERRORS = (APIConnectionError, RateLimitError, InternalServerError)


class LLMUnavailableError(Exception):
    """Raised when every model provider failed."""


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        timeout = settings.request_timeout_seconds
        retries = settings.max_retries

        self._providers = [
            (
                "groq",
                settings.primary_model,
                OpenAI(
                    api_key=settings.groq_api_key.get_secret_value(),
                    base_url=GROQ_BASE_URL,
                    timeout=timeout,
                    max_retries=retries,
                ),
            ),
            (
                "openai",
                settings.fallback_model,
                OpenAI(
                    api_key=settings.openai_api_key.get_secret_value(),
                    timeout=timeout,
                    max_retries=retries,
                ),
            ),
        ]

    def generate(
        self, messages: list[dict[str, str]], max_tokens: int = 2048
    ) -> LLMResponse:
        for provider, model, client in self._providers:
            try:
                return self._call(client, provider, model, messages, max_tokens)
            except TRANSIENT_ERRORS as exc:
                logger.warning(
                    "Provider %s failed (%s), trying next", provider, type(exc).__name__
                )

        raise LLMUnavailableError("All model providers failed")

    def _call(
        self,
        client: OpenAI,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> LLMResponse:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        return LLMResponse(text=text, provider=provider, model=model)


@lru_cache
def get_llm_client() -> LLMClient:
    return LLMClient()
