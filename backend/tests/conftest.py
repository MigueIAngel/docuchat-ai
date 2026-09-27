from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

SAMPLE_PDF = Path(__file__).resolve().parents[2] / "samples" / "remote-work-policy.pdf"


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    # Offline demo provider and an isolated data directory for every test.
    settings = Settings(_env_file=None, llm_provider="demo", data_dir=tmp_path)  # type: ignore[call-arg]
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf() -> bytes:
    return SAMPLE_PDF.read_bytes()
