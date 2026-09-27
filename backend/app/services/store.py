"""Document registry (SQLite) and vector index (ChromaDB)."""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.services.chunking import Chunk


@dataclass
class DocumentRecord:
    id: str
    filename: str
    pages: int
    chunks: int
    created_at: str


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    page: int
    text: str
    score: float


class DocumentStore:
    def __init__(self, data_dir: Path, collection: str) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(data_dir / "documents.db", check_same_thread=False)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, pages INTEGER NOT NULL,
                chunks INTEGER NOT NULL, created_at TEXT NOT NULL)"""
        )
        self._chroma = chromadb.PersistentClient(
            path=str(data_dir / "chroma"), settings=ChromaSettings(anonymized_telemetry=False)
        )
        # One collection per provider/model: embeddings from different models are not comparable.
        self._collection = self._chroma.get_or_create_collection(
            collection, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )

    def add(
        self, filename: str, pages: int, chunks: list[Chunk], vectors: list[list[float]]
    ) -> DocumentRecord:
        record = DocumentRecord(
            id=uuid.uuid4().hex,
            filename=filename,
            pages=pages,
            chunks=len(chunks),
            created_at=datetime.now(UTC).isoformat(),
        )
        self._collection.add(
            ids=[f"{record.id}:{chunk.index}" for chunk in chunks],
            embeddings=vectors,  # type: ignore[arg-type]
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {"document_id": record.id, "filename": filename, "page": chunk.page}
                for chunk in chunks
            ],
        )
        with self._db:
            self._db.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                (record.id, record.filename, record.pages, record.chunks, record.created_at),
            )
        return record

    def all(self) -> list[DocumentRecord]:
        rows = self._db.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [DocumentRecord(*row) for row in rows]

    def get(self, document_id: str) -> DocumentRecord | None:
        row = self._db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return DocumentRecord(*row) if row else None

    def delete(self, document_id: str) -> bool:
        if not self.get(document_id):
            return False
        self._collection.delete(where={"document_id": document_id})
        with self._db:
            self._db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return True

    def search(
        self, vector: list[float], k: int, document_ids: list[str] | None = None
    ) -> list[RetrievedChunk]:
        if self._collection.count() == 0:
            return []
        where = None
        if document_ids:
            where = (
                {"document_id": document_ids[0]}
                if len(document_ids) == 1
                else {"document_id": {"$in": document_ids}}
            )
        result = self._collection.query(
            query_embeddings=[vector],  # type: ignore[arg-type]
            n_results=k,
            where=where,  # type: ignore[arg-type]
        )
        chunks = []
        for text, meta, distance in zip(
            result["documents"][0],  # type: ignore[index]
            result["metadatas"][0],  # type: ignore[index]
            result["distances"][0],  # type: ignore[index]
            strict=True,
        ):
            chunks.append(
                RetrievedChunk(
                    document_id=str(meta["document_id"]),
                    filename=str(meta["filename"]),
                    page=int(meta["page"]),  # type: ignore[arg-type]
                    text=text,
                    score=round(1 - float(distance), 4),
                )
            )
        return chunks
