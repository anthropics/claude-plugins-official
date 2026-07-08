"""Assembles a final answer for the 'fazla mesai / aşırı mesai' topic by
composing: retrieved knowledge chunks (rag/), a formatted statute citation
(citations/, via a CitationProvider), and a verification reminder.

Open/Closed Principle: a new topic (e.g. worker classification) gets its
own assembler class implementing the same PromptAssembler protocol; this
class is never modified to grow unrelated topics into it.
"""
from __future__ import annotations

from typing import Any

from core.engine.plugin_engine.contracts import CitationProvider, Retriever

_VERIFICATION_NOTE = (
    "[verify] Bu yanıt, aktif ülkenin (TR) yerel bilgi paketinden üretilmiştir. "
    "Üretim kullanımından önce bir TR iş hukuku danışmanı tarafından doğrulanmalıdır."
)


class OvertimePromptAssembler:
    """Satisfies core.engine.plugin_engine.contracts.PromptAssembler."""

    def __init__(self, retriever: Retriever, citation_provider: CitationProvider):
        self._retriever = retriever
        self._citation_provider = citation_provider

    def assemble(self, topic: str, context: dict[str, Any]) -> str:
        chunks = self._retriever.retrieve(topic, top_k=2)
        citation = self._citation_provider.format_statute_citation("4857 sayılı İş Kanunu", "41")

        lines = [f"## {topic}", ""]
        for chunk in chunks:
            lines.append(f"### {chunk.heading}")
            lines.append(chunk.text)
            lines.append("")
        lines.append(f"Kaynak: {citation}")
        lines.append("")
        lines.append(_VERIFICATION_NOTE)
        return "\n".join(lines)
