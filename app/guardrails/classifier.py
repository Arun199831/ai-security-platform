import logging
from functools import lru_cache

from openai import APIError, OpenAI

from app.core.config import get_settings
from app.core.llm_client import GROQ_BASE_URL
from app.guardrails.chunking import split_into_chunks

logger = logging.getLogger(__name__)


class ClassifierUnavailableError(Exception):
    """Raised when the classifier cannot produce a usable score."""


def score_text(text: str, stop_at: float = 1.0) -> float:
    highest_score = 0.0

    try:
        for chunk in split_into_chunks(text):
            highest_score = max(highest_score, _score_chunk(chunk))
            if highest_score >= stop_at:
                break
    except (APIError, ValueError) as exc:
        logger.warning("Classifier unavailable (%s)", type(exc).__name__)
        raise ClassifierUnavailableError from exc

    return highest_score


def _score_chunk(chunk: str) -> float:
    response = _get_client().chat.completions.create(
        model=get_settings().guard_model,
        messages=[{"role": "user", "content": chunk}],
    )
    content = response.choices[0].message.content or ""
    return float(content)


@lru_cache
def _get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.groq_api_key.get_secret_value(),
        base_url=GROQ_BASE_URL,
        timeout=settings.guard_timeout_seconds,
        max_retries=1,
    )
