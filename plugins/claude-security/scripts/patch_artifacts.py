#!/usr/bin/env python3
"""Render the suggested-fix products from a patch run directory.

Reads the run's `patches.json` and raw `F<n>.diff` files, and writes into the
report's `patches/` directory:

  * `F<n>.patch` -- the raw diff behind an explanatory comment header;
  * `F<n>.md` -- a short note per finding, whether or not a patch was written;
  * `PATCHES.md` and `patches.jsonl` -- the index, prose and machine form;
  * the report directory's `.gitignore` (the single line `*`) if it lacks one.

Each written patch is checked read-only against the repository with
`git apply --check`, and the whole patch run directory -- scratch workspaces,
raw diffs and the record -- is removed once the products are written, along
with the run directory above it when nothing else remains there.

Usage:
  patch_artifacts.py <patch_dir> <patches_dir> <scan_root> --base <sha>
  patch_artifacts.py --remove-scratch <workspace>

Exits 0 on success (declined findings included), 1 on a refusal naming what is
wrong, 2 on a usage error. Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING, TypedDict, cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_report import HEX_RE, RenderError, as_map, atomic_write

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
    from typing import NoReturn

FINDING_ID_PATTERN = "F[0-9]{1,9}"
FINDING_ID_RE = re.compile(rf"^{FINDING_ID_PATTERN}\Z")
SURROGATE_RE = re.compile(r"[\ud800-\udfff]")
REGULAR_FILE_MODE = "100644"
# \Z, not $: `$` also matches before a trailing newline, and this is a fence.
REPORT_DIR_RE = re.compile(r"^CLAUDE-SECURITY-[0-9][0-9-]*\Z")
PATCHES_DIR_NAME = "patches"
SCRATCH_NAME_RE = re.compile(rf"^scratch-{FINDING_ID_PATTERN}\Z")
PATCH_DIR_RE = re.compile(r"^patch-[0-9][0-9-]*\Z")
RUN_DIR_NAME = ".claude-security-run"
DIFF_HEADER = "diff --git "
CLAIM_KEYS = ("targeted", "no_new_vulnerability", "behaviour_unchanged")
CLAIM_LABELS = {
    "targeted": "the change is highly targeted to this finding",
    "no_new_vulnerability": "the change introduces no new security vulnerability",
    "behaviour_unchanged": (
        "beyond closing the finding, the change does not alter the code's "
        "behaviour or the inputs it accepts"
    ),
}
CLAIM_STATES = ("CONFIDENT", "NOT_CONFIDENT", "UNSURE")
STATUSES = ("patch_written", "declined", "skipped_stale")
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")


class Claim(TypedDict):
    """One of the verifier's three confidence claims."""

    state: str
    evidence: str


class DiffStat(TypedDict):
    """Per-file added/deleted line counts."""

    path: str
    added: object
    deleted: object


class Unit(TypedDict):
    """A validated unit record, ready to be written out."""

    id: str
    title: str
    status: str
    summary: str
    claims: dict[str, Claim]
    untested: bool
    tests_run: str
    reviewed_paths: list[str]
    decline_reason: str
    recommendation: str


class PatchError(Exception):
    """The run record or a raw diff is malformed; the caller must correct it."""


def die(message: str) -> NoReturn:
    """A refusal: the inputs are well-formed arguments but bad data. Exits 1."""
    sys.stderr.write(f"patch_artifacts.py: {message}\n")
    sys.exit(1)


def die_usage(message: str) -> NoReturn:
    """A usage error: the arguments themselves are wrong. Exits 2."""
    sys.stderr.write(f"patch_artifacts.py: {message}\n")
    sys.exit(2)


def field(value: object, what: str) -> str:
    """A record field as text; None reads as empty."""
    if value is None:
        return ""
    if not isinstance(value, str):
        msg = f"{what} must be a string"
        raise PatchError(msg)
    lone = SURROGATE_RE.search(value)
    if lone:
        msg = f"{what} contains an unpaired surrogate ({lone.group(0)!r}); it is not valid text"
        raise PatchError(msg)
    return value


