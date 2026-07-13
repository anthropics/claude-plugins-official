"""Plugin Manifest for plugins/turkey.

Single Responsibility: describe what this code package is and which
country-plugin data directory it implements against. This is distinct
from countries/tr/.claude-plugin/plugin.json (the installable Claude Code
plugin's manifest, describing the markdown/YAML spec side) -- this one
describes the *code* side, and points at the data side it reads from.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .paths import TR_DATA_DIR


@dataclass(frozen=True)
class TurkeyPluginManifest:
    name: str = "plugins.turkey"
    version: str = "0.1.0"
    description: str = (
        "Executable, layered (SOLID) implementation of the Turkey country "
        "plugin's Provider/Tool/Prompt/Workflow contracts. Reads its legal-"
        "content data from countries/tr/ rather than duplicating it."
    )
    country_code: str = "TR"
    implements_country_data_dir: str = str(TR_DATA_DIR)
    provides: tuple[str, ...] = field(
        default=("citation_provider", "search_provider", "document_provider")
    )


PLUGIN_MANIFEST = TurkeyPluginManifest()
