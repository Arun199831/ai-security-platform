import re


# Rule names go in the audit log. The user only ever sees a generic message.
INJECTION_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignore_instructions",
        re.compile(
            r"\b(ignore|disregard|forget)\s+((all|any|your|the|my)\s+)*"
            r"(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reveal_system_prompt",
        re.compile(
            r"\b(reveal|show|print|repeat|output|leak)\b.{0,40}"
            r"\b(system|hidden|initial)\s+(prompt|instructions?|message)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "role_override",
        re.compile(
            r"\b(you are now|pretend to be|from now on you)\b.{0,40}"
            r"\b(unrestricted|no restrictions|do anything now|"
            r"without (any )?(rules|filters|limits|restrictions))\b",
            re.IGNORECASE,
        ),
    ),
]


def find_matching_rules(text: str) -> list[str]:
    return [name for name, pattern in INJECTION_RULES if pattern.search(text)]
