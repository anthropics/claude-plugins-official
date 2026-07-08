"""Plugin Dependency: two distinct dependency concerns the engine resolves.

  1. Capability dependency -- does a country plugin satisfy a Core
     Vertical's declared needs (<vertical>/extension-points.yaml vs
     countries/<code>/capabilities.yaml)? See `resolve_capability_coverage`.
  2. Load-order dependency -- if a plugin ever declares
     `plugin.json["depends_on"] = ["other-plugin-name"]` (no plugin in this
     repo does yet -- the field is optional and forward-looking), what
     order must plugins load in, and are there missing/cyclic
     dependencies? See `resolve_load_order`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .errors import DependencyError
from .manifest import PluginKind, PluginManifest

_PROVIDER_KEYS = ("citation_provider", "search_provider", "document_provider")


class CoverageVerdict(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    MISSING = "missing"


@dataclass
class CapabilityCoverageReport:
    vertical_name: str
    country_code: str
    verdicts: dict[str, str] = field(default_factory=dict)  # "provider.method" -> full/partial/not_supported
    missing: list[str] = field(default_factory=list)

    @property
    def overall(self) -> CoverageVerdict:
        if self.missing:
            return CoverageVerdict.MISSING
        if not self.verdicts:
            return CoverageVerdict.FULL  # nothing required -> trivially satisfied
        values = set(self.verdicts.values())
        if values == {"full"}:
            return CoverageVerdict.FULL
        return CoverageVerdict.PARTIAL


def resolve_capability_coverage(
    vertical: PluginManifest, country: PluginManifest
) -> CapabilityCoverageReport:
    """Compare what `vertical` needs (extension-points.yaml) against what
    `country` declares it provides (capabilities.yaml) for that vertical.
    """
    if vertical.kind is not PluginKind.VERTICAL:
        raise DependencyError(f"{vertical.name} is not a vertical plugin")
    if country.kind is not PluginKind.COUNTRY:
        raise DependencyError(f"{country.name} is not a country plugin")

    report = CapabilityCoverageReport(
        vertical_name=vertical.name, country_code=country.country_code or "?"
    )

    providers_needed = (vertical.extension_points or {}).get("providers", {})
    country_verticals = (country.capabilities or {}).get("verticals", {})
    declared = country_verticals.get(vertical.name)

    if not providers_needed:
        return report  # vertical hasn't declared any requirements -- trivially FULL

    if declared is None:
        report.missing.append(
            f"{country.name} declares no capabilities for vertical {vertical.name!r}"
        )
        return report

    for provider_key, spec in providers_needed.items():
        if not spec.get("required", False):
            continue
        methods = spec.get("methods_used", [])
        declared_methods = declared.get(provider_key, {})
        for method in methods:
            verdict = declared_methods.get(method)
            if verdict is None:
                report.missing.append(f"{provider_key}.{method}")
            else:
                report.verdicts[f"{provider_key}.{method}"] = verdict

    return report


# --- Load-order dependency graph (generic; unused by any plugin today) ---


def resolve_load_order(manifests: list[PluginManifest]) -> list[PluginManifest]:
    """Topologically sort `manifests` by each one's optional
    `plugin_json["depends_on"]` list of plugin names. Plugins with no
    dependency declaration load in name order relative to their peers.

    Raises DependencyError on a dependency naming an unknown plugin, or on
    a circular dependency.
    """
    by_name = {m.name: m for m in manifests}
    in_degree = {m.name: 0 for m in manifests}
    edges: dict[str, list[str]] = {m.name: [] for m in manifests}

    for m in manifests:
        for dep_name in m.plugin_json.get("depends_on", []) or []:
            if dep_name not in by_name:
                raise DependencyError(f"{m.name} depends on unknown plugin {dep_name!r}")
            edges[dep_name].append(m.name)
            in_degree[m.name] += 1

    ready = sorted(name for name, deg in in_degree.items() if deg == 0)
    ordered: list[str] = []
    while ready:
        ready.sort()
        current = ready.pop(0)
        ordered.append(current)
        for dependent in edges[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                ready.append(dependent)

    if len(ordered) != len(manifests):
        remaining = sorted(set(by_name) - set(ordered))
        raise DependencyError(f"circular dependency detected among: {remaining}")

    return [by_name[name] for name in ordered]
