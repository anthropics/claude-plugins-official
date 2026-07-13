from __future__ import annotations

import unittest
from pathlib import Path

from plugins.turkey.parser.legal_document import LegalDocumentType, infer_document_type
from plugins.turkey.rag.embeddings import HashEmbeddingProvider
from plugins.turkey.rag.vector_store import InMemoryVectorStore, VectorRecord


class ParserUnitTests(unittest.TestCase):
    def test_inferrs_file_and_legal_document_types(self) -> None:
        self.assertEqual(infer_document_type(Path("contract.html")), LegalDocumentType.HTML)
        self.assertEqual(infer_document_type(Path("4857-kanun.txt")), LegalDocumentType.LAW)
        self.assertEqual(infer_document_type(Path("yargitay-karar.pdf")), LegalDocumentType.COURT_DECISION)


class EmbeddingAndVectorUnitTests(unittest.TestCase):
    def test_hash_embedding_is_deterministic(self) -> None:
        provider = HashEmbeddingProvider(dimensions=16)
        self.assertEqual(provider.embed(["fazla mesai"]), provider.embed(["fazla mesai"]))

    def test_memory_store_returns_closest_record(self) -> None:
        store = InMemoryVectorStore()
        store.upsert(
            [
                VectorRecord("first", [1.0, 0.0], "first"),
                VectorRecord("second", [0.0, 1.0], "second"),
            ]
        )
        self.assertEqual(store.search([1.0, 0.0], limit=1)[0].record_id, "first")
