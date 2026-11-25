from functools import lru_cache
from pathlib import Path

from app.guardrails.classifier import ClassifierUnavailableError
from app.guardrails.leak import leaks_marker
from app.guardrails.models import Decision, GuardResult, most_severe
from app.guardrails.normalize import normalize_text
from app.guardrails.output_classifier import classify_output
from app.guardrails.output_rules import find_secrets
from app.guardrails.policy import OutputClassifierPolicy, Policy, RuleAction


def check_output(text: str, policy: Policy, marker: str | None = None) -> GuardResult:
    output = policy.output
    if len(text) > output.max_chars:
        return GuardResult(Decision.BLOCK, "limits", "output too long")

    text = normalize_text(text)
    if not text:
        return GuardResult(Decision.ALLOW, "normalize", "empty output")

    cheap_results = [
        _check_secrets(text, output.secrets),
        _check_marker(text, marker, output.marker_leak),
    ]
    for result in cheap_results:
        if result.decision == Decision.BLOCK:
            return result

    classifier_result = _check_safety(text, output.classifier)
    return most_severe(classifier_result, *cheap_results)


def _check_secrets(text: str, action: RuleAction) -> GuardResult:
    found = find_secrets(text)
    if not found or action == "off":
        return GuardResult(Decision.ALLOW, "secrets", "no secrets found")
    reason = f"secret patterns found: {', '.join(found)}"
    return GuardResult(_decision_for(action), "secrets", reason)


def _check_marker(text: str, marker: str | None, action: RuleAction) -> GuardResult:
    if marker is None or action == "off" or not leaks_marker(text, marker):
        return GuardResult(Decision.ALLOW, "marker", "no marker leak")
    return GuardResult(
        _decision_for(action), "marker", "system prompt marker found in output"
    )


def _check_safety(text: str, classifier: OutputClassifierPolicy) -> GuardResult:
    try:
        verdict = classify_output(
            text, _load_safety_text(classifier.safety_policy_file)
        )
    except ClassifierUnavailableError:
        return _classifier_failure(classifier)

    if not verdict.violation:
        return GuardResult(Decision.ALLOW, "classifier", "no unsafe content found")

    category = verdict.category or "unknown"
    # Look the category up in the policy's own fields only; unknown categories block.
    action = classifier.categories.model_dump().get(category, "block")
    return GuardResult(
        _decision_for(action), "classifier", f"unsafe output: {category}"
    )


def _classifier_failure(classifier: OutputClassifierPolicy) -> GuardResult:
    if classifier.on_failure == "block":
        return GuardResult(
            Decision.BLOCK, "classifier", "safety check unavailable, failing closed"
        )
    return GuardResult(
        Decision.FLAG, "classifier", "safety check unavailable, passed unscreened"
    )


def _decision_for(action: RuleAction) -> Decision:
    if action == "block":
        return Decision.BLOCK
    if action == "flag":
        return Decision.FLAG
    return Decision.ALLOW


@lru_cache
def _load_safety_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")
