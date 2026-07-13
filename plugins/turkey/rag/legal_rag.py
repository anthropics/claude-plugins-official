"""Provider-independent legal-document ingestion and retrieval pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ..parser.legal_document import (
    LegalDocumentParserRegistry,
    LegalDocumentType,
    ParsedLegalDocument,
)
from .embeddings import EmbeddingProvider, HashEmbeddingProvider
from .vector_store import InMemoryVectorStore, VectorRecord, VectorStore


@dataclass(frozen=True)
class LegalTextChunk:
    chunk_id: str
    text: str
    document: ParsedLegalDocument
    ordinal: int


@dataclass(frozen=True)
class LegalRetrievedChunk:
    """Retriever-compatible result without coupling document RAG to core."""

    source_path: str
    heading: str
    text: str
    score: float


class LegalRag:
    """Indexes parsed local documents through injected embeddings and storage."""

    def __init__(
        self,
        parser: LegalDocumentParserRegistry | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        chunk_size: int = 1_000,
    ):
        self._parser = parser or LegalDocumentParserRegistry()
        self._embedding_provider = embedding_provider or HashEmbeddingProvider()
        self._vector_store = vector_store or InMemoryVectorStore()
        self._chunk_size = chunk_size

    def ingest(
        self, path: Path, document_type: LegalDocumentType | None = None
    ) -> int:
        document = self._parser.parse(path, document_type)
        chunks = self._chunk(document)
        vectors = self._embedding_provider.embed([chunk.text for chunk in chunks])
        self._vector_store.upsert(
            [
                VectorRecord(
                    record_id=chunk.chunk_id,
                    vector=vector,
                    text=chunk.text,
                    metadata={
                        "source_path": str(document.path),
                        "title": document.title,
                        "document_type": document.document_type.value,
                        "ordinal": str(chunk.ordinal),
                    },
                )
                for chunk, vector in zip(chunks, vectors)
            ]
        )
        return len(chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[LegalRetrievedChunk]:
        query_vector = self._embedding_provider.embed([query])[0]
        return [
            LegalRetrievedChunk(
                source_path=record.metadata["source_path"],
                heading=record.metadata["title"],
                text=record.text,
                score=1.0 / (position + 1),
            )
            for position, record in enumerate(self._vector_store.search(query_vector, top_k))
        ]

    def _chunk(self, document: ParsedLegalDocument) -> list[LegalTextChunk]:
        parts = [document.text[index : index + self._chunk_size].strip() for index in range(0, len(document.text), self._chunk_size)]
        return [
            LegalTextChunk(
                chunk_id=sha256(f"{document.path}:{ordinal}:{text}".encode("utf-8")).hexdigest(),
                text=text,
                document=document,
                ordinal=ordinal,
            )
            for ordinal, text in enumerate(parts)
            if text
        ]
