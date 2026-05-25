#!/usr/bin/env python3
"""Discover plugins in marketplace.json whose upstream repo has moved past
their pinned SHA, update the file in place, and emit a summary.

Adapted from claude-plugins-community-internal's discover_bumps.py for the
single-file marketplace.json format used by claude-plugins-official.

Usage: discover_bumps.py [--plugin NAME] [--max N] [--dry-run]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


MARKETPLACE_PATH = ".claude-plugin/marketplace.json"


def gh_api(path: str) -> Any:
    """GET from the GitHub API. None on not-found; raises on other errors.

    "Not found" covers both 404 (resource gone) and 422 "No commit found
    for SHA" (force-pushed away). Both mean the thing we asked for isn't
    there — treating them the same lets callers handle dead refs uniformly.
    """
    r = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True
    )
    if r.returncode != 0:
        combined = r.stdout + r.stderr
        if any(s in combined for s in ("404", "Not Found", "No commit found")):
            return None
        raise RuntimeError(f"gh api {path}: {r.stderr.strip() or r.stdout.strip()}")
    return json.loads(r.stdout)


def parse_github_repo(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a URL or owner/repo shorthand."""
    # Full URL: https://github.com/owner/repo(.git)(/...)
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", url)
    if m:
        return m.group(1), m.group(2)
    # Shorthand: owner/repo
    m = re.match(r"^([\w.-]+)/([\w.-]+)$", url)
    if m:
        return m.group(1), m.group(2)
    return None


def latest_sha(owner: str, repo: str, *, ref: str | None, path: str | None) -> str | None:
    """Latest commit SHA for the repo, optionally scoped to a ref and/or path."""
    if path:
        # Scoped to a subdirectory — use the commits list endpoint with path filter.
        q = f"repos/{owner}/{repo}/commits?per_page=1&path={path}"
        if ref:
            q += f"&sha={ref}"
        commits = gh_api(q)
        if not commits:
            return None
        return commits[0]["sha"]
    # Whole repo — the single-ref endpoint is cheaper.
    if not ref:
        meta = gh_api(f"repos/{owner}/{repo}")
        if not meta:
            return None
        ref = meta["default_branch"]
    c = gh_api(f"repos/{owner}/{repo}/commits/{ref}")
    return c["sha"] if c else None


