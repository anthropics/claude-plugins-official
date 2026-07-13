from __future__ import annotations

import unittest

from plugins.turkey.providers.legal_sources.base import LegalSourceProvider
from plugins.turkey.providers.legal_sources.registry import discover_legal_source_providers

from .support import ensure_core_imports

ensure_core_imports()

from core.engine.plugin_engine.contracts import SearchRequest
from plugins.turkey.providers.search_provider import TurkishSearchProvider


class _AvailableProvider:
    source_id = "test-source"

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> list[dict[str, str]]:
        return [{"title": query, "citation_raw": "Test m.1", "source_id": self.source_id}]


class ProviderTests(unittest.TestCase):
    def test_discovers_all_turkish_legal_sources(self) -> None:
        providers = discover_legal_source_providers()
        self.assertEqual(
            {provider.source_id for provider in providers},
            {"uyap", "resmi-gazete", "mevzuat-bilgi-sistemi", "yargitay", "danistay", "aym", "kvkk"},
        )
        self.assertTrue(all(isinstance(provider, LegalSourceProvider) for provider in providers))

    def test_search_provider_maps_available_provider_results(self) -> None:
        results = TurkishSearchProvider(adapters=[_AvailableProvider()]).search(SearchRequest("test"))
        self.assertEqual(results[0].source_id, "test-source")
        self.assertEqual(results[0].citation_raw, "Test m.1")
