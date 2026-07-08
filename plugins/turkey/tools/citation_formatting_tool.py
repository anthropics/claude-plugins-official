"""Exposes a CitationProvider's statute-formatting method as a Tool."""
from __future__ import annotations

from core.engine.plugin_engine.contracts import CitationProvider


class CitationFormattingTool:
    name = "citation-formatting"

    def __init__(self, citation_provider: CitationProvider):
        self._citation_provider = citation_provider

    def run(self, instrument: str, section: str, subsection: str | None = None) -> str:
        return self._citation_provider.format_statute_citation(instrument, section, subsection)
