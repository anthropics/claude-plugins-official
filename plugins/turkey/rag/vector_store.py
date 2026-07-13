"""Vector-store abstraction and database-specific integration seams."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class VectorRecord:
    record_id: str
    vector: list[float]
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, records: list[VectorRecord]) -> None: ...

    def search(self, vector: list[float], limit: int = 5) -> list[VectorRecord]: ...


class InMemoryVectorStore:
    """Small local store that keeps RAG operational without external services."""

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        self._records.update({record.record_id: record for record in records})

    def search(self, vector: list[float], limit: int = 5) -> list[VectorRecord]:
        def cosine(record: VectorRecord) -> float:
            numerator = sum(left * right for left, right in zip(vector, record.vector))
            magnitude = sqrt(sum(value * value for value in vector)) * sqrt(
                sum(value * value for value in record.vector)
            )
            return numerator / magnitude if magnitude else 0.0

        return sorted(self._records.values(), key=cosine, reverse=True)[:limit]


class _UnwiredVectorStore:
    """Base seam for optional database drivers, preserving a common API."""

    backend_name: str

    def upsert(self, records: list[VectorRecord]) -> None:
        raise NotImplementedError(f"{self.backend_name} vector store is not configured")

    def search(self, vector: list[float], limit: int = 5) -> list[VectorRecord]:
        raise NotImplementedError(f"{self.backend_name} vector store is not configured")


class QdrantVectorStore(_UnwiredVectorStore):
    backend_name = "Qdrant"


class FaissVectorStore(_UnwiredVectorStore):
    backend_name = "FAISS"


class PgvectorVectorStore(_UnwiredVectorStore):
    backend_name = "pgvector"


class MilvusVectorStore(_UnwiredVectorStore):
    backend_name = "Milvus"
