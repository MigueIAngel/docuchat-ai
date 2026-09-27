"""LLM and embedding providers.

NVIDIA NIM and Gemini both expose OpenAI-compatible endpoints, so one client
implementation covers both. The demo provider works offline (no API key) and
is used in tests.
"""

import hashlib
import math
import re
from collections.abc import Iterator
from typing import Literal, Protocol

from openai import OpenAI

from app.core.config import Settings

InputType = Literal["query", "passage"]


class Provider(Protocol):
    name: str

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]: ...

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterator[str]: ...


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        from app.core.config import PROVIDER_DEFAULTS

        self.name = settings.effective_provider
        self.client = OpenAI(
            api_key=settings.api_key,
            base_url=PROVIDER_DEFAULTS[self.name]["base_url"],
            timeout=60,
            max_retries=2,
        )
        self.chat_model = settings.model_for("chat_model")
        self.embedding_model = settings.model_for("embedding_model")

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


def get_provider(settings: Settings) -> Provider:
    if settings.effective_provider == "demo":
        return DemoProvider()
    return OpenAICompatibleProvider(settings)
