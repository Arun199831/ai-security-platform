from app.guardrails.classifier import ClassifierUnavailableError, score_text
from app.guardrails.models import Decision, GuardResult
from app.guardrails.normalize import normalize_text
from app.guardrails.policy import ClassifierPolicy, Policy, RulesPolicy
from app.guardrails.rules import find_matching_rules

SEVERITY = {Decision.ALLOW: 0, Decision.FLAG: 1, Decision.BLOCK: 2}


def check_input(text: str, policy: Policy) -> GuardResult:
    settings = policy.input

    if len(text) > settings.max_chars:
        return GuardResult(
            decision=Decision.BLOCK, layer="limits", reason="input too long"
        )

    cleaned = normalize_text(text)
    if not cleaned:
        return GuardResult(
            decision=Decision.ALLOW, layer="limits", reason="empty input"
        )

    rules_result = _apply_rules(cleaned, settings.rules)
    if rules_result.decision == Decision.BLOCK:
        return rules_result

    classifier_result = _apply_classifier(cleaned, settings.classifier)
    # Classifier first, so on a tie its score is kept in the final result.
    return _most_severe(classifier_result, rules_result)


def _apply_rules(text: str, rules: RulesPolicy) -> GuardResult:
    decision = Decision.ALLOW
    triggered = []

    for name in find_matching_rules(text):
        action = getattr(rules, name, "block")  # rule missing from policy: fail safe
        if action == "off":
            continue
        triggered.append(name)
        if action == "block":
            decision = Decision.BLOCK
        elif decision != Decision.BLOCK:
            decision = Decision.FLAG

    reason = (
        f"matched rules: {', '.join(triggered)}" if triggered else "no rule matched"
    )
    return GuardResult(decision=decision, layer="rules", reason=reason)


def _apply_classifier(text: str, policy: ClassifierPolicy) -> GuardResult:
    try:
        score = score_text(text, stop_at=policy.block_threshold)
    except ClassifierUnavailableError:
        return _classifier_failure(policy)

    if score >= policy.block_threshold:
        return GuardResult(
            decision=Decision.BLOCK,
            layer="classifier",
            reason="prompt attack detected",
            score=score,
        )
    if score >= policy.flag_threshold:
        return GuardResult(
            decision=Decision.FLAG,
            layer="classifier",
            reason="suspicious input, flagged for review",
            score=score,
        )
    return GuardResult(
        decision=Decision.ALLOW,
        layer="classifier",
        reason="score below thresholds",
        score=score,
    )


def _classifier_failure(policy: ClassifierPolicy) -> GuardResult:
    if policy.on_failure == "block":
        return GuardResult(
            decision=Decision.BLOCK,
            layer="error",
            reason="classifier unavailable, failing closed",
        )
    return GuardResult(
        decision=Decision.FLAG,
        layer="error",
        reason="classifier unavailable, passed unscreened",
    )


def _most_severe(*results: GuardResult) -> GuardResult:
    return max(results, key=lambda result: SEVERITY[result.decision])
