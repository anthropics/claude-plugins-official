#!/usr/bin/env python3
"""Prepare a patch run, and render the suggested-fix products from it.

`--prepare` lays out a patch run for a report: it checks the repository root
and the base revision, makes the run's working directory and the report's
`patches/` directory, writes one `findings/F<n>.json` per selected finding
(the report's record, its `file` made repository-relative), and prints the two
directories and the selected ids.

The render form reads the run's `patches.json` and raw `F<n>.diff` files, and
writes into the report's `patches/` directory:

  * `F<n>.patch` -- the raw diff behind an explanatory comment header;
  * `F<n>.md` -- a short note per finding, whether or not a patch was written;
  * `PATCHES.md` and `patches.jsonl` -- the index, prose and machine form;
  * the report directory's `.gitignore` (the single line `*`) if it lacks one.

Each written patch is checked read-only against the repository with
`git apply --check`, and the whole patch run directory -- scratch workspaces,
prepared findings, raw diffs and the record -- is removed once the products are
written, along with the run directory above it when nothing else remains there.

Usage:
  patch_artifacts.py --prepare <report_dir> <selection> --repo-root <dir> --base <sha>
  patch_artifacts.py <patch_dir> <patches_dir> <scan_root> --base <sha>
  patch_artifacts.py --remove-scratch <workspace>

Exits 0 on success (declined findings included), 1 on a refusal naming what is
wrong, 2 on a usage error.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import functools
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from collections import Counter
from contextlib import suppress
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypedDict

# The lib/ package lives next to this script. Python normally adds a script's own
# directory to the import path, but not under -P or PYTHONSAFEPATH, so we add it here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import absolute, console, git, plugin, strictjson
from lib.finding import Severity, repository_file, scan_prefix_shaped
from lib.link import is_link
from lib.strictjson import JsonMap, is_int, is_list, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
    from typing import Literal

FINDING_ID_PATTERN = "F[0-9]{1,9}"
FINDING_ID_RE = re.compile(rf"^{FINDING_ID_PATTERN}\Z")


def finding_number(finding_id: str) -> int:
    """The number in a finding id, for sorting ids as a reader expects (F2 before F10)."""
    return int(finding_id[1:])


REGULAR_FILE_MODE = "100644"
PATCHES_DIR_NAME = "patches"
FINDINGS_DIR_NAME = "findings"
SCRATCH_NAME_RE = re.compile(rf"^scratch-{FINDING_ID_PATTERN}\Z")
PATCH_DIR_PREFIX = "patch-"
PATCH_DIR_RE = re.compile(rf"^{re.escape(PATCH_DIR_PREFIX)}[0-9][0-9-]*\Z")
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
NOT_CONFIRMED = (
    "The review found this finding is not exploitable as the report describes at this "
    "revision, so no patch was written for it."
)
UNTESTED_NOTICE = "no project test of the patched code was run"


class Claim(TypedDict):
    """One of the verifier's three confidence claims."""

    state: str
    evidence: str


class PathKind(str, Enum):
    """The kind the fresh reviewer gave an attack path it reported."""

    OPENED = "opened"
    STILL_REACHABLE = "still_reachable"
    SET_ASIDE = "set_aside"

    @property
    def blocks_patch(self) -> bool:
        return self is not PathKind.SET_ASIDE


PATH_KIND_LABELS = {
    PathKind.OPENED: "opened by the rejected change",
    PathKind.STILL_REACHABLE: "the finding's exploit, still reachable by another route",
    PathKind.SET_ASIDE: "set aside as outside this finding; not addressed here",
}


class AttackPath(TypedDict):
    """An attack path the fresh reviewer reported, with the kind it gave it."""

    kind: PathKind
    text: str


class DiffStat(TypedDict):
    """Per-file added/deleted line counts, "-" for a binary file as git prints it."""

    path: str
    added: int | Literal["-"]
    deleted: int | Literal["-"]


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
    attack_paths: list[AttackPath]
    attempts: int | None
    confirmed: bool | None
    decline_reason: str
    recommendation: str


class RenderArgs(argparse.Namespace):
    """The parsed render command line."""

    patch_dir: str = ""
    patches_dir: str = ""
    scan_root: str = ""
    base: str = ""


class PrepareArgs(argparse.Namespace):
    """The parsed `--prepare` command line."""

    report_dir: str = ""
    selection: str = ""
    repo_root: str = ""
    base: str = ""


class RemoveArgs(argparse.Namespace):
    """The parsed `--remove-scratch` command line."""

    workspace: str = ""


class ReportFinding(NamedTuple):
    """A report finding as `--prepare` reads it: its severity, and its record to hand on."""

    severity: Severity
    record: JsonMap


class PatchError(Exception):
    """A refusal; the message names what the caller must correct."""


