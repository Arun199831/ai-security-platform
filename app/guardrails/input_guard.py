from app.guardrails.classifier import classify_text
from app.guardrails.models import Decision, GuardResult
from app.guardrails.normalize import normalize_text
from app.guardrails.rules import check_rules

MAX_INPUT_CHARS = 4000


def check_input(text: str) -> GuardResult:
    if len(text) > MAX_INPUT_CHARS:
        return GuardResult(
            decision=Decision.BLOCK,
            layer="limits",
            reason="input too long",
        )

    cleaned = normalize_text(text)
    if not cleaned:
        return GuardResult(
            decision=Decision.ALLOW,
            layer="limits",
            reason="empty input",
        )

    rules_result = check_rules(cleaned)
    if not rules_result.allowed:
        return rules_result

    return classify_text(cleaned)
