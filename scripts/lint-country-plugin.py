#!/usr/bin/env python3
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
"""Validate country plugins under countries/*/ against core/ schemas.

For each countries/<code>/ directory (excluding _template/), checks:

  1. country.config.yaml validates against
     core/engine/providers/country-config.schema.yaml
  2. No field anywhere in the plugin is left as the literal template
     placeholder "[PLACEHOLDER]" (or a string containing it).
  3. capabilities.yaml declares a full/partial/not_supported verdict for
     every Provider method known to core/ (see PROVIDER_METHODS below —
     kept in sync with core/engine/providers/*.interface.md by hand, since
     the interface files are prose/tables, not machine-readable).
  4. Every countries/<code>/mcp/*.yaml validates against
     core/engine/registries/mcp-tool-registry.schema.yaml
  5. Every countries/<code>/legal-sources/*.yaml validates against
     core/engine/registries/legal-source-registry.schema.yaml

Exits 0 with a per-country summary on success, 1 with itemized errors on
failure. If countries/ contains only _template/ (no real country plugin
yet), prints a no-op summary and exits 0 — this is the expected state
until the first country plugin (countries/us or countries/tr) is added.

This script is self-contained (does not import scripts/validate.py) so
that it works independently of any other script in this repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES_DIR = ROOT / "countries"
CORE_DIR = ROOT / "core"

COUNTRY_CONFIG_SCHEMA = CORE_DIR / "engine" / "providers" / "country-config.schema.yaml"
MCP_REGISTRY_SCHEMA = CORE_DIR / "engine" / "registries" / "mcp-tool-registry.schema.yaml"
LEGAL_SOURCE_SCHEMA = CORE_DIR / "engine" / "registries" / "legal-source-registry.schema.yaml"

# Kept in sync by hand with core/engine/providers/*.interface.md. If a new
# method is added to an interface file, add it here too.
PROVIDER_METHODS: dict[str, list[str]] = {
    "citation_provider": [
        "formatStatuteCitation",
        "formatCaseCitation",
        "getProvenanceTagVocabulary",
        "getHighRiskPinpointPatterns",
        "classifyCitationRisk",
    ],
    "search_provider": ["search", "preflightCheck", "getSourceCatalog"],
    "document_provider": [
        "getDocumentStatus",
        "getSignatureStatus",
        "getFilingStatus",
        "getIrreversibilityFlags",
    ],
}
VALID_VERDICTS = {"full", "partial", "not_supported"}
PLACEHOLDER_MARKER = "[PLACEHOLDER"


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _find_placeholders(value, path: str = "$") -> list[str]:
    """Recursively find any string containing the template placeholder marker."""
    found: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            found.extend(_find_placeholders(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found.extend(_find_placeholders(v, f"{path}[{i}]"))
    elif isinstance(value, str) and PLACEHOLDER_MARKER in value:
        found.append(f"{path} = {value!r}")
    return found


def _validate_against_schema(instance_path: Path, schema_path: Path) -> list[str]:
    instance = _load_yaml(instance_path)
    schema = _load_yaml(schema_path)
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in validator.iter_errors(instance):
        loc = "/".join(str(p) for p in err.absolute_path) or "$"
        errors.append(f"{instance_path.relative_to(ROOT)}: {err.message} at {loc}")
    return errors


def _check_capabilities(country_dir: Path, capabilities: dict) -> list[str]:
    errors: list[str] = []
    verticals = capabilities.get("verticals") or {}
    if not verticals:
        errors.append(
            f"{country_dir.name}/capabilities.yaml: no 'verticals' declared — "
            f"a country plugin must declare at least one vertical's coverage"
        )
        return errors
    for vertical_name, providers in verticals.items():
        for provider_key, methods in PROVIDER_METHODS.items():
            declared = (providers or {}).get(provider_key) or {}
            for method in methods:
                verdict = declared.get(method)
                if verdict is None:
                    errors.append(
                        f"{country_dir.name}/capabilities.yaml: "
                        f"verticals.{vertical_name}.{provider_key}.{method} is missing "
                        f"(must be one of {sorted(VALID_VERDICTS)})"
                    )
                elif verdict not in VALID_VERDICTS:
                    errors.append(
                        f"{country_dir.name}/capabilities.yaml: "
                        f"verticals.{vertical_name}.{provider_key}.{method} = {verdict!r} "
                        f"is not a valid verdict (must be one of {sorted(VALID_VERDICTS)})"
                    )
    return errors


def _lint_one_country(country_dir: Path) -> list[str]:
    errors: list[str] = []

    config_path = country_dir / "country.config.yaml"
    if not config_path.exists():
        return [f"{country_dir.name}/: missing country.config.yaml"]
    config = _load_yaml(config_path)
    errors.extend(_validate_against_schema(config_path, COUNTRY_CONFIG_SCHEMA))
    errors.extend(f"{country_dir.name}: unresolved placeholder at {p}" for p in _find_placeholders(config))

    caps_path = country_dir / "capabilities.yaml"
    if not caps_path.exists():
        errors.append(f"{country_dir.name}/: missing capabilities.yaml")
    else:
        capabilities = _load_yaml(caps_path)
        errors.extend(_check_capabilities(country_dir, capabilities))
        errors.extend(f"{country_dir.name}: unresolved placeholder at {p}" for p in _find_placeholders(capabilities))

    mcp_dir = country_dir / "mcp"
    if mcp_dir.is_dir():
        for mcp_file in sorted(mcp_dir.glob("*.yaml")):
            errors.extend(_validate_against_schema(mcp_file, MCP_REGISTRY_SCHEMA))

    sources_dir = country_dir / "legal-sources"
    if sources_dir.is_dir():
        for source_file in sorted(sources_dir.glob("*.yaml")):
            errors.extend(_validate_against_schema(source_file, LEGAL_SOURCE_SCHEMA))

    return errors


def main() -> int:
    if not COUNTRIES_DIR.is_dir():
        print(f"no countries/ directory at {COUNTRIES_DIR}", file=sys.stderr)
        return 2

    country_dirs = sorted(
        d for d in COUNTRIES_DIR.iterdir() if d.is_dir() and d.name != "_template"
    )
    if not country_dirs:
        print("no country plugins yet (only countries/_template/ exists) — nothing to lint, OK")
        return 0

    total_errors: list[str] = []
    for country_dir in country_dirs:
        errs = _lint_one_country(country_dir)
        if errs:
            total_errors.extend(errs)
        else:
            print(f"  ✓ {country_dir.name:8s} country plugin schema-clean")

    if total_errors:
        print("lint-country-plugin FAILED:", file=sys.stderr)
        for e in total_errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
