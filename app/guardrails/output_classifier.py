import logging
from functools import lru_cache
from typing import Literal

from openai import APIError, OpenAI
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings
from app.core.llm_client import GROQ_BASE_URL
from app.guardrails.classifier import ClassifierUnavailableError

logger = logging.getLogger(__name__)
CLOSING_TAG = "</assistant_reply>"


class SafetyVerdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    violation: Literal[0, 1]
    category: str | None = None
    rationale: str = ""


def classify_output(text: str, policy_text: str) -> SafetyVerdict:
    settings = get_settings()
    # Remove our closing tag from the reply so it can't break out of the wrapper.
    wrapped = f"<assistant_reply>\n{text.replace(CLOSING_TAG, '')}\n{CLOSING_TAG}"
    try:
        response = _get_client().chat.completions.create(
            model=settings.output_guard_model,
            messages=[
                {"role": "system", "content": policy_text},
                {"role": "user", "content": wrapped},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2048,
        )
        return SafetyVerdict.model_validate_json(
            response.choices[0].message.content or ""
        )
    except (APIError, ValueError) as exc:
        logger.warning("output classifier failed: %s", type(exc).__name__)
        raise ClassifierUnavailableError("output classifier unavailable") from exc


@lru_cache
def _get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.groq_api_key.get_secret_value(),
        base_url=GROQ_BASE_URL,
        timeout=settings.output_guard_timeout_seconds,
        max_retries=1,
    )
