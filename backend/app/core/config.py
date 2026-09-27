from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Provider = Literal["nvidia", "gemini", "demo"]

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "chat_model": "mistralai/mistral-nemotron",
        "embedding_model": "nvidia/nemotron-3-embed-1b",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "chat_model": "gemini-3.5-flash",
        "embedding_model": "gemini-embedding-001",
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Provider = "nvidia"
    nvidia_api_key: str | None = None
    gemini_api_key: str | None = None
    chat_model: str | None = None
    embedding_model: str | None = None

    data_dir: Path = Path("data")
    max_upload_mb: int = 15
    chunk_size: int = 900
    chunk_overlap: int = 150
    top_k: int = 5
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def effective_provider(self) -> Provider:
        """Falls back to the offline demo provider when no API key is configured."""
        if self.llm_provider == "nvidia" and self.nvidia_api_key:
            return "nvidia"
        if self.llm_provider == "gemini" and self.gemini_api_key:
            return "gemini"
        return "demo"

    @property
    def api_key(self) -> str | None:
        return {"nvidia": self.nvidia_api_key, "gemini": self.gemini_api_key}.get(
            self.effective_provider
        )

    def model_for(self, kind: Literal["chat_model", "embedding_model"]) -> str:
        override = getattr(self, kind)
        if override:
            return override
        return PROVIDER_DEFAULTS.get(self.effective_provider, {}).get(kind, "demo")


@lru_cache
def get_settings() -> Settings:
    return Settings()