def field(value: object, what: str) -> str:
    """A record field as text; None reads as empty."""
    if value is None:
        return ""
    if not is_str(value):
        msg = f"{what} must be a string"
        raise PatchError(msg)
    if strictjson.has_lone_surrogate(value):
        msg = f"{what} contains an unpaired surrogate; it is not valid text"
        raise PatchError(msg)
    return value


def line_field(value: object, what: str) -> str:
    """A one-line record field; line breaks folded to spaces."""
    return field(value, what).replace("\r", " ").replace("\n", " ")


def field_list(value: object, what: str) -> list[str]:
    """A list-of-strings record field."""
    if value is None:
        return []
    if not is_list(value):
        msg = f"{what} must be a list of strings"
        raise PatchError(msg)
    return [field(item, f"{what}[{index}]") for index, item in enumerate(value)]


def build_claims(raw: object, unit_id: str, status: str) -> dict[str, Claim]:
    """Validate the three named claims. A written patch needs all three CONFIDENT."""
    claims_map: JsonMap = {}
    if raw is not None:
        if not is_map(raw):
            msg = f"{unit_id}: claims must be an object keyed by claim name"
            raise PatchError(msg)
        claims_map = raw
    out: dict[str, Claim] = {}
    for key in CLAIM_KEYS:
        claim = claims_map.get(key)
        if not is_map(claim):
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


def build_attack_path(item: object, what: str) -> AttackPath:
    """One of the fresh reviewer's attack paths: a known kind and a non-empty text."""
    if not is_map(item):
        msg = f"{what} is not an object with a kind and a text"
        raise PatchError(msg)
    try:
        kind = PathKind(field(item.get("kind"), f"{what}.kind"))
    except ValueError as error:
        kinds = ", ".join(k.value for k in PathKind)
        msg = f"{what} kind {item.get('kind')!r} is not one of {kinds}"
        raise PatchError(msg) from error
    text = line_field(item.get("text"), f"{what}.text").strip()
    if not text:
        msg = f"{what} has no text saying what the path is"
        raise PatchError(msg)
    return AttackPath(kind=kind, text=text)


def build_attack_paths(raw: object, unit_id: str, status: str) -> list[AttackPath]:
    """Validate the fresh reviewer's attack paths; a written patch lists them, none blocking it."""
    written = status == "patch_written"
    if raw is None:
        if written:
            msg = (
                f'{unit_id}: status is patch_written but "attack_paths" is missing -- it must '
                "list what the fresh reviewer reported, or be empty when it reported none."
            )
            raise PatchError(msg)
        return []
    if not is_list(raw):
        msg = f"{unit_id}: attack_paths must be a list"
        raise PatchError(msg)
    paths = [build_attack_path(item, f"{unit_id} attack_paths[{i}]") for i, item in enumerate(raw)]
    blocking = next((path for path in paths if path["kind"].blocks_patch), None)
    if written and blocking is not None:
        msg = (
            f"{unit_id}: status is patch_written but the fresh reviewer reported a path it did not "
            f"set aside ({blocking['kind'].value}: {blocking['text']}) -- that blocks the "
            "patch: record the unit as declined, or, if a later round's reviewer reported no "
            "path that counts, leave this earlier round's path out of the record."
        )
        raise PatchError(msg)
    return paths


def build_attempts(raw: object, unit_id: str, status: str) -> int | None:
    """The number of fix attempts made; None for a stale unit, whatever its record says."""
    if status == "skipped_stale":
        return None
    if raw is None:
        msg = (
            f'{unit_id}: "attempts" is missing -- it must say how many fix attempts were made '
            "(1, or 2 for a unit that went through the revision round; 0 only when its workspace "
            "could not be opened)."
        )
        raise PatchError(msg)
    if not is_int(raw) or raw < 0:
        msg = f'{unit_id}: "attempts" must be a whole number of fix attempts made'
        raise PatchError(msg)
    if status == "patch_written" and raw == 0:
        msg = f"{unit_id}: a written patch took at least one attempt; attempts cannot be 0"
        raise PatchError(msg)
    return raw


def build_confirmed(raw: object, unit_id: str, status: str) -> bool | None:
    """The verifier's word on whether the finding is real; None if unstated or for a stale unit."""
    if raw is None or status == "skipped_stale":
        return None
    if not isinstance(raw, bool):
        msg = f'{unit_id}: "confirmed" must be true or false'
        raise PatchError(msg)
    if not raw and status != "declined":
        msg = f'{unit_id}: "confirmed" is false, so the unit must be declined: no patch for it'
        raise PatchError(msg)
    return raw


