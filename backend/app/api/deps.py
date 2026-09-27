import re
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.llm import Provider, get_provider
from app.services.store import DocumentStore


@lru_cache
def _store(data_dir: str, collection: str) -> DocumentStore:
    from pathlib import Path

    return DocumentStore(Path(data_dir), collection)


def get_store(settings: Annotated[Settings, Depends(get_settings)]) -> DocumentStore:
    model = settings.model_for("embedding_model")
    collection = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{settings.effective_provider}_{model}")[:60]
    return _store(str(settings.data_dir), collection)


_providers: dict[tuple[str, str, str, bool], Provider] = {}


def get_llm(settings: Annotated[Settings, Depends(get_settings)]) -> Provider:
    """One provider per configuration, built from the injected settings."""
    key = (
        settings.effective_provider,
        settings.model_for("chat_model"),
        settings.model_for("embedding_model"),
        bool(settings.gemini_api_key and settings.nvidia_api_key),
    )
    if key not in _providers:
        _providers[key] = get_provider(settings)
    return _providers[key]


StoreDep = Annotated[DocumentStore, Depends(get_store)]
LLMDep = Annotated[Provider, Depends(get_llm)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
