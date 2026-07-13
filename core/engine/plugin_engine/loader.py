"""Plugin Loader: the end-to-end entry point that ties Discovery, Manifest,
Validation, Dependency, Lifecycle, and the five Registries together into
one runtime pass over a repository.

This module (and every module it imports in this package) never imports or
references a specific plugin by name. Every plugin directory it touches
was found by discovery.py at run time. This is the concrete enforcement of
"Core plugin'lerden bagimsiz olmali" -- delete any plugin directory, add a
new one, rename one, and nothing in core/engine/plugin_engine/ changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import dependency as dep
from .discovery import discover_plugin_dirs
from .errors import PluginEngineError, VersionError
from .frontmatter import parse_frontmatter
from .lifecycle import LifecycleState, PluginLifecycle
from .manifest import PluginKind, PluginManifest, load_manifest
from .registry import CountryRegistry, PluginRegistry, ProviderRegistry, PromptRegistry, ToolRegistry
from .validation import validate_manifest
from .versioning import is_interface_compatible

_PROVIDER_KEYS = ("citation_provider", "search_provider", "document_provider")

_INTERFACE_FILES = {
    "citation_provider": "citation-provider.interface.md",
    "search_provider": "search-provider.interface.md",
    "document_provider": "document-provider.interface.md",
}

# core/engine/plugin_engine/loader.py -> parents: plugin_engine, engine, core
_CORE_DIR = Path(__file__).resolve().parent.parent.parent
_ENGINE_DIR = _CORE_DIR / "engine"
_GUARDRAIL_FRAGMENTS_DIR = _CORE_DIR / "shared" / "guardrail-fragments"
_PROVIDER_INTERFACES_DIR = _ENGINE_DIR / "providers"


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    lifecycle: PluginLifecycle
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class EngineReport:
    loaded: list[LoadedPlugin]
    coverage: list[dep.CapabilityCoverageReport]
    skill_count: int
    guardrail_fragment_count: int

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        by_kind: dict[str, int] = {}
        for lp in self.loaded:
            by_kind[lp.manifest.kind.value] = by_kind.get(lp.manifest.kind.value, 0) + 1
        lines.append(
            "Discovered "
            + ", ".join(f"{n} {k}" for k, n in sorted(by_kind.items()))
            + f" plugin(s) | {self.skill_count} skill(s) registered | "
            f"{self.guardrail_fragment_count} guardrail fragment(s) registered"
        )
        for lp in self.loaded:
            marker = "OK  " if lp.lifecycle.state is LifecycleState.ACTIVE else "FAIL"
            lines.append(
                f"  [{marker}] {lp.manifest.name} ({lp.manifest.kind.value}) "
                f"v{lp.manifest.version} -> {lp.lifecycle.state.value}"
            )
            for e in lp.errors:
                lines.append(f"          error:   {e}")
            for w in lp.warnings:
                lines.append(f"          warning: {w}")
        if self.coverage:
            lines.append("Capability coverage (Core Vertical x Country Plugin):")
            for c in self.coverage:
                lines.append(f"  {c.vertical_name} x {c.country_code}: {c.overall.value}")
                for missing in c.missing:
                    lines.append(f"      missing: {missing}")
        return lines


class PluginEngine:
    """Owns the five registries and runs the full
    discover -> load -> validate -> register -> activate pipeline over a
    repository root."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.plugins = PluginRegistry()
        self.countries = CountryRegistry()
        self.prompts = PromptRegistry()
        self.tools = ToolRegistry()
        self.providers = ProviderRegistry()

    def load_all(self) -> EngineReport:
        self._register_guardrail_fragments()

        loaded: list[LoadedPlugin] = [
            self._load_one(plugin_dir) for plugin_dir in discover_plugin_dirs(self.repo_root)
        ]
        coverage = self._resolve_all_coverage(loaded)

        return EngineReport(
            loaded=loaded,
            coverage=coverage,
            skill_count=len(self.prompts.all_skills()),
            guardrail_fragment_count=len(self.prompts.guardrail_fragment_ids()),
        )

    # --- per-plugin pipeline -------------------------------------------------

    def _load_one(self, plugin_dir: Path) -> LoadedPlugin:
        lifecycle = PluginLifecycle(plugin_name=plugin_dir.name)

        try:
            manifest = load_manifest(plugin_dir)
        except PluginEngineError as exc:
            lifecycle.transition(LifecycleState.FAILED, note=str(exc))
            return LoadedPlugin(
                manifest=PluginManifest(
                    path=plugin_dir,
                    kind=PluginKind.VERTICAL,
                    name=plugin_dir.name,
                    version="0.0.0",
                    description="",
                    author="",
                    plugin_json={},
                ),
                lifecycle=lifecycle,
                errors=[str(exc)],
            )

        lifecycle.plugin_name = manifest.name
        lifecycle.transition(LifecycleState.MANIFEST_LOADED)

        validation_errors = validate_manifest(manifest)
        if validation_errors:
            lifecycle.transition(LifecycleState.FAILED, note="manifest validation failed")
            return LoadedPlugin(manifest=manifest, lifecycle=lifecycle, errors=validation_errors)
        lifecycle.transition(LifecycleState.VALIDATED)

        try:
            self._register(manifest)
        except PluginEngineError as exc:
            lifecycle.transition(LifecycleState.FAILED, note=str(exc))
            return LoadedPlugin(manifest=manifest, lifecycle=lifecycle, errors=[str(exc)])
        lifecycle.transition(LifecycleState.REGISTERED)
        lifecycle.transition(LifecycleState.ACTIVE)

        warnings = self._check_provider_versions(manifest) if manifest.kind is PluginKind.COUNTRY else []
        return LoadedPlugin(manifest=manifest, lifecycle=lifecycle, warnings=warnings)

    # --- registration ---------------------------------------------------------

    def _register(self, manifest: PluginManifest) -> None:
        self.plugins.register(manifest)

        if manifest.kind is PluginKind.COUNTRY:
            self.countries.register(manifest)
            self._register_country_providers(manifest)
            self._register_country_tool_bindings(manifest)
        else:
            # VERTICAL and VENDOR plugins both expose skills/ the same way.
            self._register_plugin_skills(manifest)
            if manifest.kind is PluginKind.VERTICAL:
                self._register_vertical_tool_requirements(manifest)

    def _register_guardrail_fragments(self) -> None:
        if not _GUARDRAIL_FRAGMENTS_DIR.is_dir():
            return
        for path in sorted(_GUARDRAIL_FRAGMENTS_DIR.glob("*.md")):
            if path.name == "README.md":
                continue
            meta, _ = parse_frontmatter(path)
            fragment_id = str(meta.get("fragment_id", path.stem))
            self.prompts.register_guardrail_fragment(fragment_id, path)

    def _register_country_providers(self, manifest: PluginManifest) -> None:
        code = manifest.country_code
        if not code:
            return
        default_providers = (manifest.country_config or {}).get("default_providers", {})
        for provider_key in _PROVIDER_KEYS:
            rel_path = default_providers.get(provider_key)
            if not rel_path:
                continue
            self.providers.register(provider_key, code, manifest.path / rel_path)

    def _register_country_tool_bindings(self, manifest: PluginManifest) -> None:
        code = manifest.country_code
        if not code:
            return
        mcp_dir = manifest.path / "mcp"
        if not mcp_dir.is_dir():
            return
        for mcp_file in sorted(mcp_dir.glob("*.yaml")):
            data = yaml.safe_load(mcp_file.read_text(encoding="utf-8")) or {}
            for binding in data.get("bindings", []):
                capability_id = binding.get("capability_id")
                if capability_id:
                    self.tools.register_binding(capability_id, code, binding)

    def _register_plugin_skills(self, manifest: PluginManifest) -> None:
        skills_dir = manifest.path / "skills"
        if not skills_dir.is_dir():
            return
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            self.prompts.register_skill(manifest.name, skill_dir)

    def _register_vertical_tool_requirements(self, manifest: PluginManifest) -> None:
        if not manifest.extension_points:
            return
        for cap in manifest.extension_points.get("tool_capabilities", []):
            capability_id = cap.get("capability_id")
            if capability_id:
                self.tools.register_requirement(capability_id, manifest.name)

    # --- versioning ------------------------------------------------------------

    def _interface_version(self, provider_key: str) -> str | None:
        path = _PROVIDER_INTERFACES_DIR / _INTERFACE_FILES[provider_key]
        if not path.exists():
            return None
        meta, _ = parse_frontmatter(path)
        version = meta.get("version")
        return str(version) if version is not None else None

    def _check_provider_versions(self, manifest: PluginManifest) -> list[str]:
        warnings: list[str] = []
        declared = (manifest.capabilities or {}).get("provider_versions", {})
        for provider_key, declared_version in declared.items():
            required_version = self._interface_version(provider_key)
            if not required_version:
                continue
            try:
                if not is_interface_compatible(required_version, declared_version):
                    warnings.append(
                        f"{provider_key}: capabilities.yaml declares {declared_version}, "
                        f"older than the interface's {required_version}"
                    )
            except VersionError as exc:
                warnings.append(f"{provider_key}: {exc}")
        return warnings

    # --- dependency --------------------------------------------------------

    def _resolve_all_coverage(self, loaded: list[LoadedPlugin]) -> list[dep.CapabilityCoverageReport]:
        verticals = [
            lp.manifest
            for lp in loaded
            if lp.manifest.kind is PluginKind.VERTICAL
            and lp.manifest.extension_points
            and lp.lifecycle.state is LifecycleState.ACTIVE
        ]
        countries = [
            lp.manifest
            for lp in loaded
            if lp.manifest.kind is PluginKind.COUNTRY and lp.lifecycle.state is LifecycleState.ACTIVE
        ]
        return [
            dep.resolve_capability_coverage(vertical, country)
            for vertical in verticals
            for country in countries
        ]