def build_unit(item: object, index: int) -> Unit:
    """Validate one unit from patches.json into the shape the writers use."""
    if not is_map(item):
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
    attack_paths = build_attack_paths(item.get("attack_paths"), unit_id, status)
    confirmed = build_confirmed(item.get("confirmed"), unit_id, status)
    reachable = next((p for p in attack_paths if p["kind"] is PathKind.STILL_REACHABLE), None)
    if confirmed is False and reachable is not None:
        msg = (
            f'{unit_id}: "confirmed": false cannot sit beside a still_reachable path '
            f"({reachable['text']}) -- if that path reaches the function or line the finding "
            'names, the panel disagreed: drop "confirmed" and decline on that path; if it '
            "reaches only other code, the refutation stands: record that path's kind as set_aside"
        )
        raise PatchError(msg)
    untested = item.get("untested")
    if untested is None and status == "patch_written":
        msg = (
            f'{unit_id}: status is patch_written but "untested" is missing -- it must '
            "say (true/false) whether the project's own tests exercise the patched "
            "code, because the patch header warns the reader when they do not."
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
        attack_paths=attack_paths,
        attempts=build_attempts(item.get("attempts"), unit_id, status),
        confirmed=confirmed,
        decline_reason=decline_reason,
        recommendation=field(item.get("recommendation"), f"{unit_id} recommendation"),
    )


def load_units(patch_dir: Path) -> list[Unit]:
    """Read and validate patches.json (an object with a `units` array) against the prepared units.

    Every unit id must have the `findings/<id>.json` that `--prepare` laid out.
    """
    try:
        raw = strictjson.load(patch_dir / "patches.json")
    except FileNotFoundError as error:
        msg = "patches.json is missing from the patch directory. Write it before running this."
        raise PatchError(msg) from error
    except ValueError as error:
        msg = f"patches.json is not valid JSON: {error}"
        raise PatchError(msg) from error
    units_raw = raw.get("units") if is_map(raw) else raw
    if not is_list(units_raw):
        msg = 'patches.json must be an object with a "units" array'
        raise PatchError(msg)
    units = [build_unit(item, i) for i, item in enumerate(units_raw)]
    counted = Counter(unit["id"] for unit in units)
    repeated = sorted(
        (unit_id for unit_id, count in counted.items() if count > 1), key=finding_number
    )
    if repeated:
        msg = f"patches.json uses these unit ids more than once: {', '.join(repeated)}"
        raise PatchError(msg)
    findings_dir = patch_dir / FINDINGS_DIR_NAME
    if not os.path.isdir(findings_dir):
        msg = f"the patch dir has no {FINDINGS_DIR_NAME}/ folder; run --prepare first"
        raise PatchError(msg)
    prepared = {path.stem for path in findings_dir.glob("*.json") if FINDING_ID_RE.match(path.stem)}
    unprepared = [unit["id"] for unit in units if unit["id"] not in prepared]
    if unprepared:
        msg = (
            f"patches.json names {', '.join(unprepared)}, which --prepare did not lay out; "
            f"this run's units are {', '.join(sorted(prepared, key=finding_number)) or 'none'} "
            "(the ids --prepare printed)"
        )
        raise PatchError(msg)
    return units


def read_diff(patch_dir: Path, unit_id: str, required: bool) -> bytes | None:
    """The raw diff git wrote for this unit; None only if absent and optional.

    A required one (a written patch) must exist and hold at least one
    `diff --git` section, since the patch and its diffstat are built from it.
    """
    path = patch_dir / f"{unit_id}.diff"
    if not os.path.isfile(path):
        if required:
            msg = (
                f"{unit_id}: status is patch_written but {unit_id}.diff is missing from the "
                "patch directory. Write the staged diff with git diff --output before "
                "running this script."
            )
            raise PatchError(msg)
        return None
    data = path.read_bytes()
    if required and DIFF_HEADER.encode("ascii") not in data:
        msg = f"{unit_id}.diff contains no '{DIFF_HEADER.strip()}' header; it is not a git diff"
        raise PatchError(msg)
    return data


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
    return git.run(scan_root, "rev-parse", "--show-toplevel") or None


