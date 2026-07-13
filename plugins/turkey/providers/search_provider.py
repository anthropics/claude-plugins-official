"""Implements core.engine.plugin_engine.contracts.SearchProvider for
Turkey by delegating to a list of injected adapters (Dependency Inversion
-- this class knows nothing about HTTP/MCP transport, only the
LegalResearchAdapter abstraction, so it never needs to change when a real
adapter implementation replaces a documented-but-unwired one)."""
from __future__ import annotations

from datetime import datetime, timezone

from core.engine.plugin_engine.contracts import (
    PreflightResult,
    SearchRequest,
    SearchResult,
    SourceDescriptor,
)

from ..adapters.base import LegalResearchAdapter
from ..sources.legal_source_registry import TurkishLegalSourceRegistry

_CATALOG_SOURCE_TYPES = ("court", "legislature", "official_gazette")


class TurkishSearchProvider:
    """Satisfies core.engine.plugin_engine.contracts.SearchProvider."""

    def __init__(
        self,
        adapters: list[LegalResearchAdapter] | None = None,
        registry: TurkishLegalSourceRegistry | None = None,
    ):
        self._adapters = adapters or []
        self._registry = registry or TurkishLegalSourceRegistry()

    def search(self, request: SearchRequest) -> list[SearchResult]:
        results: list[SearchResult] = []
        for adapter in self._adapters:
            if not adapter.is_available():
                continue
            for raw in adapter.search(request.query):
                results.append(
                    SearchResult(
                        title=raw.get("title", ""),
                        citation_raw=raw.get("citation_raw", ""),
                        source_id=raw.get("source_id", adapter.source_id),
                        retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        url=raw.get("url"),
                        snippet=raw.get("snippet"),
                    )
                )
        return results

    def preflight_check(self) -> PreflightResult:
        for adapter in self._adapters:
            if adapter.is_available():
                return PreflightResult(available=True, source_id=adapter.source_id)
        return PreflightResult(
            available=False,
            reason="no configured Turkish legal-research adapter is currently connected "
            "(all are documented-but-not-yet-wired -- see countries/tr/mcp/mcp-tool-registry.tr.yaml)",
        )

    def get_source_catalog(self) -> list[SourceDescriptor]:
        return [
            SourceDescriptor(source_id=s.source_id, tier=s.tier, coverage=s.notes or s.name)
            for s in self._registry.all()
            if s.source_type in _CATALOG_SOURCE_TYPES
        ]
