import logging
from functools import lru_cache

from openai import APIError, OpenAI

from app.core.config import get_settings
from app.core.llm_client import GROQ_BASE_URL
from app.guardrails.chunking import split_into_chunks
from app.guardrails.models import Decision, GuardResult

logger = logging.getLogger(__name__)


def classify_text(text: str) -> GuardResult:
    settings = get_settings()
    highest_score = 0.0

    try:
        for chunk in split_into_chunks(text):
            highest_score = max(highest_score, _score_chunk(chunk))
            if highest_score >= settings.injection_threshold:
                break
    except (APIError, ValueError) as exc:
        return _classifier_unavailable(exc)

    if highest_score >= settings.injection_threshold:
        return GuardResult(
            decision=Decision.BLOCK,
            layer="classifier",
            reason="prompt attack detected",
            score=highest_score,
        )

    return GuardResult(
        decision=Decision.ALLOW,
        layer="classifier",
        reason="score below threshold",
        score=highest_score,
    )


def _score_chunk(chunk: str) -> float:
    response = _get_client().chat.completions.create(
        model=get_settings().guard_model,
        messages=[{"role": "user", "content": chunk}],
    )
    content = response.choices[0].message.content or ""
    return float(content)


def _classifier_unavailable(exc: Exception) -> GuardResult:
    logger.warning("Classifier unavailable (%s)", type(exc).__name__)

    if get_settings().guard_fail_closed:
        return GuardResult(
            decision=Decision.BLOCK,
            layer="error",
            reason="classifier unavailable, failing closed",
        )
    return GuardResult(
        decision=Decision.ALLOW,
        layer="error",
        reason="classifier unavailable, failing open",
    )


@lru_cache
def _get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.groq_api_key.get_secret_value(),
        base_url=GROQ_BASE_URL,
        timeout=settings.guard_timeout_seconds,
        max_retries=1,
    )