def pinned_age_days(owner: str, repo: str, sha: str) -> int | None:
    """Days since the pinned commit was authored. Used for oldest-first rotation."""
    c = gh_api(f"repos/{owner}/{repo}/commits/{sha}")
    if not c:
        return None
    dt = datetime.fromisoformat(
        c["commit"]["committer"]["date"].replace("Z", "+00:00")
    )
    return (datetime.now(timezone.utc) - dt).days


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", help="only check this plugin")
    ap.add_argument("--max", type=int, default=20, help="cap bumps emitted")
    ap.add_argument("--dry-run", action="store_true", help="don't write marketplace.json")
    args = ap.parse_args()

    with open(MARKETPLACE_PATH) as f:
        marketplace = json.load(f)

    plugins = marketplace.get("plugins", [])
    bumps: list[dict] = []
    dead: list[str] = []
    skipped_non_github = 0
    checked = 0

    for plugin in plugins:
        name = plugin.get("name", "?")
        src = plugin.get("source")

        # Only process object sources with a sha field
        if not isinstance(src, dict) or "sha" not in src:
            continue

        # Filter to specific plugin if requested
        if args.plugin and name != args.plugin:
            continue

        checked += 1
        kind = src.get("source")
        url = src.get("url", "")
        path = src.get("path")
        ref = src.get("ref")
        pinned = src.get("sha")

        slug = parse_github_repo(url)
        if not slug:
            skipped_non_github += 1
            continue
        owner, repo = slug

        try:
            latest = latest_sha(owner, repo, ref=ref, path=path)
        except RuntimeError as e:
            print(f"::warning::{name}: {e}", file=sys.stderr)
            continue

        if latest is None:
            dead.append(f"{name} ({owner}/{repo})")
            continue

        if latest == pinned:
            continue  # up to date

        # Age lookup for rotation — oldest-pinned first prevents starvation.
        try:
            age = pinned_age_days(owner, repo, pinned) if pinned else None
        except RuntimeError as e:
            print(f"::warning::{name}: age lookup failed: {e}", file=sys.stderr)
            age = None

        bumps.append({
            "name": name,
            "kind": kind,
            "url": url,
            "path": path or "",
            "ref": ref or "",
            "old_sha": pinned or "",
            "new_sha": latest,
            "age_days": age if age is not None else 10**6,
        })

    # Oldest-pinned first so nothing starves under the cap.
    bumps.sort(key=lambda b: -b["age_days"])
    emitted = bumps[: args.max]

    # Apply bumps to marketplace data
    if emitted and not args.dry_run:
        bump_map = {b["name"]: b["new_sha"] for b in emitted}
        for plugin in plugins:
            name = plugin.get("name")
            src = plugin.get("source")
            if isinstance(src, dict) and name in bump_map:
                src["sha"] = bump_map[name]

        with open(MARKETPLACE_PATH, "w") as f:
            json.dump(marketplace, f, indent=2, ensure_ascii=False)
            f.write("\n")

    # Write GitHub outputs
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        bumped_names = ",".join(b["name"] for b in emitted)
        with open(out, "a") as fh:
            fh.write(f"count={len(emitted)}\n")
            fh.write(f"bumped_names={bumped_names}\n")

    # Write GitHub step summary
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write("## SHA Bump Discovery\n\n")
            fh.write(f"- Checked: {checked} SHA-pinned entries\n")
            fh.write(f"- Stale: {len(bumps)} (applying {len(emitted)}, cap {args.max})\n")
            if skipped_non_github:
                fh.write(f"- Skipped non-GitHub: {skipped_non_github}\n")
            if dead:
                fh.write(f"- **Dead upstream** ({len(dead)}): {', '.join(dead)}\n")
            if emitted:
                fh.write("\n| Plugin | Old | New | Age |\n|---|---|---|---|\n")
                for b in emitted:
                    old = b["old_sha"][:8] if b["old_sha"] else "(unpinned)"
                    fh.write(f"| {b['name']} | `{old}` | `{b['new_sha'][:8]}` | {b['age_days']}d |\n")

    # Write PR body for the workflow to use
    pr_body_path = os.environ.get("PR_BODY_PATH", "/tmp/bump-pr-body.md")
    if emitted:
        with open(pr_body_path, "w") as fh:
            fh.write("Upstream repos moved. Bumping pinned SHAs so plugins track latest.\n\n")
            fh.write("| Plugin | Old | New | Upstream |\n")
            fh.write("|--------|-----|-----|----------|\n")
            for b in emitted:
                old = b["old_sha"][:8] if b["old_sha"] else "(unpinned)"
                slug_str = re.sub(r"https?://github\.com/", "", b["url"])
                slug_str = re.sub(r"\.git$", "", slug_str)
                compare = f"https://github.com/{slug_str}/compare/{b['old_sha'][:12]}...{b['new_sha'][:12]}"
                fh.write(f"| `{b['name']}` | `{old}` | `{b['new_sha'][:8]}` | [diff]({compare}) |\n")
            fh.write(f"\n---\n_Auto-generated by `bump-plugin-shas.yml` on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}_\n")

    # Console summary
    print(f"Checked {checked} SHA-pinned plugins", file=sys.stderr)
    print(f"Stale: {len(bumps)}, applying: {len(emitted)}", file=sys.stderr)
    if dead:
        print(f"Dead upstream: {', '.join(dead)}", file=sys.stderr)
    for b in emitted:
        old = b["old_sha"][:8] if b["old_sha"] else "unpinned"
        print(f"  {b['name']}: {old} -> {b['new_sha'][:8]} ({b['age_days']}d)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
