"""Plugin Versioning: parse and compare the two version schemes used in
this repo.

  - Plugin release version: semantic-ish `MAJOR.MINOR.PATCH` in every
    plugin.json (e.g. "1.1.0").
  - Provider interface version: a dated tag `@YYYY-MM` (e.g. "@2026-07"),
    declared by core/engine/providers/*.interface.md's frontmatter and
    referenced by countries/<code>/capabilities.yaml's `provider_versions`
    block.

Neither scheme is invented by this module -- both already exist in the
repo's real files; this module only knows how to read and compare them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import VersionError

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_INTERFACE_VERSION_RE = re.compile(r"^@(\d{4})-(\d{2})$")


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str) -> "SemVer":
        match = _SEMVER_RE.match(raw.strip())
        if not match:
            raise VersionError(f"not a valid MAJOR.MINOR.PATCH version: {raw!r}")
        major, minor, patch = (int(g) for g in match.groups())
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True, order=True)
class InterfaceVersion:
    year: int
    month: int

    @classmethod
    def parse(cls, raw: str) -> "InterfaceVersion":
        match = _INTERFACE_VERSION_RE.match(raw.strip())
        if not match:
            raise VersionError(f"not a valid @YYYY-MM interface version: {raw!r}")
        year, month = (int(g) for g in match.groups())
        return cls(year, month)

    def __str__(self) -> str:
        return f"@{self.year:04d}-{self.month:02d}"


def is_interface_compatible(required: str, provided: str) -> bool:
    """A provided interface version is compatible with a required one if
    it is the same or newer (later year-month).

    This is a deliberately simple, conservative policy -- see
    core/engine/providers/CONVENTIONS.md section 1 for the versioning
    policy it encodes. Raises VersionError if either string doesn't parse.
    """
    return InterfaceVersion.parse(provided) >= InterfaceVersion.parse(required)
