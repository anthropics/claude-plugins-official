"""Plugin/Country/Prompt/Tool/Provider Registration.

Five focused, in-memory registries the Loader populates as it processes
plugins. Each raises RegistrationError on a duplicate key rather than
silently overwriting -- a collision almost always means two plugins are
fighting over the same name/capability/country code, which the operator
needs to know about, not have silently resolved one way or the other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .errors import RegistrationError
from .frontmatter import parse_frontmatter
from .manifest import PluginManifest


@dataclass
class PluginRegistry:
    """Registry of every successfully loaded plugin, keyed by name."""

    _plugins: dict[str, PluginManifest] = field(default_factory=dict)

    def register(self, manifest: PluginManifest) -> None:
        if manifest.name in self._plugins:
            raise RegistrationError(f"duplicate plugin name: {manifest.name!r}")
        self._plugins[manifest.name] = manifest

    def get(self, name: str) -> PluginManifest | None:
        return self._plugins.get(name)

    def all(self) -> list[PluginManifest]:
        return sorted(self._plugins.values(), key=lambda m: m.name)


@dataclass
class CountryRegistry:
    """Registry of every loaded country plugin, keyed by ISO country code."""

    _countries: dict[str, PluginManifest] = field(default_factory=dict)

    def register(self, manifest: PluginManifest) -> None:
        code = manifest.country_code
        if not code:
            raise RegistrationError(f"{manifest.name}: country plugin has no country_code")
        if code in self._countries:
            raise RegistrationError(f"duplicate country_code: {code!r}")
        self._countries[code] = manifest

    def get(self, code: str) -> PluginManifest | None:
        return self._countries.get(code)

    def all_codes(self) -> list[str]:
        return sorted(self._countries)


@dataclass
class SkillRecord:
    plugin_name: str
    skill_id: str
    name: str
    description: str
    path: Path


@dataclass
class PromptRegistry:
    """Registry of every skill (from any plugin kind with a skills/ dir)
    and every canonical guardrail fragment under core/shared/guardrail-fragments/.
    """

    _skills: dict[str, SkillRecord] = field(default_factory=dict)
    _guardrail_fragments: dict[str, Path] = field(default_factory=dict)

    def register_skill(self, plugin_name: str, skill_dir: Path) -> None:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return
        meta, _ = parse_frontmatter(skill_md)
        skill_id = skill_dir.name
        key = f"{plugin_name}:{skill_id}"
        if key in self._skills:
            raise RegistrationError(f"duplicate skill registration: {key!r}")
        self._skills[key] = SkillRecord(
            plugin_name=plugin_name,
            skill_id=skill_id,
            name=str(meta.get("name", skill_id)),
            description=str(meta.get("description", "")).strip(),
            path=skill_md,
        )

    def register_guardrail_fragment(self, fragment_id: str, path: Path) -> None:
        if fragment_id in self._guardrail_fragments:
            raise RegistrationError(f"duplicate guardrail fragment: {fragment_id!r}")
        self._guardrail_fragments[fragment_id] = path

    def skills_for(self, plugin_name: str) -> list[SkillRecord]:
        return sorted(
            (s for s in self._skills.values() if s.plugin_name == plugin_name),
            key=lambda s: s.skill_id,
        )

    def all_skills(self) -> list[SkillRecord]:
        return sorted(self._skills.values(), key=lambda s: (s.plugin_name, s.skill_id))

    def guardrail_fragment_ids(self) -> list[str]:
        return sorted(self._guardrail_fragments)


@dataclass
class ToolCapability:
    capability_id: str
    required_by: set[str] = field(default_factory=set)
    bound_countries: dict[str, list[dict]] = field(default_factory=dict)


@dataclass
class ToolRegistry:
    """Registry of abstract capability_id's (from Core Vertical
    extension-points.yaml) and their concrete per-country MCP bindings
    (from countries/<code>/mcp/*.yaml)."""

    _capabilities: dict[str, ToolCapability] = field(default_factory=dict)

    def register_requirement(self, capability_id: str, plugin_name: str) -> None:
        cap = self._capabilities.setdefault(capability_id, ToolCapability(capability_id))
        cap.required_by.add(plugin_name)

    def register_binding(self, capability_id: str, country_code: str, binding: dict) -> None:
        cap = self._capabilities.setdefault(capability_id, ToolCapability(capability_id))
        cap.bound_countries.setdefault(country_code, []).append(binding)

    def get(self, capability_id: str) -> ToolCapability | None:
        return self._capabilities.get(capability_id)

    def all(self) -> list[ToolCapability]:
        return sorted(self._capabilities.values(), key=lambda c: c.capability_id)


@dataclass
class ProviderBinding:
    provider_type: str  # "citation_provider" | "search_provider" | "document_provider"
    country_code: str
    definition_path: Path


@dataclass
class ProviderRegistry:
    """Registry mapping (provider_type, country_code) -> the concrete
    Provider implementation definition file for that country."""

    _bindings: dict[tuple[str, str], ProviderBinding] = field(default_factory=dict)

    def register(self, provider_type: str, country_code: str, definition_path: Path) -> None:
        key = (provider_type, country_code)
        if key in self._bindings:
            raise RegistrationError(f"duplicate provider binding: {provider_type}/{country_code}")
        self._bindings[key] = ProviderBinding(provider_type, country_code, definition_path)

    def resolve(self, provider_type: str, country_code: str) -> ProviderBinding | None:
        return self._bindings.get((provider_type, country_code))

    def all(self) -> list[ProviderBinding]:
        return sorted(self._bindings.values(), key=lambda b: (b.provider_type, b.country_code))
