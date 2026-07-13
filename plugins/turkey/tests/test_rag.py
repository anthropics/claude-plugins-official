from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from plugins.turkey.parser.legal_document import LegalDocumentType
from plugins.turkey.rag.legal_rag import LegalRag


class RagTests(unittest.TestCase):
    def test_ingests_and_retrieves_txt_legal_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "is-kanunu.txt"
            path.write_text("4857 sayılı İş Kanunu fazla mesai düzenlemesi.", encoding="utf-8")
            rag = LegalRag()
            self.assertEqual(rag.ingest(path, LegalDocumentType.LAW), 1)
            self.assertIn("fazla mesai", rag.retrieve("fazla mesai", top_k=1)[0].text)

    def test_ingests_html_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "karar.html"
            path.write_text("<html><body><h1>Karar</h1><p>Onama kararı.</p></body></html>", encoding="utf-8")
            rag = LegalRag()
            rag.ingest(path, LegalDocumentType.COURT_DECISION)
            self.assertIn("Onama", rag.retrieve("onama", top_k=1)[0].text)
