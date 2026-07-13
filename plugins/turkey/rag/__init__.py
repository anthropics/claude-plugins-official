"""Retrieval layer for local knowledge and provider-independent legal documents."""

from .embeddings import EmbeddingProvider, HashEmbeddingProvider
from .legal_rag import LegalRag, LegalRetrievedChunk
from .vector_store import (
    FaissVectorStore,
    InMemoryVectorStore,
    MilvusVectorStore,
    PgvectorVectorStore,
    QdrantVectorStore,
    VectorStore,
)

__all__ = [
    "EmbeddingProvider",
    "FaissVectorStore",
    "HashEmbeddingProvider",
    "InMemoryVectorStore",
    "LegalRag",
    "LegalRetrievedChunk",
    "MilvusVectorStore",
    "PgvectorVectorStore",
    "QdrantVectorStore",
    "VectorStore",
]