def apply_check(top: str | None, patch_path: Path) -> str:
    """`git apply --check` against the user's tree: 'clean', 'conflicts: ...', or 'not_run'."""
    if top is None:
        return "not_run"
    try:
        out = subprocess.run(
            ["git", "-C", top, "apply", "--check", os.path.abspath(patch_path)],
            env=git.ENV,
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


def line_counts(entry: DiffStat) -> str:
    """A file's size in the diffstat: "(+a -d)", or "(binary)" where git counts no lines."""
    if entry["added"] == "-":
        return "(binary)"
    return f"(+{entry['added']} -{entry['deleted']})"


def diffstat_lines(stats: list[DiffStat] | None) -> list[str]:
    """Diffstat as markdown bullets, or a one-line note when there is no diff to size."""
    if stats is None:
        return ["- _(no attempt diff was saved)_"]
    if not stats:
        return ["- _(no file changes recorded)_"]
    return [f"- `{s['path']}` {line_counts(s)}" for s in stats]


def attack_path_lines(paths: list[AttackPath]) -> list[str]:
    """The fresh reviewer's attack paths as a note section; no lines when it reported none."""
    if not paths:
        return []
    bullets = [f"- **{PATH_KIND_LABELS[path['kind']]}** -- {path['text']}" for path in paths]
    return ["## What the fresh reviewer reported", "", *bullets, ""]


def header_comment(unit: Unit, base: str, report_ref: str) -> str:
    """The comment block prepended above the first `diff --git`; git apply ignores it."""
    short = base[: plugin.SHORT_ID_CHARS]
    lines = [
        f"# Claude Security -- suggested patch for {unit['id']}: {unit['title']}",
        f"# Applies to revision {short} (the revision these patches were built against).",
        "#",
        "# Verified by a panel of agents: an independent verifier reviewed this",
        "# change against the finding, and a second, fresh reviewer challenged the",
        "# diff for an attack path it opens, or a route it leaves open to the",
        "# finding's exploit. The patch was written only because the panel stated",
        "# all three of these with confidence:",
    ]
    for key in CLAIM_KEYS:
        claim = unit["claims"][key]
        lines.append(f"#   - {CLAIM_LABELS[key]}: {claim['evidence'] or claim['state']}")
    if unit["untested"]:
        lines += [
            "#",
            f"# NOTE: {UNTESTED_NOTICE}. The claim that",
            "# behaviour is unchanged rests on review of the change and its callers,",
            "# not on a test run -- weigh it accordingly before applying.",
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
            "confidence, and a second, fresh reviewer challenged the diff for an "
            "attack path it opens, or a route it leaves open to the finding's exploit. "
            "The patch was written only because the panel could vouch for it; nothing "
            "here was applied for you."
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
                f"**{UNTESTED_NOTICE[:1].upper()}{UNTESTED_NOTICE[1:]}.** The behaviour claim "
                "rests on review of the change and its callers, not on a test run."
            ),
        ]
    lines += ["", f"**Tests run:** {unit['tests_run'] or 'none recorded'}", ""]
    lines += ["## Change", ""]
    lines += diffstat_lines(stats)
    lines += ["", *attack_path_lines(unit["attack_paths"]), "## Applying it", ""]
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


def decline_wording(unit: Unit) -> tuple[str, str] | None:
    """A declined unit's outcome as (note sentence, index parenthesis); None for a stale unit."""
    count = unit["attempts"]
    if count is None:
        return None
    if unit["confirmed"] is False:
        return NOT_CONFIRMED, "finding not confirmed at this revision"
    if count == 0:
        sentence = "No fix for this finding could be attempted, so no patch was written."
        return sentence, "no attempt possible"
    made = "1 attempt" if count == 1 else f"{count} attempts"
    sentence = (
        f"After {made}, no fix for this finding was produced that passed the panel's review, "
        "so no patch was written."
    )
    return sentence, f"no fix passed review in {made}"


def note_declined(unit: Unit, stats: list[DiffStat] | None) -> str:
    """The F<n>.md note for a finding with no patch."""
    lines = [
        f"# {unit['id']}: {unit['title']}",
        "",
        "**Status:** no patch produced",
        "",
        *([wording[0], ""] if (wording := decline_wording(unit)) else []),
        unit["decline_reason"],
        "",
    ]
    blocking = [(k, c) for k, c in unit["claims"].items() if c["state"] != "CONFIDENT"]
    if blocking:
        lines += ["## What could not be claimed with confidence", ""]
        for key, claim in blocking:
            lines.append(f"- **{CLAIM_LABELS[key]}** -- {claim['state']}: {claim['evidence']}")
        lines.append("")
    lines += attack_path_lines(unit["attack_paths"])
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
    short = base[: plugin.SHORT_ID_CHARS]
    lines = [
        "# Suggested patches",
        "",
        (
            f"Targeted patches for findings in `{report_dir_name}`, each written against "
            f"revision `{short}` and verified by a panel of agents before it was "
            "written. Nothing here is applied, committed, or opened as a pull request "
            "until you choose to do so."
        ),
        "",
    ]
    if patched:
        lines += ["## Patches written", ""]
        for unit in patched:
            caveat = f" _({UNTESTED_NOTICE})_" if unit["untested"] else ""
            lines.append(f"- **{unit['id']}** -- {unit['title']}: `{unit['id']}.patch`{caveat}")
        lines.append("")
    if declined:
        lines += ["## No patch produced", ""]
        for unit in declined:
            wording = decline_wording(unit)
            suffix = f" ({wording[1]})" if wording else ""
            lines.append(f"- **{unit['id']}** -- {unit['title']}{suffix}: {unit['decline_reason']}")
        lines.append("")
    aside = [
        (unit["id"], path)
        for unit in units
        for path in unit["attack_paths"]
        if path["kind"] is PathKind.SET_ASIDE
    ]
    if aside:
        lines += ["## Set aside by the reviewers", ""]
        lines += [f"- while reviewing **{unit_id}** -- {path['text']}" for unit_id, path in aside]
        lines += [
            "",
            (
                "Each of these was seen while reviewing the finding named beside it and was "
                "set aside as outside that finding, so nothing written for that finding "
                "addresses it. Unless another finding here covers it, review it yourself, or "
                "ask Claude Security to scan or patch it."
            ),
            "",
        ]
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
    return "".join(
        strictjson.text({
            "id": unit["id"],
            "status": unit["status"],
            "base": base,
            "patch": f"{unit['id']}.patch" if unit["status"] == "patch_written" else None,
            "note": f"{unit['id']}.md",
            "claims": unit["claims"],
            "untested": unit["untested"],
            "tests_run": unit["tests_run"] or None,
            "reviewed_paths": unit["reviewed_paths"],
            "attack_paths": unit["attack_paths"],
            "attempts": unit["attempts"],
            "confirmed": unit["confirmed"],
            "diffstat": stats_by_id.get(unit["id"]),
            "apply_check": checks.get(unit["id"]),
            "decline_reason": unit["decline_reason"] or None,
        })
        + "\n"
        for unit in units
    )


