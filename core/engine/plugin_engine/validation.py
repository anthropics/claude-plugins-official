"""Plugin Validation: schema-driven checks for every manifest kind.

This is the formal, jsonschema-driven counterpart to the ad hoc checks
scripts/lint-country-plugin.py hand-rolled. Two schemas back it (in
addition to the pre-existing country-config.schema.yaml):
core/engine/registries/capabilities.schema.yaml and
core/engine/registries/extension-points.schema.yaml.
"""
from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

from .manifest import PluginKind, PluginManifest

_ENGINE_DIR = Path(__file__).resolve().parent.parent  # core/engine/
_PROVIDERS_DIR = _ENGINE_DIR / "providers"
_REGISTRIES_DIR = _ENGINE_DIR / "registries"

_COUNTRY_CONFIG_SCHEMA = _PROVIDERS_DIR / "country-config.schema.yaml"
_CAPABILITIES_SCHEMA = _REGISTRIES_DIR / "capabilities.schema.yaml"
_EXTENSION_POINTS_SCHEMA = _REGISTRIES_DIR / "extension-points.schema.yaml"

PLACEHOLDER_MARKER = "[PLACEHOLDER"


def _load_schema(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _schema_errors(instance: dict, schema_path: Path) -> list[str]:
    schema = _load_schema(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in validator.iter_errors(instance):
        loc = "/".join(str(p) for p in err.absolute_path) or "$"
        errors.append(f"{err.message} at {loc}")
    return errors


def find_placeholders(value: object, path: str = "$") -> list[str]:
    """Recursively find any string containing the template placeholder
    marker `[PLACEHOLDER` -- signals a country plugin copied from
    countries/_template/ without finishing the fill-in."""
    found: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            found.extend(find_placeholders(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found.extend(find_placeholders(v, f"{path}[{i}]"))
    elif isinstance(value, str) and PLACEHOLDER_MARKER in value:
        found.append(f"{path} = {value!r}")
    return found


def validate_manifest(manifest: PluginManifest) -> list[str]:
    """Return a list of human-readable validation error strings (empty if
    the manifest is fully valid). Never raises for validation failures --
    only propagates I/O problems reading a schema file itself.
    """
    errors: list[str] = []

    if manifest.kind is PluginKind.COUNTRY:
        if manifest.country_config is None:
            errors.append("country plugin has no country.config.yaml")
        else:
            errors.extend(
                f"country.config.yaml: {e}"
                for e in _schema_errors(manifest.country_config, _COUNTRY_CONFIG_SCHEMA)
            )
            errors.extend(
                f"country.config.yaml: unresolved placeholder at {p}"
                for p in find_placeholders(manifest.country_config)
            )

        if manifest.capabilities is None:
            errors.append("country plugin has no capabilities.yaml")
        else:
            errors.extend(
                f"capabilities.yaml: {e}"
                for e in _schema_errors(manifest.capabilities, _CAPABILITIES_SCHEMA)
            )
            errors.extend(
                f"capabilities.yaml: unresolved placeholder at {p}"
                for p in find_placeholders(manifest.capabilities)
            )

    elif manifest.kind is PluginKind.VERTICAL:
        # extension-points.yaml is optional (most verticals aren't migrated
        # yet) -- only validate its *shape* if the vertical has one.
        if manifest.extension_points is not None:
            errors.extend(
                f"extension-points.yaml: {e}"
                for e in _schema_errors(manifest.extension_points, _EXTENSION_POINTS_SCHEMA)
            )

    # PluginKind.VENDOR has no additional kind-specific schema today.

    return errors