def line_field(value: object, what: str) -> str:
    """A record field for the patch's one-line "#" header; line breaks folded to spaces."""
    return field(value, what).replace("\r", " ").replace("\n", " ")


def field_list(value: object, what: str) -> list[str]:
    """A list-of-strings record field."""
    if value is None:
        return []
    if not isinstance(value, list):
        msg = f"{what} must be a list of strings"
        raise PatchError(msg)
    items = cast("list[object]", value)
    return [field(item, f"{what}[{index}]") for index, item in enumerate(items)]


def build_claims(raw: object, unit_id: str, status: str) -> dict[str, Claim]:
    """Validate the three named claims. A written patch needs all three CONFIDENT."""
    claims_map = as_map(raw) or {}
    out: dict[str, Claim] = {}
    for key in CLAIM_KEYS:
        claim = as_map(claims_map.get(key))
        if claim is None:
            if status == "patch_written":
                msg = f"{unit_id}: status is patch_written but claim {key!r} is missing"
                raise PatchError(msg)
            continue
        state = field(claim.get("state"), f"{unit_id} claim {key}.state").upper()
        if state not in CLAIM_STATES:
            msg = (
                f"{unit_id}: claim {key!r} has state {state!r}; want one of "
                f"{', '.join(CLAIM_STATES)}"
            )
            raise PatchError(msg)
        evidence = line_field(claim.get("evidence"), f"{unit_id} claim {key}.evidence")
        out[key] = Claim(state=state, evidence=evidence)
    if status == "patch_written":
        not_confident = [k for k in CLAIM_KEYS if out[k]["state"] != "CONFIDENT"]
        if not_confident:
            msg = (
                f"{unit_id}: status is patch_written but {', '.join(not_confident)} "
                "is not CONFIDENT -- a patch is written only when all three claims "
                "are; record the unit as declined instead."
            )
            raise PatchError(msg)
    return out


def build_unit(raw: object, index: int) -> Unit:
    """Validate one unit from patches.json into the shape the writers use."""
    item = as_map(raw)
    if item is None:
        msg = f"patches.json unit {index} is not an object"
        raise PatchError(msg)
    unit_id = field(item.get("id"), f"unit {index} id")
    if not FINDING_ID_RE.match(unit_id):
        msg = f"unit {index} id {unit_id!r} is not a finding id (want F<number>, at most 9 digits)"
        raise PatchError(msg)
    status = field(item.get("status"), f"{unit_id} status")
    if status not in STATUSES:
        msg = f"{unit_id}: status {status!r} is not one of {', '.join(STATUSES)}"
        raise PatchError(msg)
    claims = build_claims(item.get("claims"), unit_id, status)
    decline_reason = field(item.get("decline_reason"), f"{unit_id} decline_reason")
    if status != "patch_written" and not decline_reason:
        msg = f"{unit_id}: status {status} needs a decline_reason saying why no patch was written"
        raise PatchError(msg)
    untested = item.get("untested")
    if untested is None and status == "patch_written":
        msg = (
            f'{unit_id}: status is patch_written but "untested" is missing -- it must '
            "say (true/false) whether the project's own tests exercise the patched "
            "code, because the patch header tells the reader exactly that."
        )
        raise PatchError(msg)
    if untested is not None and not isinstance(untested, bool):
        msg = f'{unit_id}: "untested" must be true or false'
        raise PatchError(msg)
    return Unit(
        id=unit_id,
        title=line_field(item.get("title"), f"{unit_id} title") or unit_id,
        status=status,
        summary=line_field(item.get("summary"), f"{unit_id} summary"),
        claims=claims,
        untested=untested is True,
        tests_run=line_field(item.get("tests_run"), f"{unit_id} tests_run"),
        reviewed_paths=field_list(item.get("reviewed_paths"), f"{unit_id} reviewed_paths"),
        decline_reason=decline_reason,
        recommendation=field(item.get("recommendation"), f"{unit_id} recommendation"),
    )