def clear_stale_products(patches_dir: Path, produced: set[str]) -> list[str]:
    """Remove F<n>.patch / F<n>.md files an earlier run left that this run did not write.

    Only the script's own product names (F<n>.patch, F<n>.md) are removed;
    every other file in the folder is left alone.
    """
    removed: list[str] = []
    for path in sorted(patches_dir.iterdir()):
        if path.suffix not in {".patch", ".md"} or not FINDING_ID_RE.match(path.stem):
            continue
        if path.name in produced or os.path.isdir(path):
            continue
        path.unlink()
        removed.append(path.name)
    return removed


def ensure_gitignore(report_dir: Path) -> str:
    """Fence the report directory with a `*` .gitignore if it has none.

    Returns "written" when the fence was just added, "present" when an
    existing .gitignore already ignores everything, and "open" when one exists
    but has no bare `*` line; an existing file is never rewritten.
    """
    path = report_dir / ".gitignore"
    if os.path.lexists(path):
        try:
            existing = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "open"
        return "present" if "*" in (line.strip() for line in existing.splitlines()) else "open"
    path.write_bytes(b"*\n")
    return "written"


def report_path_from_root(report_dir: Path, top: str | None, fallback: str) -> str:
    """The report directory as a path from the repository root, for the apply command.

    Falls back to the bare folder name when git cannot name a root or the
    folder sits outside it.
    """
    if top is None:
        return fallback
    return absolute.relative(os.path.realpath(report_dir), os.path.realpath(top)) or fallback


def resolve_report_dir(patches_dir: Path) -> Path:
    """The report directory holding `patches_dir`, validated by name."""
    # abspath folds ".." without following symlinks, so the checks below see this path's own names.
    patches_abs = Path(os.path.abspath(patches_dir))
    report_dir = patches_abs.parent
    if patches_abs.name != PATCHES_DIR_NAME:
        msg = (
            f"patches dir must be a directory named {PATCHES_DIR_NAME!r} inside the "
            f"report directory; got {patches_abs}"
        )
        raise PatchError(msg)
    if not plugin.REPORT_DIR_RE.match(report_dir.name):
        msg = (
            "patches dir must live inside a CLAUDE-SECURITY-<timestamp> report "
            f"directory; its parent is {report_dir.name!r}. Refusing rather than "
            "fence the wrong directory with a .gitignore."
        )
        raise PatchError(msg)
    return report_dir


def stamp_scan_prefix(report_dir: Path) -> str:
    """The `scan_prefix` recorded in the report's one revision stamp."""
    stamps = [path for path in report_dir.iterdir() if plugin.is_revision_stamp(path)]
    if len(stamps) != 1:
        msg = (
            f"the report directory must hold exactly one {plugin.REVISION_PREFIX}*.json "
            f"stamp; {report_dir.name} holds {len(stamps)}"
        )
        raise PatchError(msg)
    try:
        stamp = strictjson.load(stamps[0])
    except ValueError as error:
        msg = f"{stamps[0].name} is not valid JSON: {error}"
        raise PatchError(msg) from error
    prefix = stamp.get("scan_prefix") if is_map(stamp) else None
    if not is_str(prefix) or not scan_prefix_shaped(prefix):
        msg = f"{stamps[0].name} scan_prefix {prefix!r} is not a path prefix"
        raise PatchError(msg)
    return prefix


