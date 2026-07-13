from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from plugins.turkey.mcp import TurkeyMcpToolServer
from plugins.turkey.parser.legal_document import LegalDocumentType
from plugins.turkey.rag.legal_rag import LegalRag


class TurkeyPluginIntegrationTests(unittest.TestCase):
    def test_document_retrieval_and_tool_analysis_work_together(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mahkeme-karari.txt"
            path.write_text("Mahkeme davayı kabul etti. KVKK kapsamında idari para cezası uygulanabilir.", encoding="utf-8")
            rag = LegalRag()
            rag.ingest(path, LegalDocumentType.COURT_DECISION)
            document = rag.retrieve("KVKK", top_k=1)[0].text
            result = TurkeyMcpToolServer().call_tool("turkey_risk_analyzer", {"text": document})
            self.assertIn("sanction", result["structuredContent"]["risk_flags"])
