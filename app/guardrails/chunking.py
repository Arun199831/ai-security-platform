CHUNK_CHARS = 1000
OVERLAP_CHARS = 150


def split_into_chunks(text: str) -> list[str]:
    chunks = []
    start = 0

    while start < len(text):
        chunks.append(text[start : start + CHUNK_CHARS])
        if start + CHUNK_CHARS >= len(text):
            break
        start += CHUNK_CHARS - OVERLAP_CHARS

    return chunks