def load_units(patch_dir: str) -> list[Unit]:
    """Read and validate patches.json (an object with a `units` array)."""
    path = os.path.join(patch_dir, "patches.json")
    try:
        with open(path, encoding="utf-8") as handle:
            raw = cast("object", json.load(handle))
    except OSError as error:
        msg = "patches.json is missing from the patch directory. Write it before running this."
        raise PatchError(msg) from error
    except ValueError as error:
        msg = f"patches.json is not valid JSON: {error}"
        raise PatchError(msg) from error
    record = as_map(raw)
    units_raw: object = record.get("units") if record is not None else raw
    if not isinstance(units_raw, list):
        msg = 'patches.json must be an object with a "units" array'
        raise PatchError(msg)
    units = [build_unit(item, i) for i, item in enumerate(cast("list[object]", units_raw))]
    seen: set[str] = set()
    for unit in units:
        if unit["id"] in seen:
            msg = f"{unit['id']} appears more than once in patches.json"
            raise PatchError(msg)
        seen.add(unit["id"])
    return units


def read_diff(patch_dir: str, unit_id: str, required: bool) -> bytes | None:
    """The raw diff git wrote for this unit; None only if absent and optional.

    A required one (a written patch) must exist and hold at least one
    `diff --git` section, since the patch and its diffstat are built from it.
    """
    path = os.path.join(patch_dir, f"{unit_id}.diff")
    if not os.path.isfile(path):
        if required:
            msg = (
                f"{unit_id}: status is patch_written but {unit_id}.diff is missing from the "
                "patch directory. Write the staged diff with git diff --output before "
                "running this script."
            )
            raise PatchError(msg)
        return None
    data = pathlib.Path(path).read_bytes()
    if required and DIFF_HEADER.encode("ascii") not in data:
        msg = f"{unit_id}.diff contains no '{DIFF_HEADER.strip()}' header; it is not a git diff"
        raise PatchError(msg)
    return data


def atomic_write_bytes(path: str, data: bytes) -> None:
    """Byte-faithful counterpart of render_report.atomic_write."""
    handle, temp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".render.")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp)
        raise


def display_name(name: str | None) -> str | None:
    """A `--- `/`+++ ` line's file name for display: a/ or b/ dropped, None for /dev/null."""
    if name is None:
        return None
    name = name.rstrip("\r")
    if not name.startswith('"'):
        name = name.split("\t", 1)[0]
    if name == "/dev/null":
        return None
    if name.startswith(('"a/', '"b/')):
        return '"' + name[3:]
    return name[2:] if name[:2] in {"a/", "b/"} else name


def section_stat(lines: list[str]) -> DiffStat:
    """One `diff --git` section's file name and added/deleted line counts."""
    names: dict[str, str] = {}
    modes: dict[str, str] = {}
    added = deleted = 0
    binary = False
    in_hunk = False
    for line in lines[1:]:
        if in_hunk:
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                deleted += 1
        elif line.startswith(("GIT binary patch", "Binary files ")):
            binary = True
        elif line.startswith("@@ "):
            in_hunk = True
        else:
            for key in ("--- ", "+++ "):
                if line.startswith(key):
                    names[key.strip()] = line[4:]
            for key in ("old mode", "new mode", "new file mode", "rename from", "rename to"):
                if line.startswith(key + " "):
                    modes[key] = line[len(key) + 1 :].strip()
    if modes.get("rename from") and modes.get("rename to"):
        path = f"{modes['rename from']} => {modes['rename to']}"
    else:
        header = lines[0][len(DIFF_HEADER) :].rstrip("\r")
        cut = header.rfind(" b/")
        fallback = header[cut + 3 :] if cut >= 0 else header
        path = display_name(names.get("+++")) or display_name(names.get("---")) or fallback
    old_mode, new_mode = modes.get("old mode"), modes.get("new mode")
    if old_mode and new_mode and old_mode != new_mode:
        path += f" (mode {old_mode} -> {new_mode})"
    elif modes.get("new file mode") not in {None, REGULAR_FILE_MODE}:
        path += f" (new file, mode {modes['new file mode']})"
    return DiffStat(path=path, added="-" if binary else added, deleted="-" if binary else deleted)


