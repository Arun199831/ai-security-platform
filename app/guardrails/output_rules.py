import re

SECRET_RULES = [
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("groq_key", re.compile(r"\bgsk_[A-Za-z0-9]{20,}")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "private_key_block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
]


def find_secrets(text: str) -> list[str]:
    return [name for name, pattern in SECRET_RULES if pattern.search(text)]
