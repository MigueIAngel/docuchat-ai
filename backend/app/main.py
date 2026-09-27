from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="DocuChat AI",
    description="Retrieval-augmented chat over your PDF documents.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents.router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": settings.effective_provider,
        "chat_model": settings.model_for("chat_model"),
        "embedding_model": settings.model_for("embedding_model"),
    }