def report_findings(report_dir: Path, scan_prefix: str) -> dict[str, ReportFinding]:
    """The report's findings by id, in report order, each `file` made repository-relative."""
    name = plugin.JSONL_NAME
    try:
        lines = (report_dir / name).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        msg = f"{name} is missing from the report directory"
        raise PatchError(msg) from error
    except ValueError as error:
        msg = f"{name} is not UTF-8 text: {error}"
        raise PatchError(msg) from error
    findings: dict[str, ReportFinding] = {}
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = strictjson.loads(line)
        except ValueError as error:
            msg = f"{name} line {number} is not valid JSON: {error}"
            raise PatchError(msg) from error
        if not is_map(record):
            msg = f"{name} line {number} is not a finding object"
            raise PatchError(msg)
        finding_id = field(record.get("id"), f"{name} line {number} id")
        if not FINDING_ID_RE.match(finding_id):
            msg = f"{name} line {number}: id {finding_id!r} is not a finding id"
            raise PatchError(msg)
        if finding_id in findings:
            msg = f"{finding_id} appears more than once in {name}"
            raise PatchError(msg)
        severity = field(record.get("severity"), f"{finding_id} severity")
        if severity not in Severity.__members__:
            msg = f"{name} line {number}: {finding_id} severity {severity!r} is not a severity"
            raise PatchError(msg)
        declared = field(record.get("file"), f"{finding_id} file")
        file = repository_file(scan_prefix, file=declared)
        off_shape = not declared or declared.startswith("/") or "\\" in declared
        if off_shape or file.split("/")[0] in {".", ".."}:
            msg = f"{name} line {number}: {finding_id} file {declared!r} is not a repository path"
            raise PatchError(msg)
        findings[finding_id] = ReportFinding(Severity[severity], {**record, "file": file})
    return findings


def select_units(findings: dict[str, ReportFinding], selection: str) -> list[str]:
    """The ids `selection` names -- `all`, `high`, or ids like `F1,F3` -- in report order."""
    if selection == "all":
        chosen = set(findings)
    elif selection == "high":
        chosen = {i for i, finding in findings.items() if finding.severity >= Severity.HIGH}
    else:
        chosen = {part.strip() for part in selection.split(",")}
        malformed = sorted(i for i in chosen if not FINDING_ID_RE.match(i))
        if malformed:
            msg = (
                f"selection {selection!r}: {', '.join(map(repr, malformed))} is not a finding id "
                "(F<number>, at most 9 digits); a selection is all, high, or ids like F1,F3"
            )
            raise PatchError(msg)
        unknown = sorted(chosen - findings.keys(), key=finding_number)
        if unknown:
            msg = f"{', '.join(unknown)} is not a finding in the report's {plugin.JSONL_NAME}"
            raise PatchError(msg)
    ids = [i for i in findings if i in chosen]
    if not ids:
        msg = f"nothing to patch: no finding in the report matches the selection {selection!r}"
        raise PatchError(msg)
    return ids


def prepare(report_dir: Path, *, selection: str, repo_root: str, base: str) -> int:
    """Lay out a patch run for the selected findings; print its directories and unit ids."""
    report_dir = Path(os.path.abspath(report_dir))
    if not plugin.REPORT_DIR_RE.match(report_dir.name):
        msg = f"{report_dir.name!r} is not a CLAUDE-SECURITY-<timestamp> report directory"
        raise PatchError(msg)
    top = git_toplevel(repo_root)
    if top is None:
        msg = f"--repo-root {repo_root!r}: git names no repository there"
        raise PatchError(msg)
    if not Path(repo_root).samefile(top):
        msg = f"--repo-root {repo_root!r} is not the top level of its repository; git names {top}"
        raise PatchError(msg)
    if git.run(repo_root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}") is None:
        msg = f"--base {base}: git cannot resolve it to a commit in {repo_root}"
        raise PatchError(msg)
    findings = report_findings(report_dir, stamp_scan_prefix(report_dir))
    ids = select_units(findings, selection)
    started = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    patch_dir = report_dir / plugin.RUN_DIR_NAME / f"{PATCH_DIR_PREFIX}{started}"
    try:
        patch_dir.mkdir(parents=True)
    except FileExistsError as error:
        msg = f"{patch_dir} already exists (a run prepared this same second); run this again"
        raise PatchError(msg) from error
    findings_dir = patch_dir / FINDINGS_DIR_NAME
    findings_dir.mkdir()
    patches_dir = report_dir / PATCHES_DIR_NAME
    patches_dir.mkdir(exist_ok=True)
    for unit_id in ids:
        text = strictjson.text(findings[unit_id].record, indent=2) + "\n"
        (findings_dir / f"{unit_id}.json").write_bytes(text.encode())
    print(f"patch_dir: {patch_dir}")
    print(f"patches_dir: {patches_dir}")
    print(f"units: {strictjson.text(ids)}")
    return 0


