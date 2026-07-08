"""Plugin Engine: discovers, loads, validates, and registers every plugin
(Core Vertical, Country, or Vendor) found under a repository root, at
runtime, with zero hardcoded plugin names.

Public API:

    from core.engine.plugin_engine import PluginEngine
    engine = PluginEngine(repo_root)
    report = engine.load_all()
    print("\\n".join(report.summary_lines()))

See README.md in this directory for the full architecture write-up, and
run `python -m core.engine.plugin_engine` from the repo root for a live
report against the actual repository.
"""

from .config import ActiveCountryPointer, load_active_country, set_active_country
from .dependency import CapabilityCoverageReport, CoverageVerdict, resolve_capability_coverage, resolve_load_order
from .discovery import discover_plugin_dirs
from .errors import (
    DependencyError,
    DiscoveryError,
    LifecycleError,
    ManifestError,
    PluginEngineError,
    PluginValidationError,
    RegistrationError,
    VersionError,
)
from .lifecycle import LifecycleState, PluginLifecycle
from .loader import EngineReport, LoadedPlugin, PluginEngine
from .manifest import PluginKind, PluginManifest, load_manifest
from .registry import (
    CountryRegistry,
    PluginRegistry,
    ProviderBinding,
    ProviderRegistry,
    SkillRecord,
    ToolCapability,
    ToolRegistry,
    PromptRegistry,
)
from .validation import validate_manifest
from .versioning import InterfaceVersion, SemVer, is_interface_compatible

__all__ = [
    "ActiveCountryPointer",
    "load_active_country",
    "set_active_country",
    "CapabilityCoverageReport",
    "CoverageVerdict",
    "resolve_capability_coverage",
    "resolve_load_order",
    "discover_plugin_dirs",
    "DependencyError",
    "DiscoveryError",
    "LifecycleError",
    "ManifestError",
    "PluginEngineError",
    "PluginValidationError",
    "RegistrationError",
    "VersionError",
    "LifecycleState",
    "PluginLifecycle",
    "EngineReport",
    "LoadedPlugin",
    "PluginEngine",
    "PluginKind",
    "PluginManifest",
    "load_manifest",
    "CountryRegistry",
    "PluginRegistry",
    "ProviderBinding",
    "ProviderRegistry",
    "SkillRecord",
    "ToolCapability",
    "ToolRegistry",
    "PromptRegistry",
    "validate_manifest",
    "InterfaceVersion",
    "SemVer",
    "is_interface_compatible",
]
