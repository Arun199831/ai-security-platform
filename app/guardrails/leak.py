import secrets
from functools import lru_cache

from app.guardrails.normalize import normalize_text


@lru_cache
def get_marker() -> str:
    return f"marker-{secrets.token_hex(8)}"


def leaks_marker(text: str, marker: str) -> bool:
    return marker.lower() in normalize_text(text).lower()