def render(patch_dir: Path, patches_dir: Path, scan_root: str, base: str) -> int:
    units = load_units(patch_dir)
    report_dir = resolve_report_dir(patches_dir)
    top = git_toplevel(scan_root)
    report_ref = shlex.quote(report_path_from_root(report_dir, top, report_dir.name))
    stats_by_id: dict[str, list[DiffStat] | None] = {}
    checks: dict[str, str] = {}
    produced: set[str] = set()
    for unit in units:
        written = unit["status"] == "patch_written"
        diff = read_diff(patch_dir, unit["id"], required=written)
        stats = numstat(diff) if diff is not None else None
        stats_by_id[unit["id"]] = stats
        if written and diff is not None:
            patch_path = patches_dir / f"{unit['id']}.patch"
            header = header_comment(unit, base, report_ref)
            patch_path.write_bytes(header.encode("utf-8", "surrogateescape") + diff)
            check = apply_check(top, patch_path)
            checks[unit["id"]] = check
            note = note_written(unit, stats, check, report_ref)
            produced.add(f"{unit['id']}.patch")
            print(f"{unit['id']}: patch written -> {patch_path} (apply check: {check})")
        else:
            note = note_declined(unit, stats)
            print(f"{unit['id']}: no patch ({unit['status']}) -> {unit['id']}.md")
        (patches_dir / f"{unit['id']}.md").write_bytes(note.encode("utf-8", "surrogateescape"))
        produced.add(f"{unit['id']}.md")
    index = index_markdown(units, base, report_dir.name, report_ref)
    (patches_dir / "PATCHES.md").write_bytes(index.encode("utf-8", "surrogateescape"))
    (patches_dir / "patches.jsonl").write_bytes(jsonl(units, base, stats_by_id, checks).encode())
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


def misplaced_patch_run_reason(patch_dir: Path) -> str | None:
    """Why `patch_dir` is not where a patch run lives, or None when it is:
    `<report>/.claude-security-run/patch-<ts>`, none of the three a symbolic link."""
    run_dir = patch_dir.parent
    report_dir = run_dir.parent
    if not PATCH_DIR_RE.match(patch_dir.name):
        return f"'{patch_dir.name}' is not named patch-<timestamp>"
    if run_dir.name != plugin.RUN_DIR_NAME:
        return f"'{patch_dir.name}' is not inside {plugin.RUN_DIR_NAME}/"
    if not plugin.REPORT_DIR_RE.match(report_dir.name):
        return f"'{report_dir.name}' is not a CLAUDE-SECURITY-<timestamp> report directory"
    for directory in (patch_dir, run_dir, report_dir):
        if is_link(directory):
            return f"'{directory}' is a symbolic link"
    return None


def refuse_reason(path: Path) -> str | None:
    """Why `path` may NOT be deleted as a scratch workspace, or None when it may.

    Only `<report>/.claude-security-run/patch-<ts>/scratch-F<n>` holding its
    own `.git` may be deleted; every other shape is refused.
    """
    leaf = Path(os.path.abspath(path))
    if is_link(leaf):
        return "it is a symbolic link"
    if not os.path.isdir(leaf):
        return "it is not a directory"
    if not SCRATCH_NAME_RE.match(leaf.name):
        return "its name is not scratch-F<n>"
    if reason := misplaced_patch_run_reason(leaf.parent):
        return reason
    dot_git = leaf / ".git"
    if is_link(dot_git) or not os.path.isdir(dot_git):
        return "it holds no .git directory of its own"
    return None


