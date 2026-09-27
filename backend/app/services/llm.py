"""LLM and embedding providers.

NVIDIA NIM and Gemini both expose OpenAI-compatible endpoints, so one client
implementation covers both. The demo provider works offline (no API key) and
is used in tests.
"""

import hashlib
import logging
import math
import re
from collections.abc import Iterator
from typing import Literal, Protocol

from openai import OpenAI

from app.core.config import Settings

logger = logging.getLogger(__name__)

InputType = Literal["query", "passage"]


class Restart(str):
    """Marker yielded by FailoverProvider: discard the partial answer and start over."""


RESTART = Restart("")


class Provider(Protocol):
    name: str

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]: ...

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterator[str]: ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        name: str,
        api_key: str | None,
        chat_model: str,
        embedding_model: str,
    ) -> None:
        from app.core.config import PROVIDER_DEFAULTS

        self.name = name
        self.client = OpenAI(
            api_key=api_key,
            base_url=PROVIDER_DEFAULTS[name]["base_url"],
            timeout=120,
            max_retries=2,
        )
        self.chat_model = chat_model
        self.embedding_model = embedding_model

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        vectors: list[list[float]] = []
        # NVIDIA retrieval embeddings are asymmetric: queries and passages differ.
        extra = {"input_type": input_type, "truncate": "END"} if self.name == "nvidia" else {}
        for start in range(0, len(texts), 32):
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts[start : start + 32],
                encoding_format="float",
                extra_body=extra or None,
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.2,
            max_tokens=1024,
            stream=True,
        )
        for event in stream:
            if event.choices and (delta := event.choices[0].delta.content):
                yield delta


class DemoProvider:
    """Offline provider: hashed bag-of-words embeddings and an extractive answer."""

    name = "demo"
    dimensions = 256

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"\w+", text.lower()):
            bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterator[str]:
        context = messages[-1]["content"]
        first = re.search(r"\[1\][^\n]*\n(.+?)(?:\n\n|\Z)", context, re.S)
        excerpt = first.group(1).strip()[:400] if first else "No relevant context found."
        answer = (
            "Demo mode (no API key configured). The most relevant passage is:\n\n"
            f"> {excerpt} [1]"
        )
        yield from answer.split(" ")[:1]
        for word in answer.split(" ")[1:]:
            yield f" {word}"


class FailoverProvider:
    """Embeds with the primary provider and falls back to a second one for chat.

    Embeddings must always come from the same model (vectors are not comparable
    across models), but any model can write the answer. If the primary provider
    fails, the fallback answers instead; if it fails mid-answer, a RESTART marker
    is yielded first so the client can discard the partial text.
    """

    def __init__(self, primary: Provider, fallback: Provider) -> None:
        self.primary = primary
        self.fallback = fallback
        self.name = primary.name

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        return self.primary.embed(texts, input_type)

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterator[str]:
        started = False
        try:
            for token in self.primary.stream_chat(messages):
                started = True
                yield token
            return
        except Exception:
            logger.warning("%s failed, answering with %s", self.primary.name, self.fallback.name)
        if started:
            # The partial answer is incomplete: tell the client to discard it.
            yield RESTART
        yield from self.fallback.stream_chat(messages)


def get_provider(settings: Settings) -> Provider:
    from app.core.config import PROVIDER_DEFAULTS

    name = settings.effective_provider
    if name == "demo":
        return DemoProvider()
    primary = OpenAICompatibleProvider(
        name,
        settings.api_key,
        settings.model_for("chat_model"),
        settings.model_for("embedding_model"),
    )
    backup = "gemini" if name == "nvidia" else "nvidia"
    backup_key = settings.gemini_api_key if backup == "gemini" else settings.nvidia_api_key
    if not backup_key:
        return primary
    defaults = PROVIDER_DEFAULTS[backup]
    fallback = OpenAICompatibleProvider(
        backup, backup_key, defaults["chat_model"], defaults["embedding_model"]
    )
    return FailoverProvider(primary, fallback)
