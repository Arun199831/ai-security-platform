import re
import unicodedata

# Zero-width characters and soft hyphens that attackers hide inside words.
INVISIBLE_CHARS = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"))


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(INVISIBLE_CHARS)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
