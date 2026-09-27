import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int
    index: int


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def chunk_pages(pages: list[str], size: int = 900, overlap: int = 150) -> list[Chunk]:
    """Split page texts into overlapping chunks that respect sentence boundaries.

    Chunks never span pages, so every chunk can be cited with a single page number.
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    chunks: list[Chunk] = []
    for page_number, raw in enumerate(pages, start=1):
        text = re.sub(r"\s+", " ", raw).strip()
        if not text:
            continue
        current = ""
        for sentence in _split_sentences(text):
            # Very long sentences (tables, code) are hard-split.
            while len(sentence) > size:
                head, sentence = sentence[:size], sentence[size - overlap :]
                if current:
                    chunks.append(Chunk(current, page_number, len(chunks)))
                    current = ""
                chunks.append(Chunk(head, page_number, len(chunks)))
            if len(current) + len(sentence) + 1 <= size:
                current = f"{current} {sentence}".strip()
            else:
                chunks.append(Chunk(current, page_number, len(chunks)))
                tail = current[-overlap:] if overlap else ""
                # Start the overlap at a word boundary.
                tail = tail[tail.find(" ") + 1 :] if " " in tail else tail
                current = f"{tail} {sentence}".strip()
        if current:
            chunks.append(Chunk(current, page_number, len(chunks)))
    return chunks
