"""Plugin Configuration: the small piece of runtime state the engine
itself owns -- which country is currently active.

This mirrors core/engine/plugin-loader/active-country.template.yaml. In
production the real pointer file lives under the user's Claude Code config
directory (~/.claude/plugins/config/claude-for-legal/active-country.yaml);
this module accepts that path as a parameter so it is fully testable
without touching a real home directory, and so the engine itself never
hardcodes a user-specific path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ActiveCountryPointer:
    active_country: str | None
    installed_country_plugins: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "ActiveCountryPointer":
        return cls(active_country=None, installed_country_plugins=[], raw={})


def load_active_country(pointer_path: Path) -> ActiveCountryPointer:
    """Read the active-country pointer file.

    A missing file is NOT an error -- it means no country plugin has ever
    been activated, which is the valid default state every backward-
    compatibility guarantee in this repo's migration plan depends on.
    """
    if not pointer_path.exists():
        return ActiveCountryPointer.empty()
    raw = yaml.safe_load(pointer_path.read_text(encoding="utf-8")) or {}
    return ActiveCountryPointer(
        active_country=raw.get("active_country"),
        installed_country_plugins=list(raw.get("installed_country_plugins", [])),
        raw=raw,
    )


def set_active_country(pointer_path: Path, country_code: str, plugin_version: str = "0.0.0") -> None:
    """Write (or overwrite) the active-country pointer file, creating its
    parent directory if needed."""
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "active_country": country_code,
        "set_by": {
            "plugin": f"countries/{country_code.lower()}",
            "plugin_version": plugin_version,
            "set_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "installed_country_plugins": [country_code],
    }
    pointer_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
