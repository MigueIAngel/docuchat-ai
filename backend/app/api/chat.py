import json
import logging
from collections.abc import Iterator
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.deps import LLMDep, SettingsDep, StoreDep
from app.services.rag import build_messages

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[str] | None = None
    history: list[HistoryMessage] = []


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
def chat(request: ChatRequest, store: StoreDep, llm: LLMDep, settings: SettingsDep):
    """Answer a question about the documents as a Server-Sent Events stream.

    Events: `sources` (retrieved passages), `token` (answer deltas), `done` or `error`.
    """

    def events() -> Iterator[str]:
        try:
            [query_vector] = llm.embed([request.question], "query")
            chunks = store.search(query_vector, settings.top_k, request.document_ids)
            yield sse(
                "sources",
                [
                    {
                        "id": number,
                        "document_id": c.document_id,
                        "filename": c.filename,
                        "page": c.page,
                        "score": c.score,
                        "text": c.text,
                    }
                    for number, c in enumerate(chunks, start=1)
                ],
            )
            messages = build_messages(
                request.question, chunks, [m.model_dump() for m in request.history]
            )
            for token in llm.stream_chat(messages):
                yield sse("token", token)
            yield sse("done", {"provider": llm.name})
        except Exception:
            logger.exception("Chat request failed")
            yield sse("error", {"message": "The language model provider failed. Try again."})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
