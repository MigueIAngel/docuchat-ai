from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.api.deps import LLMDep, SettingsDep, StoreDep
from app.services.chunking import chunk_pages
from app.services.pdf import InvalidDocumentError, extract_pages

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    created_at: datetime


@router.get("", response_model=list[DocumentOut])
def list_documents(store: StoreDep):
    return store.all()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile, store: StoreDep, llm: LLMDep, settings: SettingsDep):
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF files are supported")

    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Max size is {settings.max_upload_mb} MB"
        )

    try:
        pages = await run_in_threadpool(extract_pages, data)
    except InvalidDocumentError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error

    chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
    try:
        vectors = await run_in_threadpool(llm.embed, [c.text for c in chunks], "passage")
    except Exception as error:  # provider/network errors
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Embedding provider failed") from error
    return await run_in_threadpool(store.add, filename, len(pages), chunks, vectors)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, store: StoreDep) -> None:
    if not store.delete(document_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
