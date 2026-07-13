"""Plugin Manifest: the structured, in-memory representation of a plugin's
declared identity and (for country plugins / migrated verticals) its
capability contracts.

The engine treats `.claude-plugin/plugin.json` as the one file every
plugin kind must have. Kind-specific files are layered on top:

  - country plugin:  country.config.yaml, capabilities.yaml
  - core vertical:   extension-points.yaml (optional -- most verticals
                      haven't been migrated yet; its absence is not an
                      error, just an empty capability contract)
  - vendor plugin:    nothing extra required

This module has ZERO hardcoded plugin names. It only knows about file
*conventions* relative to a plugin directory, never about a specific
plugin -- this is what "Core plugin'lerden bagimsiz olmali" means in code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from .errors import ManifestError

PLUGIN_JSON_REL_PATH = Path(".claude-plugin") / "plugin.json"
COUNTRY_CONFIG_REL_PATH = Path("country.config.yaml")
CAPABILITIES_REL_PATH = Path("capabilities.yaml")
EXTENSION_POINTS_REL_PATH = Path("extension-points.yaml")


class PluginKind(str, Enum):
    """What role a discovered plugin directory plays in the engine.

    Determined structurally (by which convention files are present), never
    by name -- see `infer_kind`.
    """

    COUNTRY = "country"
    VERTICAL = "vertical"
    VENDOR = "vendor"


def infer_kind(plugin_dir: Path) -> PluginKind:
    """Structural, name-independent classification of a plugin directory."""
    if (plugin_dir / COUNTRY_CONFIG_REL_PATH).exists():
        return PluginKind.COUNTRY
    if plugin_dir.parent.name == "external_plugins":
        return PluginKind.VENDOR
    return PluginKind.VERTICAL


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


@dataclass
class PluginManifest:
    """Everything the engine knows about one plugin, gathered from disk."""

    path: Path
    kind: PluginKind
    name: str
    version: str
    description: str
    author: str
    plugin_json: dict[str, Any]
    # Populated only for kind == COUNTRY:
    country_config: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    # Populated only for kind == VERTICAL (optional even then, until migrated):
    extension_points: dict[str, Any] | None = None

    @property
    def country_code(self) -> str | None:
        if self.country_config is None:
            return None
        code = self.country_config.get("country_code")
        return str(code) if code is not None else None


def load_manifest(plugin_dir: Path) -> PluginManifest:
    """Load and lightly parse (NOT schema-validate -- see validation.py) a
    single plugin directory's manifest files.

    Raises ManifestError if the mandatory plugin.json is missing, unreadable,
    or missing a required key. Kind-specific files that are simply absent
    (e.g. a not-yet-migrated vertical's extension-points.yaml) are not an
    error at this stage -- validation.py decides what's mandatory per kind.
    """
    plugin_json_path = plugin_dir / PLUGIN_JSON_REL_PATH
    if not plugin_json_path.exists():
        raise ManifestError(f"{plugin_dir}: missing {PLUGIN_JSON_REL_PATH}")
    try:
        plugin_json = _load_json(plugin_json_path)
    except (json.JSONDecodeError, OSError) as exc:
        raise ManifestError(f"{plugin_json_path}: {exc}") from exc

    for required_key in ("name", "version", "description"):
        if required_key not in plugin_json:
            raise ManifestError(f"{plugin_json_path}: missing required key {required_key!r}")

    kind = infer_kind(plugin_dir)

    country_config: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    extension_points: dict[str, Any] | None = None

    if kind is PluginKind.COUNTRY:
        country_config = _load_yaml(plugin_dir / COUNTRY_CONFIG_REL_PATH)
        capabilities_path = plugin_dir / CAPABILITIES_REL_PATH
        if capabilities_path.exists():
            capabilities = _load_yaml(capabilities_path)
    elif kind is PluginKind.VERTICAL:
        extension_points_path = plugin_dir / EXTENSION_POINTS_REL_PATH
        if extension_points_path.exists():
            extension_points = _load_yaml(extension_points_path)

    author_field = plugin_json.get("author", {})
    author_name = author_field.get("name", "") if isinstance(author_field, dict) else str(author_field)

    return PluginManifest(
        path=plugin_dir,
        kind=kind,
        name=plugin_json["name"],
        version=str(plugin_json["version"]),
        description=str(plugin_json["description"]),
        author=author_name,
        plugin_json=plugin_json,
        country_config=country_config,
        capabilities=capabilities,
        extension_points=extension_points,
    )