def numstat(diff: bytes) -> list[DiffStat]:
    """Per-file added/deleted line counts, parsed from the diff itself."""
    stats: list[DiffStat] = []
    section: list[str] = []
    for line in diff.decode("utf-8", "replace").splitlines():
        if line.startswith(DIFF_HEADER):
            if section:
                stats.append(section_stat(section))
            section = [line]
        elif section:
            section.append(line)
    if section:
        stats.append(section_stat(section))
    return stats


def git_toplevel(scan_root: str) -> str | None:
    """The repository root containing scan_root, or None when git can't say."""
    try:
        out = subprocess.run(
            ["git", "-C", scan_root, "rev-parse", "--show-toplevel"],
            env=GIT_ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    top = out.stdout.decode("utf-8", "replace").rstrip("\r\n")
    return top or None


def apply_check(top: str | None, patch_path: str) -> str:
    """`git apply --check` against the user's tree: 'clean', 'conflicts: ...', or 'not_run'."""
    if top is None:
        return "not_run"
    try:
        out = subprocess.run(
            ["git", "-C", top, "apply", "--check", os.path.abspath(patch_path)],
            env=GIT_ENV,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "not_run"
    if out.returncode == 0:
        return "clean"
    first = out.stderr.decode("utf-8", "replace").strip().splitlines()
    return "conflicts" + (f": {first[0]}" if first else "")


def diffstat_lines(stats: list[DiffStat] | None) -> list[str]:
    """Diffstat as markdown bullets, or a one-line fallback when git was unavailable."""
    if stats is None:
        return ["- _(no attempt diff was saved)_"]
    if not stats:
        return ["- _(no file changes recorded)_"]
    return [f"- `{s['path']}` (+{s['added']} -{s['deleted']})" for s in stats]


def header_comment(unit: Unit, base: str, report_ref: str) -> str:
    """The comment block prepended above the first `diff --git`; git apply ignores it."""
    lines = [
        f"# Claude Security -- suggested patch for {unit['id']}: {unit['title']}",
        f"# Applies to revision {base[:12]} (the revision the scan report describes).",
        "#",
        "# Verified by a panel of agents: an independent verifier reviewed this",
        "# change against the finding, and a second, fresh reviewer re-challenged",
        "# the bare diff for new vulnerabilities. The patch was written only",
        "# because the panel stated all three of these with confidence:",
    ]
    for key in CLAIM_KEYS:
        claim = unit["claims"][key]
        lines.append(f"#   - {CLAIM_LABELS[key]}: {claim['evidence'] or claim['state']}")
    if unit["untested"]:
        lines += [
            "#",
            "# NOTE: no test exercises the patched code. The claim that behaviour is",
            "# unchanged rests on review of the change and its callers, not on a test",
            "# run -- weigh it accordingly before applying.",
        ]
    if unit["summary"]:
        lines += ["#", f"# {unit['summary']}"]
    if unit["tests_run"]:
        lines += [f"# Tests run: {unit['tests_run']}"]
    lines += [
        "#",
        (f"# Apply, from the repository root:  git apply {report_ref}/patches/{unit['id']}.patch"),
        "#",
        "",
    ]
    return "\n".join(lines)


def note_written(unit: Unit, stats: list[DiffStat] | None, check: str, report_ref: str) -> str:
    """The F<n>.md note for a finding that earned a patch."""
    lines = [
        f"# {unit['id']}: {unit['title']}",
        "",
        f"**Status:** patch written -> `{unit['id']}.patch`",
        "",
        (
            "**Verified by a panel of agents.** An independent verifier reviewed the "
            "change against the finding and stated the three claims below with "
            "confidence, and a second, fresh reviewer re-challenged the bare diff "
            "for new vulnerabilities. The patch was written only because the "
            "panel could vouch for it; nothing here was applied for you."
        ),
        "",
    ]
    if unit["summary"]:
        lines += [unit["summary"], ""]
    lines += ["## Confidence", ""]
    for key in CLAIM_KEYS:
        claim = unit["claims"][key]
        lines.append(f"- **{CLAIM_LABELS[key]}** -- {claim['state']}: {claim['evidence']}")
    if unit["untested"]:
        lines += [
            "",
            (
                "**No test exercises the patched code.** The behaviour claim rests on "
                "review of the change and its callers, not on a test run."
            ),
        ]
    lines += ["", f"**Tests run:** {unit['tests_run'] or 'none recorded'}", ""]
    lines += ["## Change", ""]
    lines += diffstat_lines(stats)
    lines += ["", "## Applying it", ""]
    if check == "clean":
        lines.append("Applies cleanly to the working tree (checked with `git apply --check`).")
    elif check == "not_run":
        lines.append("The clean-apply check could not run here (git unavailable); try it yourself.")
    else:
        detail = check.split(": ", 1)[-1]
        lines.append(
            f"`git apply --check` reported a conflict ({detail}). The patch was built against the "
            "recorded revision, so this usually means the working tree has uncommitted or newer "
            "changes in these files -- apply it to a checkout of that revision, or merge by "
            "hand."
        )
    lines += [
        "",
        "```",
        f"git apply {report_ref}/patches/{unit['id']}.patch",
        "```",
        "",
        "Or ask Claude Security to apply it, or to open a pull request for it.",
        "",
    ]
    return "\n".join(lines)


def note_declined(unit: Unit, stats: list[DiffStat] | None) -> str:
    """The F<n>.md note for a finding with no patch."""
    lines = [
        f"# {unit['id']}: {unit['title']}",
        "",
        "**Status:** no patch produced",
        "",
        unit["decline_reason"],
        "",
    ]
    blocking = [(k, c) for k, c in unit["claims"].items() if c["state"] != "CONFIDENT"]
    if blocking:
        lines += ["## The claim that could not be made with confidence", ""]
        for key, claim in blocking:
            lines.append(f"- **{CLAIM_LABELS[key]}** -- {claim['state']}: {claim['evidence']}")
        lines.append("")
    if stats is not None:
        lines += ["## What the rejected attempt changed", ""]
        lines += diffstat_lines(stats)
        lines.append("")
    if unit["recommendation"]:
        lines += ["## The report's original recommendation", "", unit["recommendation"], ""]
    return "\n".join(lines)


def index_markdown(units: list[Unit], base: str, report_dir_name: str, report_ref: str) -> str:
    """PATCHES.md: the one-page index of every unit's outcome."""
    patched = [u for u in units if u["status"] == "patch_written"]
    declined = [u for u in units if u["status"] != "patch_written"]
    lines = [
        "# Suggested patches",
        "",
        (
            f"Targeted patches for findings in `{report_dir_name}`, each written against "
            f"revision `{base[:12]}` and verified by a panel of agents before it was "
            "written. Nothing here is applied, committed, or opened as a pull request "
            "until you choose to do so."
        ),
        "",
    ]
    if patched:
        lines += ["## Patches written", ""]
        for unit in patched:
            caveat = " _(no tests cover the patched code)_" if unit["untested"] else ""
            lines.append(f"- **{unit['id']}** -- {unit['title']}: `{unit['id']}.patch`{caveat}")
        lines.append("")
    if declined:
        lines += ["## No patch produced", ""]
        for unit in declined:
            lines.append(f"- **{unit['id']}** -- {unit['title']}: {unit['decline_reason']}")
        lines.append("")
    lines += [
        "## Applying a patch",
        "",
        "From the repository root:",
        "",
        "```",
        f"git apply {report_ref}/patches/F<n>.patch",
        "```",
        "",
        (
            "Each `F<n>.md` beside the patch explains the change and what was verified. "
            "The job that wrote these applied, committed, pushed, and opened nothing; "
            "if you want one applied, or turned into a pull request, ask Claude "
            "Security and it handles that as a separate request."
        ),
        "",
    ]
    return "\n".join(lines)


def jsonl(
    units: list[Unit],
    base: str,
    stats_by_id: dict[str, list[DiffStat] | None],
    checks: dict[str, str],
) -> str:
    """patches.jsonl: one record per unit, machine-readable for tooling."""
    rows: list[str] = []
    for unit in units:
        record: dict[str, object] = {
            "id": unit["id"],
            "status": unit["status"],
            "base": base,
            "patch": f"{unit['id']}.patch" if unit["status"] == "patch_written" else None,
            "note": f"{unit['id']}.md",
            "claims": unit["claims"],
            "untested": unit["untested"],
            "tests_run": unit["tests_run"] or None,
            "reviewed_paths": unit["reviewed_paths"],
            "diffstat": stats_by_id.get(unit["id"]),
            "apply_check": checks.get(unit["id"]),
            "decline_reason": unit["decline_reason"] or None,
        }
        rows.append(json.dumps(record, ensure_ascii=False, sort_keys=False))
    return "\n".join(rows) + ("\n" if rows else "")


def clear_stale_products(patches_dir: str, produced: set[str]) -> list[str]:
    """Remove F<n>.patch / F<n>.md files an earlier run left that this run did not write.

    Only the script's own product names (F<n>.patch, F<n>.md) are removed;
    every other file in the folder is left alone.
    """
    removed: list[str] = []
    for name in sorted(os.listdir(patches_dir)):
        stem, dot, ext = name.rpartition(".")
        if not dot or ext not in {"patch", "md"} or not FINDING_ID_RE.match(stem):
            continue
        if name in produced:
            continue
        path = os.path.join(patches_dir, name)
        if os.path.isdir(path):
            continue
        os.unlink(path)
        removed.append(name)
    return removed


def ensure_gitignore(report_dir: str) -> str:
    """Fence the report directory with a `*` .gitignore if it has none.

    Returns "written" when the fence was just added, "present" when an
    existing .gitignore already ignores everything, and "open" when one exists
    but has no bare `*` line; an existing file is never rewritten.
    """
    path = os.path.join(report_dir, ".gitignore")
    if os.path.lexists(path):
        try:
            existing = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "open"
        return "present" if "*" in (line.strip() for line in existing.splitlines()) else "open"
    atomic_write(path, "*\n")
    return "written"


def contained_relpath(target: str, root: str) -> str | None:
    """`target` as a path from `root`, or None when it does not sit inside root."""
    rel = os.path.relpath(os.path.realpath(target), os.path.realpath(root))
    if rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel):
        return None
    return rel


def report_path_from_root(report_dir: str, top: str | None, fallback: str) -> str:
    """The report directory as a path from the repository root, for the apply command.

    Falls back to the bare folder name when git cannot name a root or the
    folder sits outside it.
    """
    if top is None:
        return fallback
    return contained_relpath(report_dir, top) or fallback


def resolve_report_dir(patches_dir: str) -> tuple[str, str]:
    """The report directory holding `patches_dir`, validated by name."""
    patches_abs = os.path.abspath(patches_dir)
    report_dir = os.path.dirname(patches_abs)
    report_dir_name = os.path.basename(report_dir)
    if os.path.basename(patches_abs) != PATCHES_DIR_NAME:
        msg = (
            f"patches dir must be a directory named {PATCHES_DIR_NAME!r} inside the "
            f"report directory; got {patches_abs}"
        )
        raise PatchError(msg)
    if not REPORT_DIR_RE.match(report_dir_name):
        msg = (
            "patches dir must live inside a CLAUDE-SECURITY-<timestamp> report "
            f"directory; its parent is {report_dir_name!r}. Refusing rather than "
            "fence the wrong directory with a .gitignore."
        )
        raise PatchError(msg)
    return report_dir, report_dir_name


def run(patch_dir: str, patches_dir: str, scan_root: str, base: str) -> int:
    units = load_units(patch_dir)
    report_dir, report_dir_name = resolve_report_dir(patches_dir)
    top = git_toplevel(scan_root)
    report_ref = shlex.quote(report_path_from_root(report_dir, top, report_dir_name))
    stats_by_id: dict[str, list[DiffStat] | None] = {}
    checks: dict[str, str] = {}
    produced: set[str] = set()
    for unit in units:
        written = unit["status"] == "patch_written"
        diff = read_diff(patch_dir, unit["id"], required=written)
        stats = numstat(diff) if diff is not None else None
        stats_by_id[unit["id"]] = stats
        if written and diff is not None:
            patch_path = os.path.join(patches_dir, f"{unit['id']}.patch")
            header = header_comment(unit, base, report_ref)
            atomic_write_bytes(patch_path, header.encode("utf-8") + diff)
            check = apply_check(top, patch_path)
            checks[unit["id"]] = check
            note = note_written(unit, stats, check, report_ref)
            produced.add(f"{unit['id']}.patch")
            print(f"{unit['id']}: patch written -> {patch_path} (apply check: {check})")
        else:
            note = note_declined(unit, stats)
            print(f"{unit['id']}: no patch ({unit['status']}) -> {unit['id']}.md")
        atomic_write(os.path.join(patches_dir, f"{unit['id']}.md"), note)
        produced.add(f"{unit['id']}.md")
    index_text = index_markdown(units, base, report_dir_name, report_ref)
    atomic_write(os.path.join(patches_dir, "PATCHES.md"), index_text)
    atomic_write(
        os.path.join(patches_dir, "patches.jsonl"), jsonl(units, base, stats_by_id, checks)
    )
    for name in clear_stale_products(patches_dir, produced):
        print(f"removed stale {name} (not produced by this run)")
    swept, warnings = remove_workspaces_in(patch_dir)
    for name in swept:
        print(f"removed workspace {name}")
    removed, more_warnings = remove_patch_run(patch_dir)
    for path in removed:
        print(f"removed {path}")
    for warning in warnings + more_warnings:
        print(f"WARNING: {warning}")
    fence = ensure_gitignore(report_dir)
    if fence == "written":
        print(f"fenced {report_dir} with .gitignore")
    elif fence == "open":
        print(
            f"WARNING: {report_dir}/.gitignore exists but does not ignore everything "
            "('*'); the report and these patches are NOT fenced off from git add. "
            "Left untouched -- edit it yourself if you want them ignored."
        )
    patched = sum(1 for u in units if u["status"] == "patch_written")
    print(
        f"wrote PATCHES.md and patches.jsonl into {patches_dir} "
        f"({patched} patched, {len(units) - patched} declined)"
    )
    return 0


def refuse_reason(path: str) -> str | None:
    """Why `path` may NOT be deleted as a scratch workspace, or None when it may.

    Only `<report>/.claude-security-run/patch-<ts>/scratch-F<n>` holding its
    own `.git` may be deleted; every other shape is refused.
    """
    leaf = os.path.normpath(os.path.abspath(path))
    if not os.path.isdir(leaf):
        return "it is not a directory"
    if not SCRATCH_NAME_RE.match(os.path.basename(leaf)):
        return "its name is not scratch-F<n>"
    run = os.path.dirname(leaf)
    top = os.path.dirname(run)
    if not PATCH_DIR_RE.match(os.path.basename(run)):
        return "it is not inside a patch-<timestamp> run directory"
    if os.path.basename(top) != RUN_DIR_NAME:
        return f"its run directory is not inside {RUN_DIR_NAME}/"
    if not os.path.isdir(os.path.join(leaf, ".git")):
        return "it holds no .git directory of its own"
    return None


def clear_readonly(
    func: Callable[..., object],
    path: str,
    exc_info: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    """Make `path` writable and retry the removal rmtree could not do."""
    # Git writes read-only objects, which Windows will not delete.
    if func not in {os.unlink, os.rmdir}:
        raise exc_info[1]
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_workspace(path: str) -> None:
    """Delete one scratch workspace, refusing anything off the fenced layout."""
    reason = refuse_reason(path)
    if reason is not None:
        msg = f"refusing to remove {path!r}: {reason}"
        raise PatchError(msg)
    target = os.path.normpath(os.path.abspath(path))
    try:
        shutil.rmtree(target, onerror=clear_readonly)
    except OSError as error:
        detail = error.args[0] if error.args else error
        msg = f"could not remove {path!r}: {detail}"
        raise PatchError(msg) from error


def remove_workspaces_in(patch_dir: str) -> tuple[list[str], list[str]]:
    """Remove every scratch workspace in a patch run directory.

    Returns (removed names, warnings). Never raises: a workspace that cannot
    be removed is reported as a warning.
    """
    removed: list[str] = []
    warnings: list[str] = []
    try:
        names = sorted(os.listdir(patch_dir))
    except OSError as error:
        return removed, [f"could not list {patch_dir!r}: {error}"]
    for name in names:
        if not name.startswith("scratch-"):
            continue
        path = os.path.join(patch_dir, name)
        try:
            remove_workspace(path)
        except PatchError as error:
            warnings.append(str(error))
        else:
            removed.append(name)
    return removed, warnings


def remove_patch_run(patch_dir: str) -> tuple[list[str], list[str]]:
    """Remove a finished patch run directory, and its run directory if now empty.

    Returns (removed paths, warnings). Never raises; only the recipe's own
    `<report>/.claude-security-run/patch-<ts>` layout is deleted.
    """
    removed: list[str] = []
    target = os.path.normpath(os.path.abspath(patch_dir))
    run_dir = os.path.dirname(target)
    if not PATCH_DIR_RE.match(os.path.basename(target)):
        return removed, [f"left {patch_dir!r} in place: its name is not patch-<timestamp>"]
    if os.path.basename(run_dir) != RUN_DIR_NAME:
        return removed, [f"left {patch_dir!r} in place: it is not inside {RUN_DIR_NAME}/"]
    try:
        shutil.rmtree(target, onerror=clear_readonly)
    except OSError as error:
        detail = error.args[0] if error.args else error
        return removed, [f"could not remove {patch_dir!r}: {detail}"]
    removed.append(target)
    try:
        os.rmdir(run_dir)
    except OSError:
        return removed, []
    removed.append(run_dir)
    return removed, []


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--remove-scratch":
        if len(argv) != 2:
            die_usage("--remove-scratch takes exactly one workspace path")
        try:
            remove_workspace(argv[1])
        except PatchError as error:
            die(str(error))
        print(f"removed workspace {argv[1]!r}")
        return 0
    parser = argparse.ArgumentParser(
        prog="patch_artifacts.py",
        description="Render suggested-fix patch files and notes from a patch run directory.",
        epilog="Also: --remove-scratch <workspace> deletes one fenced scratch workspace.",
    )
    parser.add_argument("patch_dir", help="the patch run dir holding patches.json and F<n>.diff")
    parser.add_argument("patches_dir", help="the report's patches/ directory to write into")
    parser.add_argument("scan_root", help="the user's repository root (for git apply --check)")
    parser.add_argument("--base", required=True, help="the revision every patch applies to")
    args = parser.parse_args(argv)
    patch_dir = str(cast("object", args.patch_dir))
    patches_dir = str(cast("object", args.patches_dir))
    scan_root = str(cast("object", args.scan_root))
    base = str(cast("object", args.base))
    for label, path in (("patch dir", patch_dir), ("patches dir", patches_dir)):
        if not os.path.isdir(path):
            die_usage(f"{label} is not a directory: {path}")
    if not HEX_RE.match(base):
        die_usage(f"--base {base!r} is not a hex revision id")
    try:
        return run(patch_dir, patches_dir, scan_root, base)
    except (PatchError, RenderError) as error:
        die(str(error))
    except OSError as error:
        die(f"could not read or write the report's files: {error}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
