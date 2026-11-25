from app.guardrails.classifier import ClassifierUnavailableError, score_text
from app.guardrails.models import Decision, GuardResult, most_severe
from app.guardrails.normalize import normalize_text
from app.guardrails.policy import ClassifierPolicy, Policy, RulesPolicy
from app.guardrails.rules import find_matching_rules


def check_input(text: str, policy: Policy) -> GuardResult:
    if len(text) > policy.input.max_chars:
        return GuardResult(Decision.BLOCK, "limits", "input too long")

    text = normalize_text(text)
    if not text:
        return GuardResult(Decision.ALLOW, "normalize", "empty input")

    rules_result = _apply_rules(text, policy.input.rules)
    if rules_result.decision == Decision.BLOCK:
        return rules_result

    classifier_result = _apply_classifier(text, policy.input.classifier)
    return most_severe(classifier_result, rules_result)


def _apply_rules(text: str, rules: RulesPolicy) -> GuardResult:
    blocked = []
    flagged = []
    for name in find_matching_rules(text):
        action = getattr(rules, name, "block")
        if action == "block":
            blocked.append(name)
        elif action == "flag":
            flagged.append(name)
    if blocked:
        return GuardResult(
            Decision.BLOCK, "rules", f"matched rules: {', '.join(blocked)}"
        )
    if flagged:
        return GuardResult(
            Decision.FLAG, "rules", f"flagged rules: {', '.join(flagged)}"
        )
    return GuardResult(Decision.ALLOW, "rules", "no rules matched")


def _apply_classifier(text: str, classifier: ClassifierPolicy) -> GuardResult:
    try:
        score = score_text(text, stop_at=classifier.block_threshold)
    except ClassifierUnavailableError:
        return _classifier_failure(classifier)

    if score >= classifier.block_threshold:
        return GuardResult(
            Decision.BLOCK, "classifier", "prompt attack detected", score
        )
    if score >= classifier.flag_threshold:
        return GuardResult(
            Decision.FLAG, "classifier", "suspicious input, flagged for review", score
        )
    return GuardResult(Decision.ALLOW, "classifier", "score below thresholds", score)


def _classifier_failure(classifier: ClassifierPolicy) -> GuardResult:
    if classifier.on_failure == "block":
        return GuardResult(
            Decision.BLOCK, "classifier", "classifier unavailable, failing closed"
        )
    return GuardResult(
        Decision.FLAG, "classifier", "classifier unavailable, passed unscreened"
    )
