from __future__ import annotations

import unittest

from .support import ensure_core_imports

ensure_core_imports()

from core.engine.plugin_engine.contracts import RetrievedChunk
from plugins.turkey.prompts.overtime_prompt_assembler import OvertimePromptAssembler


class _Retriever:
    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        return [RetrievedChunk("knowledge.md", "Fazla Mesai", "Haftalık sınır aşılmıştır.", 1.0)]


class _CitationProvider:
    def format_statute_citation(self, instrument: str, section: str, subsection: str | None = None) -> str:
        return f"{instrument} m.{section}"


class PromptTests(unittest.TestCase):
    def test_overtime_prompt_uses_retrieval_and_citation(self) -> None:
        output = OvertimePromptAssembler(_Retriever(), _CitationProvider()).assemble("Fazla mesai", {})
        self.assertIn("Haftalık sınır", output)
        self.assertIn("4857 sayılı İş Kanunu m.41", output)
        self.assertIn("[verify]", output)
