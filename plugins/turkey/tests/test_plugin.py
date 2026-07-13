from __future__ import annotations

import unittest

from .support import ensure_core_imports

ensure_core_imports()

from plugins.turkey.registration import TurkeyPluginRegistrar


class PluginTests(unittest.TestCase):
    def test_registrar_constructs_all_plugin_services(self) -> None:
        registrar = TurkeyPluginRegistrar()
        self.assertEqual(registrar.country_code, "TR")
        self.assertIsNotNone(registrar.citation_provider)
        self.assertFalse(registrar.search_provider.preflight_check().available)
        self.assertEqual(len(registrar.tools), 3)
