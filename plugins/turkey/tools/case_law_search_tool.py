"""Exposes a SearchProvider as the 'case-law-search' Tool Registry
capability. Single Responsibility: adapt SearchProvider's request-object
API to a simple keyword-argument call a workflow can invoke directly."""
from __future__ import annotations

from core.engine.plugin_engine.contracts import SearchProvider, SearchRequest, SearchResult


class CaseLawSearchTool:
    name = "case-law-search"

    def __init__(self, search_provider: SearchProvider):
        self._search_provider = search_provider

    def run(self, query: str, jurisdiction_scope: str | None = None) -> list[SearchResult]:
        request = SearchRequest(query=query, jurisdiction_scope=jurisdiction_scope, source_type="case-law")
        return self._search_provider.search(request)
