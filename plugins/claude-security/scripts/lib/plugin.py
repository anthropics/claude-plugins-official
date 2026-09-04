"""The plugin's fixed names, and its own manifest."""

from __future__ import annotations

import re
from pathlib import Path

from . import strictjson
from .strictjson import is_map, is_str

NAME = "claude-security"
ROOT = Path(__file__).resolve().parents[2]
RUN_DIR_NAME = ".claude-security-run"
TARGET_FILES_NAME = "target-files.json"
# Set only by workflows/scan.js (its PROVENANCE) on each vote record it computes.
VOTES_PROVENANCE = "workflows/scan.js"
MODES = ("scan", "changes", "commit")
REPORT_DIR_PREFIX = "CLAUDE-SECURITY-"
# \Z, not $: `$` also matches before a trailing newline, and this id names product files.
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,64}\Z")


def version() -> str | None:
    """The non-blank version string in the plugin's manifest, or None when there is not one."""
    try:
        manifest = strictjson.load(ROOT / ".claude-plugin" / "plugin.json")
    except (OSError, ValueError):
        return None
    if not is_map(manifest):
        return None
    declared = manifest.get("version")
    if not is_str(declared):
        return None
    return declared.strip() or None
