from app.services.store import RetrievedChunk

SYSTEM_PROMPT = """You are DocuChat, an assistant that answers questions about the user's documents.

Rules:
- Answer ONLY with information from the numbered context passages.
- Cite the passages you use with their number in brackets, e.g. [1] or [2][3].
- If the context does not contain the answer, say you could not find it in the documents.
- Answer in the same language as the question. Be concise; use lists when helpful.
"""

MAX_HISTORY_MESSAGES = 6


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no relevant passages were found)"
    return "\n\n".join(
        f"[{number}] ({chunk.filename}, page {chunk.page})\n{chunk.text}"
        for number, chunk in enumerate(chunks, start=1)
    )


def build_messages(
    question: str, chunks: list[RetrievedChunk], history: list[dict[str, str]] | None = None
) -> list[dict[str, str]]:
    """System prompt + recent conversation + the question grounded in retrieved context."""
    recent = [
        {"role": m["role"], "content": m["content"][:2000]}
        for m in (history or [])[-MAX_HISTORY_MESSAGES:]
        if m.get("role") in {"user", "assistant"}
    ]
    user = f"Context:\n{format_context(chunks)}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *recent,
        {"role": "user", "content": user},
    ]
