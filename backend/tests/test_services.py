import pytest

from app.services.llm import DemoProvider
from app.services.pdf import InvalidDocumentError, extract_pages
from app.services.rag import MAX_HISTORY_MESSAGES, build_messages
from app.services.store import RetrievedChunk


def chunk(text: str, page: int = 1) -> RetrievedChunk:
    return RetrievedChunk(document_id="d1", filename="policy.pdf", page=page, text=text, score=0.9)


def test_prompt_numbers_passages_and_keeps_recent_history() -> None:
    history = [{"role": "user", "content": f"q{i}"} for i in range(10)]
    messages = build_messages("How many days?", [chunk("Three days", 2), chunk("VPN")], history)

    assert messages[0]["role"] == "system"
    assert len(messages) == 1 + MAX_HISTORY_MESSAGES + 1
    user = messages[-1]["content"]
    assert "[1] (policy.pdf, page 2)\nThree days" in user
    assert "[2] (policy.pdf, page 1)\nVPN" in user
    assert user.endswith("Question: How many days?")


def test_prompt_without_context_says_so() -> None:
    assert "no relevant passages" in build_messages("Anything?", [])[-1]["content"]


def test_invalid_pdf_is_rejected() -> None:
    with pytest.raises(InvalidDocumentError):
        extract_pages(b"not a pdf")


def test_demo_embeddings_rank_related_text_higher() -> None:
    provider = DemoProvider()
    query, related, unrelated = provider.embed(
        ["vpn security", "Use the VPN for security", "Lunch menu"], "query"
    )
    similarity = lambda a, b: sum(x * y for x, y in zip(a, b, strict=True))  # noqa: E731
    assert similarity(query, related) > similarity(query, unrelated)


class _Failing:
    name = "primary"

    def embed(self, texts, input_type):
        return [[1.0] for _ in texts]

    def stream_chat(self, messages):
        raise TimeoutError("provider timed out")
        yield  # pragma: no cover


class _Answering:
    name = "fallback"

    def embed(self, texts, input_type):  # pragma: no cover
        raise AssertionError("embeddings must come from the primary provider")

    def stream_chat(self, messages):
        yield "fallback answer"


def test_failover_uses_fallback_for_chat_but_primary_for_embeddings() -> None:
    from app.services.llm import FailoverProvider

    provider = FailoverProvider(_Failing(), _Answering())
    assert provider.embed(["a"], "query") == [[1.0]]
    assert "".join(provider.stream_chat([{"role": "user", "content": "hi"}])) == "fallback answer"


class _BreaksMidAnswer:
    name = "primary"

    def embed(self, texts, input_type):  # pragma: no cover
        return [[1.0] for _ in texts]

    def stream_chat(self, messages):
        yield "partial "
        raise ConnectionError("engine crashed")


def test_failover_restarts_answer_when_primary_breaks_mid_stream() -> None:
    from app.services.llm import FailoverProvider, Restart

    tokens = list(FailoverProvider(_BreaksMidAnswer(), _Answering()).stream_chat([]))
    assert tokens[0] == "partial "
    assert isinstance(tokens[1], Restart)
    assert tokens[2:] == ["fallback answer"]
