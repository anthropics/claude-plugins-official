"""Filesystem locations plugins/turkey reads its data from.

Single Responsibility: know where things are on disk, so every other
module in this package asks *this* module for a path instead of computing
one itself. Relocating the underlying data (e.g. if countries/tr/ is ever
restructured) means touching this one file, not every module that reads
from disk.
"""
from __future__ import annotations

from pathlib import Path

TURKEY_PLUGIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = TURKEY_PLUGIN_DIR.parent.parent
TR_DATA_DIR = REPO_ROOT / "countries" / "tr"

COUNTRY_CONFIG_PATH = TR_DATA_DIR / "country.config.yaml"
CAPABILITIES_PATH = TR_DATA_DIR / "capabilities.yaml"
LEGAL_SOURCE_REGISTRY_PATH = TR_DATA_DIR / "legal-sources" / "legal-source-registry.tr.yaml"
MCP_TOOL_REGISTRY_PATH = TR_DATA_DIR / "mcp" / "mcp-tool-registry.tr.yaml"
KNOWLEDGE_DIR = TR_DATA_DIR / "knowledge"

GUARDRAIL_FRAGMENTS_DIR = REPO_ROOT / "core" / "shared" / "guardrail-fragments"