def retry_removal(
    root: str,
    func: Callable[..., object],
    path: str,
    exc_info: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    """Retry a removal rmtree could not do, after making the entry deletable.

    On Windows that is the entry's read-only bit (never a symlink's); on POSIX the owner write bit
    of its parent, granted only to a directory (never a symlink) inside `root`, the tree being
    removed. An entry already gone counts as deleted.
    """
    if isinstance(exc_info[1], FileNotFoundError):
        return
    if func not in {os.unlink, os.rmdir}:
        raise exc_info[1]
    with suppress(FileNotFoundError):
        if os.name == "nt":
            if not is_link(path):
                Path(path).chmod(stat.S_IWRITE)
        else:
            parent = Path(os.path.abspath(path)).parent
            if os.path.commonpath([root, parent]) == root and not is_link(parent):
                mode = parent.stat().st_mode
                if not mode & stat.S_IWUSR:
                    parent.chmod(mode | stat.S_IWUSR)
        func(path)


def remove_workspace(path: Path) -> None:
    """Delete one scratch workspace, refusing anything off the fenced layout."""
    reason = refuse_reason(path)
    if reason is not None:
        msg = f"refusing to remove '{path}': {reason}"
        raise PatchError(msg)
    root = os.path.abspath(path)
    try:
        shutil.rmtree(root, onerror=functools.partial(retry_removal, root))
    except OSError as error:
        detail = console.removal_failure_detail(error)
        msg = f"could not remove '{path}': {detail}"
        raise PatchError(msg) from error


def remove_workspaces_in(patch_dir: Path) -> tuple[list[str], list[str]]:
    """Remove every scratch workspace in a patch run directory.

    Returns (removed names, warnings). Never raises: a workspace that cannot
    be removed is reported as a warning.
    """
    removed: list[str] = []
    warnings: list[str] = []
    try:
        paths = sorted(patch_dir.iterdir())
    except OSError as error:
        return removed, [f"could not list '{patch_dir}': {error}"]
    for path in paths:
        if not path.name.startswith("scratch-"):
            continue
        try:
            remove_workspace(path)
        except PatchError as error:
            warnings.append(str(error))
        else:
            removed.append(path.name)
    return removed, warnings


def remove_patch_run(patch_dir: Path) -> tuple[list[Path], list[str]]:
    """Remove a finished patch run directory, and its run directory if now empty.

    Returns (removed paths, warnings). Never raises; only the recipe's own
    `<report>/.claude-security-run/patch-<ts>` layout is deleted.
    """
    target = Path(os.path.abspath(patch_dir))
    run_dir = target.parent
    if reason := misplaced_patch_run_reason(target):
        return [], [f"left '{patch_dir}' in place: {reason}"]
    root = str(target)
    try:
        shutil.rmtree(root, onerror=functools.partial(retry_removal, root))
    except OSError as error:
        detail = console.removal_failure_detail(error)
        return [], [f"could not remove '{patch_dir}': {detail}"]
    try:
        run_dir.rmdir()
    except OSError:
        return [target], []
    return [target, run_dir], []


def remove_args(argv: list[str]) -> RemoveArgs:
    """The `--remove-scratch` command line, parsed; a usage error exits 2."""
    parser = argparse.ArgumentParser(
        prog="patch_artifacts.py --remove-scratch",
        description="Delete one fenced scratch workspace.",
        allow_abbrev=False,
    )
    parser.add_argument("workspace", help="the scratch workspace a patch run made")
    return parser.parse_args(argv, namespace=RemoveArgs())


def prepare_args(argv: list[str]) -> PrepareArgs:
    """The `--prepare` command line, parsed; a usage error exits 2."""
    parser = argparse.ArgumentParser(
        prog="patch_artifacts.py --prepare",
        description="Lay out a patch run for a report's selected findings.",
        allow_abbrev=False,
    )
    parser.add_argument("report_dir", help="the CLAUDE-SECURITY-<timestamp> report directory")
    parser.add_argument("selection", help="all, high, or finding ids such as F1,F3")
    parser.add_argument("--repo-root", required=True, help="the repository's top-level directory")
    parser.add_argument("--base", required=True, help="the revision every patch is built against")
    args = parser.parse_args(argv, namespace=PrepareArgs())
    if not os.path.isdir(args.report_dir):
        parser.error(f"report dir is not a directory: {args.report_dir}")
    if not plugin.SHA_RE.match(args.base):
        parser.error(f"--base {args.base!r} is not a hex revision id")
    return args


def render_args(argv: list[str]) -> RenderArgs:
    """The render command line, parsed; a usage error exits 2."""
    parser = argparse.ArgumentParser(
        prog="patch_artifacts.py",
        description="Render suggested-fix patch files and notes from a patch run directory.",
        epilog=(
            "Also: --prepare <report_dir> <selection> --repo-root <dir> --base <sha> lays out "
            "a patch run; --remove-scratch <workspace> deletes one fenced scratch workspace."
        ),
        allow_abbrev=False,
    )
    parser.add_argument("patch_dir", help="the patch run dir holding patches.json and F<n>.diff")
    parser.add_argument("patches_dir", help="the report's patches/ directory to write into")
    parser.add_argument("scan_root", help="the user's repository root (for git apply --check)")
    parser.add_argument("--base", required=True, help="the revision every patch applies to")
    args = parser.parse_args(argv, namespace=RenderArgs())
    for label, path in (("patch dir", args.patch_dir), ("patches dir", args.patches_dir)):
        if not os.path.isdir(path):
            parser.error(f"{label} is not a directory: {path}")
    if not plugin.SHA_RE.match(args.base):
        parser.error(f"--base {args.base!r} is not a hex revision id")
    return args


def dispatch(argv: list[str]) -> int:
    """Run the form the first argument names. Raises PatchError; a usage error exits 2."""
    if argv and argv[0] == "--remove-scratch":
        workspace = remove_args(argv[1:]).workspace
        remove_workspace(Path(workspace))
        print(f"removed workspace {workspace!r}")
        return 0
    if argv and argv[0] == "--prepare":
        wanted = prepare_args(argv[1:])
        return prepare(
            Path(wanted.report_dir),
            selection=wanted.selection,
            repo_root=wanted.repo_root,
            base=wanted.base,
        )
    args = render_args(argv)
    return render(Path(args.patch_dir), Path(args.patches_dir), args.scan_root, args.base)


def main(argv: list[str]) -> int:
    try:
        return dispatch(argv)
    except PatchError as error:
        sys.stderr.write(f"patch_artifacts.py: {error}\n")
        return 1
    except OSError as error:
        sys.stderr.write(
            f"patch_artifacts.py: could not read or write the report's files: {error}\n"
        )
        return 1


if __name__ == "__main__":
    console.tolerate_undecodable_names()
    sys.exit(main(sys.argv[1:]))
