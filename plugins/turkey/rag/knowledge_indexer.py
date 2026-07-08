"""Indexer: loads every knowledge/<vertical>/*.md file into parsed
markdown sections. Single Responsibility: I/O + structural parsing, no
scoring/retrieval logic -- see keyword_retriever.py for that."""
from __future__ import annotations

from pathlib import Path

from ..parser.markdown_parser import MarkdownFileParser, MarkdownSection
from ..paths import KNOWLEDGE_DIR


class KnowledgeIndexer:
    def __init__(
        self,
        knowledge_dir: Path = KNOWLEDGE_DIR,
        parser: MarkdownFileParser | None = None,
    ):
        self._knowledge_dir = knowledge_dir
        self._parser = parser or MarkdownFileParser()
        self._index: list[tuple[Path, MarkdownSection]] | None = None

    def build(self) -> list[tuple[Path, MarkdownSection]]:
        if self._index is None:
            entries: list[tuple[Path, MarkdownSection]] = []
            if self._knowledge_dir.is_dir():
                for md_path in sorted(self._knowledge_dir.rglob("*.md")):
                    document = self._parser.parse(md_path)
                    for section in document.sections:
                        entries.append((md_path, section))
            self._index = entries
        return self._index
