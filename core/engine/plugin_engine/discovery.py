"""Plugin Discovery: find installable plugin directories on disk.

Discovery is purely structural -- it looks for the one file every plugin
kind must have (.claude-plugin/plugin.json) under the conventional
locations this repo's marketplace uses (repo root, countries/, and
external_plugins/). It never hardcodes a plugin name, so a newly added
plugin directory is picked up automatically the next time discovery runs.
This is the concrete meaning of "her plugin runtime sirasinda
yuklenebilmeli" (every plugin must be loadable at runtime): nothing in
this module needs to change for a new plugin to be discovered and loaded.
"""
from __future__ import annotations

from pathlib import Path

from .errors import DiscoveryError
from .manifest import PLUGIN_JSON_REL_PATH

#: Top-level directories that hold *collections* of plugins rather than
#: being a plugin themselves. Their immediate children are scanned instead
#: of the directory itself.
_CONTAINER_DIRS = {"countries", "external_plugins"}

#: Directory name prefixes that are never plugins (templates, dotfiles,
#: private/underscore-prefixed scratch directories such as countries/_template).
_IGNORED_PREFIXES = (".", "_")


def _is_plugin_dir(path: Path) -> bool:
    return (path / PLUGIN_JSON_REL_PATH).is_file()


def discover_plugin_dirs(repo_root: Path) -> list[Path]:
    """Return every plugin directory found under `repo_root`, sorted for
    deterministic output.

    Raises DiscoveryError if repo_root doesn't exist or isn't a directory.
    """
    if not repo_root.is_dir():
        raise DiscoveryError(f"repo root does not exist or is not a directory: {repo_root}")

    found: list[Path] = []
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir() or child.name.startswith(_IGNORED_PREFIXES):
            continue
        if child.name in _CONTAINER_DIRS:
            for grandchild in sorted(child.iterdir()):
                if not grandchild.is_dir() or grandchild.name.startswith(_IGNORED_PREFIXES):
                    continue
                if _is_plugin_dir(grandchild):
                    found.append(grandchild)
            continue
        if _is_plugin_dir(child):
            found.append(child)
    return sorted(found)
