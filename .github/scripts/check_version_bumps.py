#!/usr/bin/env python3
"""Fail when a vendored plugin changes without a version bump.

Usage: check_version_bumps.py <base-sha> <head-sha>

Claude Code decides whether an installed plugin has an update by comparing
version strings. A plugin that declares a version keeps its old content on
every install until that string changes, so a merged fix never reaches the
people who already have it. A plugin that declares no version is versioned by
commit and updates on every commit, so it's skipped here.

The version comes from the same places the client reads, in the same order:
the plugin's own .claude-plugin/plugin.json, then its marketplace entry.
"""

import functools
import json
import subprocess
import sys

PLUGIN_ROOTS = ("plugins", "external_plugins")
MARKETPLACE = ".claude-plugin/marketplace.json"
# Marketplace entry keys that define what a plugin does. The LSP plugins have
# nothing else: their directories hold only a README and a LICENSE.
COMPONENT_KEYS = ("agents", "commands", "hooks", "lspServers", "mcpServers", "skills")
IMAGE_SUFFIXES = (".gif", ".jpeg", ".jpg", ".png")
# Plugins that land several changes and then bump once for a release, so a
# change with no bump is expected rather than a missed update.
BATCHED_RELEASES = {"plugins/security-guidance"}


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr}")
    return result


@functools.cache
def read_json(ref, path):
    """Return the object at path, or None if it's missing or isn't valid."""
    result = git("show", f"{ref}:{path}", check=False)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def marketplace_entries(ref):
    """Map each vendored plugin directory to its marketplace entry."""
    entries = {}
    for entry in (read_json(ref, MARKETPLACE) or {}).get("plugins", []):
        source = entry.get("source")
        if isinstance(source, str):
            entries[source.removeprefix("./").rstrip("/")] = entry
    return entries


def effective_version(ref, plugin_dir):
    manifest = read_json(ref, f"{plugin_dir}/.claude-plugin/plugin.json") or {}
    if manifest.get("version"):
        return manifest["version"]
    return marketplace_entries(ref).get(plugin_dir, {}).get("version")


def is_doc(relative):
    """Whether a file can't change what an installed plugin does."""
    if relative == "LICENSE" or relative.startswith("tests/"):
        return True
    if "/" not in relative and relative.endswith(".md"):
        return True
    return relative.endswith(IMAGE_SUFFIXES)


def changed_plugins(base, head):
    """Map each plugin directory to what changed in it, docs left out."""
    changed = {}
    names = git("diff", "-z", "--name-only", "--no-renames", f"{base}...{head}")
    for path in names.stdout.split("\0"):
        parts = path.split("/")
        if len(parts) < 3 or parts[0] not in PLUGIN_ROOTS:
            continue
        relative = "/".join(parts[2:])
        if not is_doc(relative):
            changed.setdefault("/".join(parts[:2]), []).append(relative)

    old_entries = marketplace_entries(base)
    for plugin_dir, entry in marketplace_entries(head).items():
        old = old_entries.get(plugin_dir, {})
        if any(entry.get(key) != old.get(key) for key in COMPONENT_KEYS):
            changed.setdefault(plugin_dir, []).append(MARKETPLACE)
    return changed


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    base, head = sys.argv[1:]
    merge_base = git("merge-base", base, head).stdout.strip()

    failures = []
    for plugin_dir, files in sorted(changed_plugins(merge_base, head).items()):
        if plugin_dir in BATCHED_RELEASES:
            continue
        version = effective_version(head, plugin_dir)
        # The base tip counts too: another PR may have merged the same bump,
        # and two different changes under one version reach nobody twice.
        old = (effective_version(merge_base, plugin_dir), effective_version(base, plugin_dir))
        if version is not None and version in old:
            failures.append((plugin_dir, version, files))

    for plugin_dir, version, files in failures:
        print(
            f"::error title=Missing version bump::{plugin_dir} changed but is "
            f"still version {version}. People who have it installed won't get "
            "this change until the version does. Bump it in the plugin's "
            "plugin.json, or in its marketplace entry if plugin.json has no "
            f"version. {len(files)} changed, including {', '.join(files[:5])}"
        )
    if failures:
        sys.exit(1)
    print("Every changed plugin with a version has a new one.")


if __name__ == "__main__":
    main()
