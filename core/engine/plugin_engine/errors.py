"""Exception hierarchy for the Plugin Engine.

All engine-raised errors derive from PluginEngineError so callers can catch
broadly (`except PluginEngineError`) or narrowly (`except ManifestError`).
Named `PluginValidationError` (not `ValidationError`) to avoid shadowing
`jsonschema.ValidationError` when both are imported in the same module.
"""
from __future__ import annotations


class PluginEngineError(Exception):
    """Base class for every error the plugin engine raises."""


class DiscoveryError(PluginEngineError):
    """Raised when the filesystem scan for plugins cannot proceed."""


class ManifestError(PluginEngineError):
    """Raised when a plugin's manifest (plugin.json + kind-specific files)
    is missing, malformed, or unreadable."""


class PluginValidationError(PluginEngineError):
    """Raised when a plugin's manifest fails schema validation and the
    caller asked for a hard failure rather than a list of error strings."""

    def __init__(self, plugin_name: str, messages: list[str]):
        self.plugin_name = plugin_name
        self.messages = messages
        super().__init__(
            f"{plugin_name}: {len(messages)} validation error(s): " + "; ".join(messages)
        )


class VersionError(PluginEngineError):
    """Raised when a version string cannot be parsed or is incompatible."""


class DependencyError(PluginEngineError):
    """Raised when a plugin dependency graph has a missing or cyclic
    dependency and cannot be resolved into a load order, or when capability
    coverage is requested between two manifests of the wrong kind."""


class RegistrationError(PluginEngineError):
    """Raised when registering a plugin/country/provider/tool/prompt would
    collide with an already-registered entry of the same key."""


class LifecycleError(PluginEngineError):
    """Raised when an illegal plugin lifecycle state transition is attempted."""
