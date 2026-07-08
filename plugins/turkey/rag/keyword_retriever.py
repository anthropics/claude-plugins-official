"""A simple keyword-overlap retriever over the local knowledge corpus.

Good enough to find the right section of overtime-framework.md for a
question about "fazla mesai"; not a substitute for a real research
connector -- see this package's README.md for that distinction.
"""
from __future__ import annotations

import re

from core.engine.plugin_engine.contracts import RetrievedChunk

from .knowledge_indexer import KnowledgeIndexer

_WORD_RE = re.compile(r"[\wçğıöşüÇĞİÖŞÜ]+", re.UNICODE)


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text)}


class KeywordKnowledgeRetriever:
    """Satisfies core.engine.plugin_engine.contracts.Retriever."""

    def __init__(self, indexer: KnowledgeIndexer | None = None):
        self._indexer = indexer or KnowledgeIndexer()

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[RetrievedChunk] = []
        for path, section in self._indexer.build():
            section_tokens = _tokenize(f"{section.heading} {section.text}")
            overlap = len(query_tokens & section_tokens)
            if overlap == 0:
                continue
            score = overlap / len(query_tokens)
            scored.append(
                RetrievedChunk(
                    source_path=str(path), heading=section.heading, text=section.text, score=score
                )
            )
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]
