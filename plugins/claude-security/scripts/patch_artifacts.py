#!/usr/bin/env python3
"""Prepare a patch run, and render the suggested-fix products from it.

`--prepare` lays out a patch run for a report: it checks the repository root
and the base revision, makes the run's working directory and the report's
`patches/` directory, writes one `findings/F<n>.json` per unit
(the report's record, its `file` decoded to the file's exact name and made
repository-relative), and prints the two
directories, the unit ids, and the patches of the units' findings that `patches/` already holds,
or that lie in an earlier- folder alone, if any. In a pull request's GitHub Action job, it first
leaves out, and names, each finding whose fix, by the probe's answer, an earlier comment on the
pull request still offers, for the finding's line and at the grade that this run gives it, unless
findings share its id.
Where none is left, it makes nothing, and the list of ids that it prints is empty.

The render form reads the run's `patches.json`, `findings/F<n>.json`, raw `F<n>.diff` files,
`F<n>.paths.<round>` files and `F<n>.notes` files (a verifier's notes), and
writes into the report's `patches/` directory:

  * `F<n>.patch` -- the diff behind an explanatory comment header;
  * `F<n>.md` -- a short note per finding, whether or not a patch was written;
  * `PATCHES.md` and `patches.jsonl` -- the index, prose and machine form;
  * the report directory's `.gitignore` (the single line `*`) if it lacks one.

It also reads the report's findings and revision stamp, so that a written patch's header
and note can say what became of the other findings.

Each written patch is checked against the repository (apply_check()), which changes no
file in the user's working tree and not git's index. The whole patch run directory --
scratch workspaces, prepared findings, raw diffs, paths files, notes and the record -- is
removed once the products are in place in `patches/`, along with the run directory above it when
nothing else remains there.

The products are first written in a folder inside the patch run directory. Only then does
what an earlier run wrote in `patches/` move into a new `earlier-<UTC time>/` folder inside
it, and the new products take its place.

The scratch forms tend one unit's scratch workspace, the shared clone its fix is
developed in: `--open-scratch` makes it, `--stage` stages what the generator
changed and removes the unit's `F<n>.notes`, `--clean-scratch` removes the
untracked files left in it and keeps what is
staged, `--staged` prints the finding's recommendation and what is staged, for the reviewers,
`--keep-notes` writes its standard input, the verifier's notes, beside it as `F<n>.notes`, and
for an attempt's first notes shows the recommendation once more,
`--write-diff` writes the staged diff beside it as `F<n>.diff` and lists the
paths that diff touches, `--reset-scratch` returns it to the base for another
attempt, and `--remove-scratch` deletes it. Each takes the workspace's path and
refuses any path that is not `<report>/.claude-security-run/patch-<ts>/scratch-F<n>`.

A `--repo-root` or a scan root in a git directory, which is a bare repository or a checkout's
.git, is refused; a linked worktree there passes. Unless CLAUDE_SECURITY_ROOT_ELSEWHERE is 1, so
is one outside the session's own folder and repository. So are `--prepare`'s and
`--open-scratch`'s report where it does not lie in or below the working directory, and a
workspace that does not lie there either, unless its .git is the nearest one to the shell.
`--remove-scratch` runs no git and makes neither check.

Usage:
  patch_artifacts.py --prepare <report_dir> <selection> --repo-root <dir> --base <sha>
  patch_artifacts.py --open-scratch <workspace> --repo-root <dir> --base <sha>
  patch_artifacts.py --stage | --clean-scratch | --staged | --write-diff <workspace>
  patch_artifacts.py --keep-notes <workspace> < notes
  patch_artifacts.py --reset-scratch | --remove-scratch <workspace>
  patch_artifacts.py <patch_dir> <patches_dir> <scan_root> --base <sha>

Exits 0 on success (declined findings included), 1 on a refusal naming what is
wrong, 2 on a usage error.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import textwrap
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING, NamedTuple, TypedDict, final

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (
    absolute,
    atomic,
    console,
    display,
    git,
    marker,
    plugin,
    products,
    removal,
    strictjson,
    unidiff,
)
from lib.exhaustiveness import unreachable
from lib.finding import FINDING_ID, Severity, listed_in, percent, repository_file, unpercent
from lib.link import is_link
from lib.markdown import apart, code_span, span
from lib.place import in_git_directory, outside, refusal
from lib.strictjson import JsonMap, is_int, is_list, is_map, is_str
from lib.surface_patch import (
    AFTER_APPLY,
    COPY_FIRST,
    LEFT_HALFWAY,
    WAY_BACK,
    Tried,
    Way,
    in_the_way,
    paths_and_folders,
    pointers_in,
    ways_told,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Literal

FINDING_ID_RE = re.compile(rf"^{plugin.PATCH_UNIT_ID_PATTERN}\Z")


def finding_number(finding_id: str) -> int:
    """The number in a finding id, for sorting ids as a reader expects (F2 before F10)."""
    return int(finding_id[1:])


REGULAR_FILE_MODE = "100644"
# lib/git.py's switches, and two that overrule the user's diff.renames and diff.submodule.
PINNED_DIFF = (*git.PLAIN_DIFF, "--find-renames", "--submodule=short")
FINDINGS_DIR_NAME = "findings"
SCRATCH_PREFIX = "scratch-"
SCRATCH_NAME_RE = re.compile(rf"^{re.escape(SCRATCH_PREFIX)}{plugin.PATCH_UNIT_ID_PATTERN}\Z")
PATCH_DIR_PREFIX = "patch-"
PATCH_DIR_RE = re.compile(rf"^{re.escape(PATCH_DIR_PREFIX)}[0-9][0-9-]*\Z")
# A scratch workspace's ref for the commit it was opened at. No other repository has this ref.
BASE_REF = "refs/claudesecurity/base"
CLEAN_UNTRACKED = ("clean", "-f", "-d", "-q")
# Only a .pyc directly in a __pycache__ folder: any other new file can be part of a fix.
NOT_PYTHON_CACHES = ":(exclude,glob)**/__pycache__/*.pyc"
STATUSES = ("patch_written", "declined", "skipped_stale")
NOT_CONFIRMED = (
    "The review found this finding is not exploitable as the report describes at this "
    "revision, so no patch was written for it."
)
PATCH_ALONE = (
    "The patch can differ from the report's recommendation. A request to apply this patch, in any "
    "way, does not cover the rest of the recommendation, or anything that the verifier noted."
)
NOTES_MAY_MISS = (
    "The verifier's notes may not name every step that the patch leaves out: compare the patch "
    "with the recommendation."
)
NOTES_APART = (
    "A request to apply this patch, in any way, does not cover anything that the verifier noted."
)
NOTES_NOT_RECORDED = (
    "the verifier's notes on what the patch leaves out were not recorded; compare the patch with "
    "the finding yourself"
)
MAY_BE_PART = (
    "this patch may not fully fix the finding: read the verifier's notes or warning in {}.md"
)
NOTES_RELAY = (
    "relay: say this to the user exactly as printed, in your closing message: {}: a patch may not "
    "fully fix its finding. Read the verifier's notes or warning in the .md file beside each patch "
    "before you apply it."
)
NO_RECOMMENDATION = "(the report gives none)"
NO_NOTES_GIVEN = (
    "no notes on standard input: put <<'END_NOTES' after this command, the notes on the next "
    "lines, and END_NOTES alone on the last"
)
LOOK_AGAIN = (
    "If the change leaves out a step above, or carries it out only in part, and your notes have no "
    "line for it, run this call once more with all your notes and that line. Otherwise go on."
)
NOTES_SUFFIX = ".notes"
# What can open a line of F<n>.notes before its note: a list mark, and the heading.
NOTE_LEAD_RE = re.compile(r"^\s*(?:(?:[-*]|[0-9]+\.) )?(?:\W*NOTES\W*?:\**)?")
# A line of these words alone is a heading, a fence, "none", or an indented END_NOTES.
NO_NOTE_WORDS = frozenset({"notes", "for", "the", "user", "text", "none", "end"})
UNTESTED_NOTICE = "no project test of the patched code was run"
NO_REPORT = "NO REPORT"
NO_REPORT_NOTICE = "no list of attack paths was recorded for attempt {}, so none from it is shown"
MAX_ATTEMPTS = 2
ROUND_INFIX = ".paths."
ROUND_FILE_RE = re.compile(rf"^{plugin.PATCH_UNIT_ID_PATTERN}{re.escape(ROUND_INFIX)}[0-9]+\Z")
BLOCK_FENCE_RE = re.compile(r"```\w*")
BLOCK_LINE_RE = re.compile(
    r"(?:[-*]\s+)?(?P<number>\d+)\s*(?:[.)](?:\s*\|)?|\|)(?P<kind>[^|]*)\|(?P<text>.+)"
)
BLOCK_COUNT_RE = re.compile(r"(?:[-*]\s+)?[*`]*PATHS:[*`\s]*(\d+)[*`.]*", re.IGNORECASE)
BY_HAND = "leave any changes of your own in your files, and make the patch's change by hand"
HANDS_OFF = (
    "leave your files as they are, and make none of this patch's changes, not even a part that "
    "would apply cleanly, until a person has decided what to do with each path in its way"
)
KEEP_IT = "git does not track the file, so it may be the only copy: do not delete it"
KEEP_THEM = "git may hold no copy of anything that stands in its way: do not delete it"
MAKE_AGAIN = (
    "leave your files as they are, and make none of this patch's changes, not even a part that "
    "would apply cleanly, until a person has decided how the fix is made again"
)
NO_WARNING_YET = "#\n#\n#\n"
MARKED_OUT = (
    "The plugin's script has marked out each line of the patch file's diff with `# `, so git apply "
    "refuses the file: without the marks it can fail halfway. Unless your repository already holds "
    "that content, the fix for each file named here must be made again"
)
ANALYSIS_REFUSAL = "is an attack surface analysis's folder: name a scan's report or a triage's"


@final
class Withholding:
    """How text that repeats part of a credential's source line is found and replaced."""

    WINDOW = 12
    RUN_RE = re.compile(rf"[^\s\"'`]{{{WINDOW},}}")
    MARKER = "[credential withheld: see {file}:{line}]"


class PathKind(str, Enum):
    """An attack path's kind, as the script reads it from the fresh reviewer's line."""

    OPENED = "opened"
    STILL_REACHABLE = "still_reachable"
    SET_ASIDE = plugin.SET_ASIDE

    @classmethod
    def named(cls, word: str) -> PathKind | None:
        """The kind a word names, whatever its case, spacing or marks; None when it names none."""
        value = re.sub(r"[\s`*.:;-]+", "_", word.lower()).strip("_")
        return next((kind for kind in cls if kind.value == value), None)

    @property
    def blocks_patch(self) -> bool:
        return self is not PathKind.SET_ASIDE


PATH_KIND_LABELS = {
    PathKind.OPENED: "opened by the rejected change",
    PathKind.STILL_REACHABLE: "the finding's exploit, still reachable by another route",
    PathKind.SET_ASIDE: "set aside as outside this finding; not addressed here",
}


class AttackPath(TypedDict):
    """An attack path the fresh reviewer reported; still_reachable where its word names no kind."""

    kind: PathKind
    text: str


class DiffStat(TypedDict):
    """Per-file added/deleted line counts, "-" for a binary file as git prints it."""

    path: str
    added: int | Literal["-"]
    deleted: int | Literal["-"]


OLDER = "the scan judged this flaw older than the change that it reviewed"
NOT_IN_BASE = (
    "The finding names {}, which your working tree has but the revision that patches are written "
    "against does not. Git ignores such a file, it belongs to a submodule, or it is not committed. "
    "Check by hand whether it needs a fix."
)


class Unit(TypedDict):
    """A validated unit record, ready to be written out."""

    id: str
    title: str
    others: list[str]
    older: bool
    not_in_base: list[str]
    check_said: str
    status: str
    summary: str
    claims: dict[plugin.Claim, products.Assessment]
    untested: bool
    tests_run: str
    reviewed_paths: list[str]
    attack_paths: list[AttackPath]
    no_report: list[int]
    attempts: int | None
    confirmed: bool | None
    decline_reason: str
    recommendation: str
    verifier_notes: list[str] | None


def may_be_part(unit: Unit) -> bool:
    """Whether `unit` is a written patch whose verifier noted something, or whose notes were not
    recorded."""
    return unit["status"] == "patch_written" and unit["verifier_notes"] != []


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


class WorkspaceArgs(argparse.Namespace):
    """The parsed command line of a form that tends one scratch workspace."""

    workspace: str = ""


class OpenArgs(WorkspaceArgs):
    """The parsed `--open-scratch` command line."""

    repo_root: str = ""
    base: str = ""


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
    """A one-line record field: each run of white space is folded to one space, and none is left at
    either end."""
    return " ".join(field(value, what).split())


def field_list(value: object, what: str) -> list[str]:
    """A list-of-strings record field."""
    if value is None:
        return []
    if not is_list(value):
        msg = f"{what} must be a list of strings"
        raise PatchError(msg)
    return [field(item, f"{what}[{index}]") for index, item in enumerate(value)]


def build_claims(raw: object, unit_id: str, status: str) -> dict[plugin.Claim, products.Assessment]:
    """Validate the three named claims. A written patch needs all three CONFIDENT."""
    claims_map: JsonMap = {}
    if raw is not None:
        if not is_map(raw):
            msg = f"{unit_id}: claims must be an object keyed by claim name"
            raise PatchError(msg)
        claims_map = raw
    out: dict[plugin.Claim, products.Assessment] = {}
    for claim in plugin.Claim:
        entry = claims_map.get(claim.key)
        if not is_map(entry):
            if status == "patch_written":
                msg = f"{unit_id}: status is patch_written but claim {claim.key!r} is missing"
                raise PatchError(msg)
            continue
        state = field(entry.get("state"), f"{unit_id} claim {claim.key}.state").upper()
        if state not in plugin.CLAIM_STATES:
            msg = (
                f"{unit_id}: claim {claim.key!r} has state {state!r}; want one of "
                f"{', '.join(plugin.CLAIM_STATES)}"
            )
            raise PatchError(msg)
        evidence = line_field(entry.get("evidence"), f"{unit_id} claim {claim.key}.evidence")
        out[claim] = products.Assessment(state, evidence)
    if status == "patch_written":
        not_confident = [claim.key for claim, said in out.items() if said.state != plugin.CONFIDENT]
        if not_confident:
            msg = (
                f"{unit_id}: status is patch_written but {', '.join(not_confident)} "
                "is not CONFIDENT -- a patch is written only when all three claims "
                "are; record the unit as declined instead."
            )
            raise PatchError(msg)
    return out


def round_names(unit: Unit) -> list[str]:
    """The names of the unit's paths files, one for each attempt."""
    return [f"{unit['id']}{ROUND_INFIX}{n}" for n in range(1, (unit["attempts"] or 0) + 1)]


def block_lines(path: Path) -> list[str]:
    """A paths file's lines, less blank ones and code fences."""
    text = path.read_bytes().decode("utf-8-sig", "replace")
    stripped = (line.strip() for line in text.split("\n"))
    return [line for line in stripped if line and not BLOCK_FENCE_RE.fullmatch(line)]


def read_round(path: Path, site: tuple[str, str]) -> list[AttackPath] | None:
    """The attack paths in one attempt's paths file, with the credential at `site` masked; None
    where its one line is NO REPORT. Refuse a missing file and a block that is not whole."""
    remedy = (
        "copy into that file, whole, the block that ends the fresh reviewer's reply for that unit "
        "and round. If the reply's own block is not whole or not in this form, or there was no "
        f"reply, write the one line {NO_REPORT}."
    )
    if not os.path.isfile(path):
        msg = (
            f"{path.name} is missing from the patch directory -- {remedy} If the unit had no such "
            'round, correct its "attempts".'
        )
        raise PatchError(msg)
    lines = block_lines(path)
    if lines == [NO_REPORT]:
        return None
    paths: list[AttackPath] = []
    for line in lines[:-1]:
        row = BLOCK_LINE_RE.fullmatch(line)
        if row is None or row["number"] != str(len(paths) + 1):
            break
        kind = PathKind.named(row["kind"])
        said = row["text"] if kind else line[row.start("kind") :]
        shown = line_field(without_credential(said, *site), path.name)
        paths.append(AttackPath(kind=kind or PathKind.STILL_REACHABLE, text=shown))
    count = BLOCK_COUNT_RE.fullmatch(lines[-1]) if lines else None
    if count is None or len(paths) != len(lines) - 1 or count[1] != str(len(paths)):
        msg = (
            f"{path.name} does not hold a whole block, which is lines `<number> | <kind> | <path>` "
            f"numbered 1 to N and then, last, `PATHS: N`: line {len(paths) + 1} of its block "
            f"(blank and ``` lines not counted) does not fit, or is not the last -- {remedy}"
        )
        raise PatchError(msg)
    return paths


def check_rounds(unit: Unit, rounds: list[list[AttackPath] | None]) -> None:
    """Refuse a written patch whose last attempt has no report or has a path that blocks a patch,
    and "confirmed" false beside a still-reachable path."""
    unit_id, names = unit["id"], round_names(unit)
    if unit["status"] == "patch_written":
        last = rounds[-1]
        if last is None:
            msg = (
                f"{unit_id}: status is patch_written but {names[-1]} says {NO_REPORT} -- a patch "
                "needs the fresh reviewer's report: record the unit as declined."
            )
            raise PatchError(msg)
        blocking = next((path for path in last if path["kind"].blocks_patch), None)
        if blocking is not None:
            msg = (
                f"{unit_id}: status is patch_written but the fresh reviewer reported a path it did "
                f"not set aside ({blocking['kind'].value}: {blocking['text']}) -- that blocks the "
                "patch: record the unit as declined."
            )
            raise PatchError(msg)
    for name, paths in zip(names, rounds):
        reachable = next(
            (path for path in paths or () if path["kind"] is PathKind.STILL_REACHABLE), None
        )
        if unit["confirmed"] is False and reachable is not None:
            msg = (
                f'{unit_id}: "confirmed": false cannot sit beside a still_reachable path '
                f"({reachable['text']}) -- if that path reaches the function or line the finding "
                'names, the panel disagreed: drop "confirmed" and decline on that path; if it '
                "reaches only other code, the refutation stands: change that line's kind to "
                f"set_aside in {name}"
            )
            raise PatchError(msg)


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
    if not is_int(raw) or not 0 <= raw <= MAX_ATTEMPTS:
        msg = (
            f'{unit_id}: "attempts" must be a whole number of fix attempts made, '
            f"{MAX_ATTEMPTS} at most"
        )
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
    if status != "patch_written" and not decline_reason.strip():
        msg = f"{unit_id}: status {status} needs a decline_reason saying why no patch was written"
        raise PatchError(msg)
    untested = item.get("untested")
    if untested is None and status == "patch_written":
        msg = (
            f'{unit_id}: status is patch_written but "untested" is missing. Set it to true when '
            "no test in the project's own suite ran the patched code, and to false otherwise. "
            "The patch header warns the reader of an untested patch."
        )
        raise PatchError(msg)
    if untested is not None and not isinstance(untested, bool):
        msg = f'{unit_id}: "untested" must be true or false'
        raise PatchError(msg)
    return Unit(
        id=unit_id,
        title=line_field(item.get("title"), f"{unit_id} title") or unit_id,
        others=[],
        older=False,
        not_in_base=[],
        check_said="",
        status=status,
        summary=line_field(item.get("summary"), f"{unit_id} summary"),
        claims=claims,
        untested=untested is True,
        tests_run=line_field(item.get("tests_run"), f"{unit_id} tests_run"),
        reviewed_paths=field_list(item.get("reviewed_paths"), f"{unit_id} reviewed_paths"),
        attack_paths=[],
        no_report=[],
        attempts=build_attempts(item.get("attempts"), unit_id, status),
        confirmed=build_confirmed(item.get("confirmed"), unit_id, status),
        decline_reason=decline_reason,
        recommendation=field(item.get("recommendation"), f"{unit_id} recommendation"),
        verifier_notes=None,
    )


def credential_site(patch_dir: Path, item: object, top: str | None, base: str) -> tuple[str, str]:
    """A credential unit's flagged line, and the marker that stands in for the credential. Two
    empty strings for any other unit, or, with a warning, when that line cannot be read or is
    blank. It refuses a prepared record that it cannot read, such as one that is no object or whose
    other_cwe_ids is no list."""
    unit_id = item.get("id") if is_map(item) else None
    path = patch_dir / FINDINGS_DIR_NAME / f"{unit_id}.json"
    if not is_str(unit_id) or not FINDING_ID_RE.match(unit_id) or not path.is_file():
        return "", ""
    try:
        record = strictjson.load(path)
        if not is_map(record):
            msg = "it is not an object"
            raise ValueError(msg)
        if not products.is_credential_record(record):
            return "", ""
    except (ValueError, products.ProductError) as error:
        msg = f"{FINDINGS_DIR_NAME}/{path.name} could not be read as a finding record ({error}); "
        raise PatchError(msg + "run --prepare again") from error
    file, line = record.get("file"), record.get("line")
    commit = products.Stamp.read(Path(os.path.abspath(patch_dir)).parents[1]).commit or base
    source = (
        git.run(top, "cat-file", "blob", git.argument(f"{commit}:{file}"))
        if top and is_str(file) and strictjson.surrogates_are_bytes(file)
        else None
    )
    lines = (source or "").split("\n")
    flagged = lines[line - 1] if is_int(line) and 0 < line <= len(lines) else ""
    if not flagged.strip():
        found = "could not read" if source is None else "found no text at"
        console.warn(
            f"{unit_id}: {found} {file}:{line} in {commit[: plugin.SHORT_ID_CHARS]}, so "
            f"{unit_id}'s text may still hold the secret; check it in "
            f"{plugin.PATCHES_DIR_NAME}/ before sharing"
        )
        return "", ""
    file = percent(str(file), percent_sign=False)
    return flagged, Withholding.MARKER.format(file=file, line=line)


def shares_credential(run: str, line: str) -> bool:
    return any(
        run[i : i + Withholding.WINDOW] in line for i in range(len(run) - Withholding.WINDOW + 1)
    )


def without_credential(value: object, line: str, marker: str) -> object:
    """`value`, with each word in its string values that repeats part of the credential's line
    `line` replaced by `marker`."""
    if is_str(value):
        return Withholding.RUN_RE.sub(
            lambda run: marker if shares_credential(run[0], line) else run[0], value
        )
    if is_list(value):
        return [without_credential(item, line, marker) for item in value]
    if is_map(value):
        return {key: without_credential(item, line, marker) for key, item in value.items()}
    return value


def verifier_notes(path: Path, site: tuple[str, str]) -> list[str] | None:
    """The notes in the file `path`, one for each line, passed through without_credential() with
    `site`. A heading and "none" are no notes. Returns None where the file is missing, or holds
    neither a note nor "none"."""
    text = path.read_text("utf-8", "surrogateescape") if path.is_file() else ""
    lines = strictjson.well_formed(str(without_credential(text, *site))).splitlines()
    said = (display.single_line(NOTE_LEAD_RE.sub("", line)) for line in lines)
    notes = [line for line in said if {*re.findall(r"[^\W_]+", line.lower())} - NO_NOTE_WORDS]
    return notes if notes or "none" in text.lower() else None


def report_fix(record: JsonMap, unit_id: str, site: tuple[str, str]) -> str:
    """The recommendation in the prepared finding `record`, passed through without_credential()
    with `site`, on one line; empty where it has none. Refuses one that is no text."""
    fix = without_credential(record.get("recommendation"), *site)
    return line_field(fix, f"{FINDINGS_DIR_NAME}/{unit_id}.json recommendation")


def base_files(top: str, base: str) -> frozenset[str] | None:
    """The files of the commit `base` in the repository at `top`, through str.casefold(). None, with
    a warning, where git gives no list."""
    # A lazy fetch would write into the user's repository.
    no_fetch = {"GIT_NO_LAZY_FETCH": "1"}
    listed = git.run(top, "ls-tree", "-r", "-z", "--name-only", base, env=no_fetch)
    if listed is None:
        console.warn(f"git could not list the files of {base}, so no note names one that it lacks")
        return None
    return frozenset(listed.casefold().split("\0")[:-1])


def not_in_base(top: str | None, held: frozenset[str] | None, finding: JsonMap) -> list[str]:
    """The files of a prepared `finding` that are in the working tree at `top` but, through
    str.casefold(), not in `held`, as base_files() gives it. Each comes once: `file`, then those
    that `also_at` and `also_filed_at` list. Empty where there is no `top` or no `held`."""
    if top is None or held is None:
        return []
    listed = (it for key in ("also_at", "also_filed_at") for it in listed_in(finding, key) or ())
    names = (site.get("file") for site in (finding, *listed))
    return [
        name
        for name in dict.fromkeys(filter(is_str, names))
        if strictjson.surrogates_are_bytes(name)
        and name.casefold() not in held
        and os.path.isfile(Path(top, git.for_disk(name)))
    ]


def refuse_uncounted_rounds(patch_dir: Path, units: list[Unit]) -> None:
    """Refuse a paths file that belongs to no attempt of `units`, unless it is empty."""
    counted = {name for unit in units for name in round_names(unit)}
    laid = {path.name for path in patch_dir.iterdir() if ROUND_FILE_RE.match(path.name)}
    uncounted = sorted(name for name in laid - counted if os.lstat(patch_dir / name).st_size)
    if uncounted:
        msg = (
            f"{', '.join(uncounted)}: patches.json counts no such attempt -- record each reviewed "
            "unit as patch_written or declined, with all its attempts. Where a file is misnamed or "
            "is no attempt's, write its block to the right name, if there is one, and then write "
            "that file empty."
        )
        raise PatchError(msg)


def load_paths(patch_dir: Path, unit: Unit, site: tuple[str, str]) -> None:
    """Set the unit's attack paths from its paths files, the last attempt's first, and its attempts
    with no report. A written patch leaves out the paths that blocked an earlier attempt."""
    rounds = [read_round(patch_dir / name, site) for name in round_names(unit)]
    check_rounds(unit, rounds)
    unit["no_report"] = [n for n, paths in enumerate(rounds, 1) if paths is None]
    written = unit["status"] == "patch_written"
    unit["attack_paths"] = [
        path
        for paths in reversed(rounds)
        for path in paths or ()
        if not (written and path["kind"].blocks_patch)
    ]


def load_units(patch_dir: Path, top: str | None, base: str) -> list[Unit]:
    """Read and validate patches.json against the prepared units, with the units' paths files.

    A written unit takes its `recommendation` from its `findings/<id>.json`, and its
    `verifier_notes` from `<id>.notes`.

    Every unit id must have the `findings/<id>.json` that `--prepare` laid out. A unit's `older` is
    read from that file, and its `not_in_base` is what not_in_base() gives for it. A unit keeps its
    recommendation only where that file has one.
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
    sites = [credential_site(patch_dir, item, top, base) for item in units_raw]
    units = [
        build_unit(without_credential(item, *site), i)
        for i, (item, site) in enumerate(zip(units_raw, sites))
    ]
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
    prepared = {
        path.stem
        for path in findings_dir.glob("*.json")
        if path.is_file() and FINDING_ID_RE.match(path.stem)
    }
    unprepared = [unit["id"] for unit in units if unit["id"] not in prepared]
    if unprepared:
        msg = (
            f"patches.json names {', '.join(unprepared)}, which --prepare did not lay out; "
            f"this run's units are {', '.join(sorted(prepared, key=finding_number)) or 'none'} "
            "(the ids --prepare printed)"
        )
        raise PatchError(msg)
    held = None if top is None else base_files(top, base)
    for unit, site in zip(units, sites):
        record = strictjson.load(findings_dir / f"{unit['id']}.json")
        if not is_map(record):
            msg = f"{FINDINGS_DIR_NAME}/{unit['id']}.json is not an object; run --prepare again"
            raise PatchError(msg)
        unit["older"] = "older_than_the_change" in record
        unit["not_in_base"] = not_in_base(top, held, record)
        if not record.get("recommendation"):
            unit["recommendation"] = ""
        if unit["status"] == "patch_written":
            unit["recommendation"] = report_fix(record, unit["id"], site)
            unit["verifier_notes"] = verifier_notes(patch_dir / f"{unit['id']}{NOTES_SUFFIX}", site)
    refuse_uncounted_rounds(patch_dir, units)
    for unit, site in zip(units, sites):
        load_paths(patch_dir, unit, site)
    return units


def read_diff(patch_dir: Path, unit_id: str, required: bool) -> bytes | None:
    """The raw diff git wrote for this unit; None only if absent and optional.

    A required one (a written patch) must exist and start with the text `diff --git `,
    since the patch and its diffstat are built from it.
    """
    path = patch_dir / f"{unit_id}.diff"
    if not os.path.isfile(path):
        if required:
            msg = (
                f"{unit_id}: status is patch_written but {unit_id}.diff is missing from the "
                "patch directory. Write it first with --write-diff <scratch workspace>."
            )
            raise PatchError(msg)
        return None
    data = path.read_bytes()
    if required and not data.startswith(unidiff.DIFF_HEADER.encode("ascii")):
        header = unidiff.DIFF_HEADER.strip()
        msg = f"{unit_id}.diff does not start with a '{header}' header"
        raise PatchError(msg)
    return data


def display_name(name: str | None) -> str | None:
    """A `--- `/`+++ ` line's file name for display: a/ or b/ dropped, None for /dev/null."""
    if name is None:
        return None
    name = unidiff.name_field(name)
    if name == "/dev/null":
        return None
    if name.startswith(('"a/', '"b/')):
        return '"' + name[3:]
    return name[2:] if name[:2] in {"a/", "b/"} else name


def header_name(header: str) -> str | None:
    """The file name in `header`, the text after "diff --git ", where its two halves are alike but
    for a/ and b/, at their start or just after an opening quote, with a space between them. The
    result keeps any quotes. None for any other header."""
    old = header[: len(header) // 2]
    if old.startswith(("a/", '"a/')) and header == f"{old} {old.replace('a/', 'b/', 1)}":
        return old.replace("a/", "", 1)
    return None


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
                    value = line[len(key) + 1 :].split("\r", 1)[0]
                    if key.endswith("mode"):
                        modes[key] = (value.split() or [""])[0]
                    else:
                        modes[key] = value.strip() if value.startswith('"') else value
    if modes.get("rename from") and modes.get("rename to"):
        path = f"{modes['rename from']} => {modes['rename to']}"
    else:
        header = lines[0][len(unidiff.DIFF_HEADER) :].split("\r", 1)[0]
        cut = header.rfind(" b/")
        fallback = header[cut + 3 :] if cut >= 0 else header
        if not any(line.startswith(("copy to ", "rename old ", "rename new ")) for line in lines):
            fallback = header_name(header) or fallback
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
    # git ends each line with "\n" alone. splitlines() would also cut at a form feed in a file.
    for line in diff.decode("utf-8", "replace").split("\n"):
        if line.startswith(unidiff.DIFF_HEADER):
            if section:
                stats.append(section_stat(section))
            section = [line]
        elif section:
            section.append(line)
    if section:
        stats.append(section_stat(section))
    return stats


class Checked(NamedTuple):
    """apply_check()'s answer on a patch's bytes. `why` holds git's line, through apart(), or
    Tried.BLOCKED's words with the words on the paths that are in the patch's way, each path as a
    code span. It is empty where there is neither.
    `move` holds to_move()'s file, and `to` what free_beside() gives for it, each as a code span.
    Both names are plain, by PLAIN_RE. Only a BLOCKED answer can have them. It has both, or, where
    either function gives nothing, neither. Where neither is given, `missing` says what git or the
    disk could not answer, if anything. `pointer` is set where pointers_in() names a file: the
    answer is then BLOCKED, whatever git's check says, and `why` holds Way.POINTER's words and
    MARKED_OUT."""

    tried: Literal[Tried.APPLIES, Tried.REFUSED, Tried.BLOCKED, Tried.NO_ANSWER]
    why: str = ""
    move: str = ""
    to: str = ""
    missing: str = ""
    pointer: bool = False

    @property
    def recorded(self) -> str:
        """The answer as patches.jsonl holds it: 'clean', 'conflicts', 'conflicts: ...', or
        'not_run'."""
        if self.tried is Tried.APPLIES:
            return plugin.APPLY_CLEAN
        if self.tried is Tried.NO_ANSWER:
            return plugin.APPLY_NOT_RUN
        if self.tried is Tried.REFUSED or self.tried is Tried.BLOCKED:
            return plugin.APPLY_CONFLICTS + (f": {self.why}" if self.why else "")
        return unreachable(self.tried)

    @property
    def listed(self) -> str:
        """The answer as PATCHES.md tells it, after "the apply check". Empty for a clean patch."""
        if self.tried is Tried.APPLIES:
            return ""
        if self.tried is Tried.NO_ANSWER:
            return "gave no answer"
        if self.tried is Tried.REFUSED or self.tried is Tried.BLOCKED:
            return "was not clean"
        return unreachable(self.tried)

    @property
    def step(self) -> str:
        """The user's step at this patch, as the script prints it after "for the user: ". Empty
        where the script names none."""
        if self.tried is Tried.APPLIES or self.tried is Tried.NO_ANSWER:
            return ""
        if self.tried is Tried.BLOCKED:
            if self.pointer:
                return MAKE_AGAIN
            if self.move:
                return (
                    f"first move the file {self.move} to {self.to}, a name that is free. {KEEP_IT}"
                )
            return f"{HANDS_OFF}. {KEEP_THEM}"
        if self.tried is Tried.REFUSED:
            return BY_HAND
        return unreachable(self.tried)


# A plain path: nothing in it is unseen, and no letter of it is from another script.
PLAIN_RE = re.compile(r"[A-Za-z0-9._/-]+")
PATHSPEC_VARIABLES: tuple[str, ...] = (
    "GIT_LITERAL_PATHSPECS",
    "GIT_GLOB_PATHSPECS",
    "GIT_NOGLOB_PATHSPECS",
    "GIT_ICASE_PATHSPECS",
)


NO_TRACKED = "git could not list what it tracks"
NO_PATHS = "git could not list the patch's paths"


class Suggested(NamedTuple):
    """A path that to_move() or free_beside() suggests, or none. Where git or the disk gave no
    answer on the way to one, `missing` says what it could not do."""

    path: str = ""
    missing: str = ""


def untracked(root: str, path: str) -> bool | None:
    """Whether no name in git's index or in its last commit, through str.casefold(), is `path`, or
    lies below or above it. None where git gave no list."""
    head = git.run(root, "rev-parse", "--verify", "--quiet", "HEAD", ok=(0, 1))
    if head is None:
        return None
    # A new repository has no HEAD to list. A lazy fetch would write into the user's repository.
    tree = ["--with-tree=HEAD"] if head else []
    listed = git.run(root, "ls-files", "-z", *tree, env={"GIT_NO_LAZY_FETCH": "1"})
    if listed is None:
        return None
    folded = path.casefold()
    return not any(
        name == folded or name.startswith(f"{folded}/") or folded.startswith(f"{name}/")
        for name in listed.casefold().split("\0")[:-1]
    )


def to_move(root: str, diff: bytes, blockers: Mapping[Way, tuple[str, ...]]) -> Suggested:
    """The file that the user is told to move out of `diff`'s way, or nothing. It is given where all
    of this holds. in_the_way()'s `blockers` are one path, where the diff needs a folder. The path
    is plain (PLAIN_RE), and a regular file stands there. Its real path is `root`'s real path plus
    the path as given. os.path.lexists() finds a .git in no folder above it, below `root`. Last,
    through str.casefold(), the diff does not name it, and untracked() holds for it. Only these two
    ask git, and only once the others hold."""
    files = blockers.get(Way.FILE, ())
    if len(blockers) > 1 or len(files) != 1:
        return Suggested()
    (path,) = files
    fit = (
        PLAIN_RE.fullmatch(path)
        and Path(root, path).is_file()
        and os.path.realpath(Path(root, path)) == str(Path(os.path.realpath(root), path))
        and not any(
            os.path.lexists(Path(root, folder, ".git"))
            for folder in list(PurePosixPath(path).parents)[:-1]
        )
    )
    if not fit:
        return Suggested()
    listed = paths_and_folders(root, diff)
    if listed is None:
        return Suggested(missing=NO_PATHS)
    named, _ = listed
    if path.casefold() in named:
        return Suggested()
    free = untracked(root, path)
    if free is None:
        return Suggested(missing=NO_TRACKED)
    return Suggested(path if free else "")


def ignored_alike(top: str, one: str, other: str) -> bool | None:
    """Whether git ignores both of these paths in the repository at `top`, or neither. None where
    git gives no answer. Each path is plain, by PLAIN_RE."""
    # git check-ignore refuses every path while one of these variables is on in the user's shell.
    off = dict.fromkeys(PATHSPEC_VARIABLES, "0")
    listed = git.run(top, "check-ignore", "--", one, other, ok=(0, 1), env=off)
    return None if listed is None else len(listed.splitlines()) != 1


def free_beside(top: str, file: str, diff: bytes) -> Suggested:
    """`file` with ".moved" behind it, or ".moved-2" and so on up to ".moved-99": the first of these
    names at which nothing stands below `top`, and which, through str.casefold(), the file's folder
    does not hold and `diff` neither names nor needs as a folder. Nothing where there is none, where
    untracked() does not hold for it, or where ignored_alike() does not hold for it and `file`.
    Where git gives no answer, or the folder cannot be listed, the answer says what is missing.
    `file` is plain, by PLAIN_RE."""
    listed = paths_and_folders(top, diff)
    if listed is None:
        return Suggested(missing=NO_PATHS)
    try:
        beside = {entry.name.casefold() for entry in Path(top, file).parent.iterdir()}
    except OSError as error:
        reason = f"the folder of the file in the patch's way could not be listed ({error.strerror})"
        return Suggested(missing=reason)
    names = (f"{file}.moved{f'-{n}' if n > 1 else ''}" for n in range(1, 100))
    free = (
        name
        for name in names
        if not os.path.lexists(Path(top, name))
        and Path(name).name.casefold() not in beside
        and name.casefold() not in listed[0] | listed[1]
    )
    name = next(free, "")
    if not name:
        return Suggested()
    fits = untracked(top, name)
    if fits is None:
        return Suggested(missing=NO_TRACKED)
    if not fits:
        return Suggested()
    alike = ignored_alike(top, file, name)
    if alike is None:
        return Suggested(missing="git could not check its ignore rules")
    return Suggested(name if alike else "")


def apply_check(top: str | None, patch: bytes, patch_path: Path) -> Checked:
    """Whether `patch`, a patch's bytes, would apply to the user's tree. It does where
    `git apply --check` accepts it and in_the_way() names no path. BLOCKED, before git's check,
    where pointers_in() names a file. NO_ANSWER where git gave no answer, or no list of the patch's
    paths. Where git's line names "<stdin>" and a line number, the answer names `patch_path` there:
    from `top`, or in full where it lies outside."""
    if top is None:
        return Checked(Tried.NO_ANSWER)
    pointers = pointers_in(top, patch)
    if pointers:
        told = Way.POINTER.told(tuple(sorted(pointers, key=lambda path: (path.casefold(), path))))
        return Checked(Tried.BLOCKED, f"{told}. {MARKED_OUT}", pointer=True)
    checked = git.check_patch_file(top, patch)
    if checked is None:
        return Checked(Tried.NO_ANSWER)
    clean, why = checked
    if not clean:
        below = absolute.relative(os.path.realpath(patch_path), os.path.realpath(top))
        shown = " ".join(
            git.from_disk(str(Path(below or os.path.abspath(patch_path)))).splitlines()
        )
        why = re.sub(r"<stdin>(?=:\d)", lambda _: shown, why)
        return Checked(Tried.REFUSED, apart(why))
    blockers = in_the_way(top, patch)
    why = Tried.BLOCKED.told(ways_told(blockers)) if blockers else ""
    file = to_move(top, patch, blockers) if blockers else Suggested()
    to = free_beside(top, file.path, patch) if file.path else Suggested()
    if to.path:
        return Checked(Tried.BLOCKED, why, move=code_span(file.path), to=code_span(to.path))
    return Checked(Tried.on_disk(blockers), why, missing=file.missing or to.missing)


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
    return [f"- {span(s['path'])} {line_counts(s)}" for s in stats]


def quoted(text: str) -> str:
    """`text`, which a model wrote, as a Markdown quotation."""
    return "\n".join(f"> {line}".rstrip() for line in text.splitlines())


def attack_path_lines(unit: Unit) -> list[str]:
    """The fresh reviewer's attack paths as a note section, with each attempt that has no report;
    no lines when there is neither."""
    bullets = [
        f"- **{PATH_KIND_LABELS[path['kind']]}** -- {path['text']}" for path in unit["attack_paths"]
    ]
    bullets += [f"- **no report** -- {NO_REPORT_NOTICE.format(n)}" for n in unit["no_report"]]
    return ["## What the fresh reviewer reported", "", *bullets, ""] if bullets else []


def header_comment(unit: Unit, base: str, check: Checked) -> str:
    """The comment block prepended above the diff; git apply ignores it. Where `check`
    names a step, the block opens with a warning: the check's words, and the step. For a Git LFS
    pointer, it names the note, and leaves out the lines on how to apply the patch."""
    short = base[: plugin.SHORT_ID_CHARS]
    lines: list[str] = []
    if check.step:
        why = check.why.removesuffix(".")
        found = f"the apply check {check.listed}" + (f": {why}" if why else "")
        where = " to your working tree" if check.tried is Tried.REFUSED else ""
        lines = [
            f"# WARNING: do not apply this patch{where} as it is. When it was written, {found}.",
            f"# For the user: {check.step}.",
            "#",
        ]
    lines += [
        f"# Claude Security -- suggested patch for {unit['id']}: {unit['title']}",
        f"# Applies to revision {short} (the revision these patches were built against).",
        *(["#", f"# NOTE: {MAY_BE_PART.format(unit['id'])}."] if may_be_part(unit) else []),
        *(["#", f"# NOTE: {OLDER}."] if unit["older"] else []),
        *(["#", f"# {WRITTEN_FOR.format(unit['id'])}"] if unit["others"] else []),
        *(f"#   - {item}" for item in unit["others"]),
        "#",
        "# Analyzed by a panel of agents: an independent verifier reviewed this",
        "# change against the finding, and a second, fresh reviewer challenged the",
        "# diff for an attack path it opens, or a route it leaves open to the",
        "# finding's exploit. The patch was written only because the panel stated",
        "# all three of these with confidence:",
    ]
    lines += [
        f"#   - {claim.sentence}: {said.evidence or said.state}"
        for claim, said in unit["claims"].items()
    ]
    lines += ["#", f"# Please review this patch carefully: {plugin.AI_CAUTION}."]
    if unit["untested"]:
        lines += [
            "#",
            f"# NOTE: {UNTESTED_NOTICE}. The claim that",
            "# behaviour is unchanged rests on review of the change and its callers,",
            "# not on a test run -- weigh it accordingly before applying.",
        ]
    if unit["summary"]:
        lines += ["#", f"# Summary: {unit['summary']}"]
    if unit["tests_run"]:
        lines += [f"# Tests run: {unit['tests_run']}"]
    if check.pointer:
        limit = (f"# {line}" for line in textwrap.wrap(AFTER_APPLY))
        read = f"# Read {unit['id']}.md, beside this file."
        return "\n".join([*lines, "#", read, "#", *limit, "#", ""])
    lines += [
        "#",
        f"# Before you apply it, read {unit['id']}.md, beside this file.",
        *(f"# {line}" for line in textwrap.wrap(f"{AT_THE_TOP} {SKIPS}")),
        "#",
        *(f"# {line}" for line in textwrap.wrap(AFTER_APPLY)),
        "#",
        "",
    ]
    return "\n".join(lines)


def not_in_base_lines(files: list[str]) -> list[str]:
    """A note's paragraph on a unit's `not_in_base` files, with a blank line after it. Nothing
    where there are none."""
    names = ", ".join(span(percent(name, percent_sign=False)) for name in files)
    return [NOT_IN_BASE.format(names), ""] if names else []


NOTE_SAYS_WRITTEN = "**Status:** patch written"
NOTE_SAYS_NONE = "**Status:** no patch produced"


def note_written(
    unit: Unit, stats: list[DiffStat] | None, check: Checked, report_ref: str, report_full: str
) -> str:
    """The F<n>.md note for a finding that earned a patch. `report_ref` is the report's folder as
    report_path_from_root() gives it, and `report_full` its full path, with links followed."""
    lines = [
        f"# {unit['id']}: {unit['title']}",
        "",
        f"{NOTE_SAYS_WRITTEN} -> `{unit['id']}.patch`",
        "",
        *([f"**Note:** {OLDER}.", ""] if unit["older"] else []),
        *not_in_base_lines(unit["not_in_base"]),
        *([WRITTEN_FOR.format(unit["id"]), ""] if unit["others"] else []),
        *(["\n".join(f"- {item}" for item in unit["others"]), ""] if unit["others"] else []),
        (
            "**Analyzed by a panel of agents.** An independent verifier reviewed the "
            "change against the finding, and a second, fresh reviewer challenged the diff for an "
            "attack path it opens, or a route it leaves open to the finding's exploit. "
            "The patch was written only because the panel stated the three claims below with "
            f"confidence. Please review it carefully: {plugin.AI_CAUTION_LINK}. When this note "
            "was written, the run that wrote it had applied nothing."
        ),
        "",
    ]
    if unit["summary"]:
        lines += [f"**Summary:** {unit['summary']}", ""]
    lines += ["## Confidence", ""]
    lines += [
        f"- **{claim.sentence}** -- {said.state}: {said.evidence}"
        for claim, said in unit["claims"].items()
    ]
    if unit["untested"]:
        lines += [
            "",
            (
                f"**{UNTESTED_NOTICE[:1].upper()}{UNTESTED_NOTICE[1:]}.** The behaviour claim "
                "rests on review of the change and its callers, not on a test run."
            ),
        ]
    lines += ["", f"**Tests run:** {unit['tests_run'] or 'none recorded'}", ""]
    if (noted := unit["verifier_notes"]) is None:
        lines += [f"**Warning:** {NOTES_NOT_RECORDED}.", ""]
    elif noted:
        lines += [*(f"- **The verifier noted:** {said}" for said in noted), ""]
    if unit["recommendation"]:
        fix = code_span(apart(unit["recommendation"]))
        lines += [f"**The report's recommendation:** {fix}", "", PATCH_ALONE, ""]
        lines += [NOTES_MAY_MISS, ""]
    elif noted:
        lines += [NOTES_APART, ""]
    lines += ["## Change", ""]
    lines += diffstat_lines(stats)
    lines += ["", *attack_path_lines(unit), "## Applying it", ""]
    folder = report_ref
    if check.tried is Tried.APPLIES:
        lines.append(
            "Applies cleanly to the working tree (checked with `git apply --check`, and for a file "
            f"or a folder in the way of its paths). Before you apply it, {COPY_FIRST}. If "
            f"`git apply` fails all the same, for example at a read-only folder, {LEFT_HALFWAY} "
            f"{WAY_BACK}"
        )
    elif check.tried is Tried.NO_ANSWER:
        lines.append(
            "The clean-apply check gave no answer here (git found no repository that it could "
            "read, stopped before it read any patch, did not start or did not finish, or gave no "
            f"list of the patch's files); {COPY_FIRST} first, and try it yourself."
        )
    elif check.tried is Tried.BLOCKED and check.move:
        lines.append(
            f"Does not apply to the working tree as it is now. {check.why}. Move the file "
            f"{check.move} to {check.to} first, a name that is free. {KEEP_IT}. "
            f"If a folder stands at {check.move} now, skip this step. Before you apply the patch, "
            f"{COPY_FIRST}. If `git apply` fails halfway, {LEFT_HALFWAY} {WAY_BACK}"
        )
        lines += ["", "After the move:"]
    elif check.tried is Tried.BLOCKED:
        told = (
            f"{check.why[:1].upper()}{check.why[1:]}."
            if check.pointer
            else f"{check.why}. If `git apply` was run on this patch, {LEFT_HALFWAY} {WAY_BACK}"
        )
        step = MAKE_AGAIN if check.pointer else HANDS_OFF
        lines.append(f"{step[:1].upper()}{step[1:]}. {told}")
        if not check.pointer:
            lines[-1] += (
                " To decide, a person looks at each path in its way, in the working tree and in "
                f"the patch. {KEEP_THEM}."
            )
        folder = ""
    elif check.tried is Tried.REFUSED:
        detail = span(check.why) if check.why else plugin.APPLY_CONFLICTS
        lines.append(
            f"Does not apply cleanly to the working tree ({detail}). The patch was built "
            "against the recorded revision, so this usually means the working tree has "
            f"uncommitted or newer changes in these files. {BY_HAND[:1].upper()}{BY_HAND[1:]}. "
            "Or, to try the patch apart from your own changes, apply it in a new worktree at that "
            "revision, in a folder outside this repository (`git worktree add`). Do not copy files "
            "from that worktree over yours."
        )
        lines += ["", "In that worktree (the command holds the report folder's full path):"]
        folder = report_full
    else:
        unreachable(check.tried)
    lines.append("")
    if folder:
        lines += ["```", apply_command(f"{folder}/patches/{unit['id']}.patch"), "```", ""]
        lines += [
            ANY_FOLDER,
            "",
            f"If this note is in an `{EARLIER_PREFIX}<UTC time>` folder, its command {STILL_NAMES}",
            "",
        ]
        if check.tried is Tried.APPLIES or check.move:
            lines += ["Or ask Claude to apply it, or to open a pull request for it.", ""]
        lines += [AFTER_APPLY, ""]
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
        NOTE_SAYS_NONE,
        "",
        *([f"**Note:** {OLDER}.", ""] if unit["older"] else []),
        *not_in_base_lines(unit["not_in_base"]),
        *([wording[0], ""] if (wording := decline_wording(unit)) else []),
        quoted(unit["decline_reason"]),
        "",
    ]
    unsure = [
        f"- **{claim.sentence}** -- {said.state}: {said.evidence}"
        for claim, said in unit["claims"].items()
        if said.state != plugin.CONFIDENT
    ]
    if unsure:
        lines += ["## What could not be claimed with confidence", "", *unsure, ""]
    lines += attack_path_lines(unit)
    if stats is not None:
        lines += ["## What the rejected attempt changed", ""]
        lines += diffstat_lines(stats)
        lines.append("")
    if unit["recommendation"]:
        lines += ["## The report's original recommendation", "", quoted(unit["recommendation"]), ""]
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
            f"revision `{short}` and analyzed by a panel of agents. When this index was "
            "written, the run that wrote it had applied nothing, committed nothing, and "
            "opened no pull request."
        ),
        "",
        (
            f"Earlier runs' files, if any, are in `{EARLIER_PREFIX}<UTC time>` folders in "
            f"`patches/`. A command in such a file {STILL_NAMES}"
        ),
        "",
    ]
    if patched:
        request = f"Please review each one carefully: {plugin.AI_CAUTION_LINK}."
        lines += ["## Patches written", "", request, ""]
        for unit in patched:
            notices = (
                OLDER if unit["older"] else "",
                UNTESTED_NOTICE if unit["untested"] else "",
                MAY_BE_PART.format(unit["id"]) if may_be_part(unit) else "",
            )
            caveat = "".join(f" _({notice})_" for notice in notices if notice)
            if said := unit["check_said"]:
                caveat += f" _(the apply check {said}: read `{unit['id']}.md` first)_"
            lines.append(f"- **{unit['id']}** -- {unit['title']}: `{unit['id']}.patch`{caveat}")
        lines.append("")
    if declined:
        lines += ["## No patch produced", ""]
        for unit in declined:
            wording = decline_wording(unit)
            suffix = f" ({wording[1]})" if wording else ""
            older = f" _({OLDER})_" if unit["older"] else ""
            reason = " ".join(unit["decline_reason"].split())
            lines.append(f"- **{unit['id']}** -- {unit['title']}{suffix}{older}: {reason}")
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
        "Where a patch's `F<n>.md` gives this command, run it:",
        "",
        "```",
        apply_command(f"{report_ref}/patches/F<n>.patch"),
        "```",
        "",
        ANY_FOLDER,
        "",
        (
            "Each `F<n>.md` beside the patch explains the change and how it was analyzed. "
            "If you want a patch applied, or turned into a pull request, ask Claude."
        ),
        "",
        AFTER_APPLY,
        "",
    ]
    return "\n".join(lines)


def jsonl(
    units: list[Unit],
    base: str,
    stats_by_id: dict[str, list[DiffStat] | None],
    checks: dict[str, Checked],
) -> str:
    """patches.jsonl: one record per unit, machine-readable for tooling."""
    return "".join(
        strictjson.text({
            "provenance": plugin.PATCHES_PROVENANCE,
            "id": unit["id"],
            "status": unit["status"],
            "base": base,
            "patch": f"{unit['id']}.patch" if unit["status"] == "patch_written" else None,
            "note": f"{unit['id']}.md",
            "summary": unit["summary"] or None,
            "claims": {claim.key: said._asdict() for claim, said in unit["claims"].items()},
            "untested": unit["untested"],
            "tests_run": unit["tests_run"] or None,
            "verifier_notes": unit["verifier_notes"],
            "reviewed_paths": unit["reviewed_paths"],
            "attack_paths": unit["attack_paths"],
            "no_report": unit["no_report"],
            "attempts": unit["attempts"],
            "confirmed": unit["confirmed"],
            "diffstat": stats_by_id.get(unit["id"]),
            "apply_check": checks[unit["id"]].recorded if unit["id"] in checks else None,
            "decline_reason": unit["decline_reason"] or None,
        })
        + "\n"
        for unit in units
    )


# The job's instructions and patch-spec.md name these folders by this prefix.
EARLIER_PREFIX = "earlier-"
EARLIER_TIME = "%Y%m%d-%H%M%S-%f"
EARLIER_GLOB = EARLIER_PREFIX + "-".join("[0-9]" * digits for digits in (8, 6, 6))
REASON_CHARS = 300

STILL_NAMES = (
    "still names `patches/` itself: a newer patch, or none. Add that folder's name after "
    "`patches/`."
)
APPLY = 'git -C "$(git rev-parse --show-toplevel)" apply'
SKIPS = (
    "Plain `git apply`, run in a folder below the repository's top, skips each file of the patch "
    "that is outside that folder, says nothing, and exits with 0."
)
AT_THE_TOP = "If you apply it, do so at the repository's top."
ANY_FOLDER = (
    "This command first goes to the top folder of the repository or worktree that you are in, so "
    f"you can run it in any of its folders. Do not shorten it. {SKIPS} In a shell that does not "
    "know `$(...)`, such as cmd.exe, put the path that `git rev-parse --show-toplevel` prints in "
    "its place, and type the patch file's path in double quotes."
)


def apply_command(patch: str) -> str:
    """The command that applies the patch file at `patch`, a full path or one from the repository's
    top, for a user to paste."""
    return f"{APPLY} {shlex.quote(patch)}"


def has_product_name(path: PurePath) -> bool:
    """Whether a path has a name that the render writes."""
    named = path.suffix in {".patch", ".md"} and FINDING_ID_RE.match(path.stem) is not None
    return named or path.name in {plugin.PATCHES_INDEX_NAME, plugin.PATCHES_JSONL_NAME}


def is_patch_product(path: Path) -> bool:
    """Whether a path in the patches folder is a file with a name that the render writes."""
    return has_product_name(path) and path.is_file()


def index_last(path: Path) -> tuple[bool, str]:
    """The order of a delivery: each note before its patch, then patches.jsonl, then the index."""
    return path.name == plugin.PATCHES_INDEX_NAME, path.name


def move_earlier_products(patches_dir: Path) -> None:
    """Move what an earlier run wrote into a new folder in `patches_dir`, and print its path.

    Only the script's own product names move, with their bytes as they are; every other
    file in the folder stays. With none to move, it makes no folder and prints nothing.
    """
    earlier = sorted(filter(is_patch_product, patches_dir.iterdir()), key=index_last, reverse=True)
    if not earlier:
        return
    folder = patches_dir / datetime.now(timezone.utc).strftime(EARLIER_PREFIX + EARLIER_TIME)
    print(f"moving the earlier patches, notes and index to {folder}", flush=True)
    folder.mkdir()
    for path in earlier:
        path.rename(folder / path.name)


def sweep_leftovers(patches_dir: Path) -> list[str]:
    """Remove the temporary files of atomic.write() for a product from the patches folder. Every
    other file there is left alone. Returns a warning for each that will not go."""
    warnings: list[str] = []
    for path in sorted(patches_dir.glob(f"*{atomic.SUFFIX}")):
        product = PurePath(path.name.removesuffix(atomic.SUFFIX))
        if has_product_name(product) and not os.path.isdir(path):
            try:
                path.unlink()
            except OSError as error:
                warnings.append(f"could not remove a leftover: {error}")
    return warnings


def newest_earlier(patches_dir: Path, name: str) -> Path | None:
    """The product `name` in the newest earlier- folder that holds it, of those named as
    move_earlier_products() names them, or None."""
    held = filter(is_patch_product, patches_dir.glob(f"{EARLIER_GLOB}/{name}"))
    return max(held, default=None)


def newest_word(patches_dir: Path, unit_id: str) -> str:
    """Where a finding's newest note is, and what the run that wrote it says of the finding in the
    patches.jsonl beside that note, as sentences on one line that open with a space. With no
    readable row there that has a status of the script's own, and that the note's status line agrees
    with on whether a patch was written, it sends the reader to the note. It is "" with no note."""
    note = patches_dir / f"{unit_id}.md"
    found = note if is_patch_product(note) else newest_earlier(patches_dir, note.name)
    if not found:
        return ""
    newest = (
        f" {unit_id}'s newest note is {found.relative_to(patches_dir).as_posix()} of patches_dir."
    )
    try:
        rows = products.records(found.parent / plugin.PATCHES_JSONL_NAME, required=False)
        lines = found.read_text("utf-8", "surrogateescape").splitlines()
    except (OSError, products.ProductError):
        rows, lines = [], []
    row = next((r for r in rows if r["id"] == unit_id and r.get("status") in STATUSES), None)
    written = row is not None and row["status"] == "patch_written"
    said = NOTE_SAYS_WRITTEN if written else NOTE_SAYS_NONE
    if row is None or not any(line.startswith(said) for line in lines):
        return (
            f"{newest} No readable record that agrees with it lies beside it: read that note for "
            f"{unit_id}'s status."
        )
    word = f"{newest} The run that wrote it gave {unit_id} the status {row['status']}."
    if written:
        return word
    reason = display.single_line(strictjson.clean(row.get("decline_reason")))
    escaped = reason.replace("\\", "\\\\").replace('"', '\\"')
    cut = display.capped(display.written_out(escaped), REASON_CHARS)
    why = f' Its reason (that note has it whole): "{cut}".' if reason else ""
    return f"{word} That run wrote no patch for {unit_id}.{why}"


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
    atomic.write(path, b"*\n")
    return "written"


def report_path_from_root(report_dir: Path, top: str | None) -> str:
    """The report directory as a path from the repository root, for the apply command.

    Falls back to the folder's full path when it sits outside the root, or git cannot name a root.
    """
    real = os.path.realpath(report_dir)
    below = None if top is None else absolute.relative(real, os.path.realpath(top))
    if below is None:
        return Path(real).as_posix()
    return f"./{below}" if below.startswith("-") else below


def refuse_analysis(report_dir: Path) -> None:
    """Raise PatchError where the report directory is an attack surface analysis's."""
    if plugin.holds_analysis(report_dir):
        msg = f"{report_dir.name!r} {ANALYSIS_REFUSAL}"
        raise PatchError(msg)


def refuse_line_break(report_dir: Path) -> None:
    """Raise PatchError where the report directory's resolved path holds a line break."""
    # A line break in this path would split the fenced `git apply` command in the notes.
    path = os.path.realpath(report_dir)
    if "\n" in path or "\r" in path:
        msg = (
            "a directory on the path to the report directory has a line break in its name, so no "
            "patch is written for this report. The user must rename that directory. The path, with "
            f"links followed, is {path!r}"
        )
        raise PatchError(msg)


def resolve_report_dir(patches_dir: Path) -> Path:
    """The report directory holding `patches_dir`, validated by name. An attack surface analysis's
    directory is refused, and so is one whose resolved path holds a line break."""
    # abspath folds ".." without following symlinks, so the name checks see this path's own names.
    patches_abs = Path(os.path.abspath(patches_dir))
    report_dir = patches_abs.parent
    refuse_analysis(report_dir)
    if patches_abs.name != plugin.PATCHES_DIR_NAME:
        msg = (
            f"patches dir must be a directory named {plugin.PATCHES_DIR_NAME!r} inside the "
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
    refuse_line_break(report_dir)
    return report_dir


def report_findings(report_dir: Path, scan_prefix: str) -> dict[str, ReportFinding]:
    """The report's findings by id, in report order, each `file` decoded and made relative to the
    repository."""
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
        where = f"{name} line {number}"
        lists = {key: listed_in(record, key) for key in ("also_at", "also_filed_at")}
        for key, entries in lists.items():
            if entries is None:
                msg = f"{where}: {finding_id} {key} is not a list of objects"
                raise PatchError(msg)
        file = checked_repository_file(
            record.get("file"), scan_prefix, where=where, whose=finding_id
        )
        listed = {
            key: [
                {
                    **entry,
                    "file": checked_repository_file(
                        entry.get("file"), scan_prefix, where=where, whose=f"{finding_id} {key}"
                    ),
                }
                for entry in entries
            ]
            for key, entries in lists.items()
            if entries
        }
        # Called for its refusal alone.
        try:
            products.is_credential_record(record)
        except products.ProductError as error:
            msg = f"{where}: {finding_id} could not be read as a finding record ({error}); "
            raise PatchError(msg + "run the scan again") from error
        finding = {**record, "file": file, **listed}
        findings[finding_id] = ReportFinding(Severity[severity], finding)
    return findings


IDS_SHOWN = 5
WRITTEN_FOR = "This patch was written for {} alone. It may leave the report's other findings open:"
OWN_PATCH = "a patch of their own, in this folder"
LISTED_UNDER = "listed under a finding as the same flaw, with no patch of their own"
NO_PATCH_HERE = (
    "the report holds other findings with no patch here; each patch's note names or counts them"
)
TRIAGE_REST = f"any other finding of the triage: see {plugin.TRIAGE_MD_NAME}"
MAYBE_MORE = "there may be others: the report was unreadable or empty when this patch was written"


def findings_if_read(report_dir: Path) -> dict[str, ReportFinding]:
    """What report_findings() gives. Empty, with a warning, where the report or its stamp cannot be
    read, or the report lists no finding."""
    why = "it lists no finding"
    try:
        if findings := report_findings(report_dir, products.Stamp.read(report_dir).prefix):
            return findings
    except (PatchError, products.ProductError, OSError) as error:
        why = str(error)
    console.warn(f"the report was unreadable or empty, so the notes may omit findings: {why}")
    return {}


def other_findings(
    unit_id: str, report: dict[str, ReportFinding], *, fixed: set[str], taken: set[str]
) -> list[str]:
    """What became of the findings other than `unit_id`: a line for each kind that has a finding,
    with its ids, or their count where they are more than IDS_SHOWN. `taken` holds the ids of this
    run's units, and `fixed` those with a patch. Where `report` is empty, a last line says that
    there may be others. Empty where there is nothing to say."""
    named = (e.get("id") for one in report.values() for e in listed_in(one.record) or [])
    listed = {i for i in named if is_str(i) and FINDING_ID_RE.match(i)} - report.keys()
    kinds = (
        (OWN_PATCH, fixed, plugin.PATCHES_INDEX_NAME),
        ("taken up in this run, with no patch", taken - fixed, plugin.PATCHES_INDEX_NAME),
        ("no result from this run", report.keys() - taken, "the report"),
        (LISTED_UNDER, listed, "the report"),
    )
    return [
        f"{what}: "
        + (", ".join(ids) if len(ids) <= IDS_SHOWN else f"{len(ids)} findings, see {where}")
        for what, found, where in kinds
        if (ids := sorted(found - {unit_id}, key=finding_number))
    ] + ([] if report else [MAYBE_MORE])


def checked_repository_file(declared: object, scan_prefix: str, *, where: str, whose: str) -> str:
    """A JSONL `file`, percent-decoded when it is in the form the JSONL writes, spelled from the
    repository's top level; one not below it is refused."""
    written = unpercent(field(declared, f"{whose} file"))
    file = repository_file(scan_prefix, file=written)
    if not written or written.startswith("/") or not absolute.below_top(file):
        msg = f"{where}: {whose} file {written!r} is not a repository path"
        raise PatchError(msg)
    return file


def select_units(findings: dict[str, ReportFinding], selection: str) -> list[str]:
    """The ids that `selection` takes -- `all`, `high`, or ids like `F1,F3` -- in report order.
    PatchError when an id is malformed or not in the report, or when the selection takes nothing."""
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


def refuse_place(folder: str) -> None:
    """PatchError with lib/place.py's refusal()'s words where it refuses `folder`, in which git is
    to run."""
    if reason := refusal(folder):
        raise PatchError(reason)


def refuse_outside(folder: Path, *, same_git: bool) -> None:
    """PatchError with lib/place.py's outside()'s words where it refuses `folder`."""
    if reason := outside(str(folder), same_git=same_git):
        raise PatchError(reason)


def probe_answer(repo_root: str, stamp: products.Stamp) -> JsonMap:
    """The answer that the GitHub Action's probe left in the repository's .git folder, where it is
    for the range that `stamp` records; empty where there is none, where it is for another range,
    and, with a warning, where it cannot be read."""
    probe = Path(repo_root, ".git", plugin.PROBE_NAME)
    try:
        answer = strictjson.as_map(strictjson.load(probe))
    except (FileNotFoundError, NotADirectoryError):
        return {}
    except (OSError, ValueError) as error:
        console.warn(f"could not read {probe}, so no finding is left out: {error}")
        return {}
    pull_request = strictjson.as_map(answer.get("pull_request"))
    base, head = (strictjson.clean(pull_request.get(key)) for key in ("merge_base", "head"))
    return answer if base and (base, head) == (stamp.merge_base, stamp.commit) else {}


def offered_earlier(findings: dict[str, ReportFinding], answer: JsonMap) -> set[str]:
    """The ids of the findings of the change, each with a key of its own, whose fix an earlier
    comment on the pull request offers for the finding's line at this run's grade
    (marker.still_answers), by `answer`, the probe's. marker.Earlier.answering says which comment
    can offer it."""
    offered = {
        marker.FindingLine.of(one): marker.grade_named(one)
        for one in strictjson.maps(answer.get("previous_findings"))
        if one.get("fix_offered") is True
    }
    keys = {
        i: key
        for i, finding in findings.items()
        if "older_than_the_change" not in finding.record
        and (key := strictjson.clean(finding.record.get(FINDING_ID)))
    }
    counts = Counter(keys.values())
    return {
        i
        for i, key in keys.items()
        if counts[key] == 1
        and (place := marker.FindingLine.of(findings[i].record)) in offered
        and (graded := marker.grade_named(findings[i].record))
        and marker.still_answers(marker.Tag.FIX, offered[place], marker.Tag.FIX, graded)
    }


def resolved_base(repo_root: str, base: str) -> str:
    """The full id of the commit `base` names in the repository whose top level is `repo_root`;
    PatchError when refuse_place() refuses `repo_root`, when it is not a top level, or when `base`
    resolves to no commit there."""
    refuse_place(repo_root)
    top = git.toplevel(repo_root)
    if top is None or not Path(repo_root).samefile(git.for_disk(top)):
        msg = f"--repo-root {repo_root!r} is not the top level of a repository"
        raise PatchError(msg)
    commit = git.commit_id(repo_root, base)
    if commit is None:
        msg = f"--base {base}: git cannot resolve it to a commit in {repo_root}"
        raise PatchError(msg)
    return commit


STOP_JOB = (
    "If the user asked to apply a patch, stop this job now: it only writes new patches, and "
    "applies none."
)
APPLY_INSTEAD = (
    f"{STOP_JOB} Read the note beside the patch that they named, and apply that patch only "
    "as its note allows."
)
ASK_FIRST = (
    f"{STOP_JOB} Follow the recipe's paragraph that opens \"Where the user asks you to apply a "
    "patch\": name the patch's folder to them, give its finding's newest status and the newest "
    "note's reason for no patch, if it has one (copy its first block quote word for word, each "
    "line with its `>`, and add no quotation marks), mark no option as recommended, and ask before "
    "you apply it, which you do only as the note beside it allows."
)


def prepare(report_dir: Path, *, selection: str, repo_root: str, base: str) -> int:
    """Lay out a patch run for the selected findings; print its directories and its unit ids.

    First leave out, and name, the findings whose fix an earlier comment on the pull request still
    offers, for the finding's line and at the grade that this run gives it, unless findings share
    its id (offered_earlier() on probe_answer()). Where none is left, print an empty list of ids,
    make nothing and stop there.

    Then print one line for the units' patches that are already in the patches folder, if any. For
    each whose patch lies in earlier- folders alone, print a line that names it in the newest folder
    that holds it, with where that finding's newest note is and what its run says of the finding, if
    any. The line for the patches already there, and the last of the others, end in words that tell
    a session whose user asked to apply a patch to stop the job."""
    report_dir = Path(os.path.abspath(report_dir))
    if not plugin.REPORT_DIR_RE.match(report_dir.name):
        msg = f"{report_dir.name!r} is not a CLAUDE-SECURITY-<timestamp> report directory"
        raise PatchError(msg)
    refuse_analysis(report_dir)
    refuse_line_break(report_dir)
    refuse_outside(report_dir, same_git=False)
    resolved_base(repo_root, base)
    stamp = products.Stamp.read(report_dir)
    findings = report_findings(report_dir, stamp.prefix)
    ids = select_units(findings, selection)
    offered = offered_earlier(findings, probe_answer(repo_root, stamp))
    if left_out := [i for i in ids if i in offered]:
        said = ", ".join(left_out)
        print(f"left out, as an earlier comment on the pull request still offers the fix: {said}")
        ids = [i for i in ids if i not in offered]
    if not ids:
        print("units: []")
        return 0
    started = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    patch_dir = report_dir / plugin.RUN_DIR_NAME / f"{PATCH_DIR_PREFIX}{started}"
    try:
        patch_dir.mkdir(parents=True)
    except FileExistsError as error:
        msg = f"{patch_dir} already exists (a run prepared this same second); run this again"
        raise PatchError(msg) from error
    findings_dir = patch_dir / FINDINGS_DIR_NAME
    findings_dir.mkdir()
    patches_dir = report_dir / plugin.PATCHES_DIR_NAME
    patches_dir.mkdir(exist_ok=True)
    for unit_id in ids:
        text = strictjson.text(findings[unit_id].record, indent=2) + "\n"
        (findings_dir / f"{unit_id}.json").write_bytes(text.encode())
    print(f"patch_dir: {patch_dir}")
    print(f"patches_dir: {patches_dir}")
    print(f"units: {strictjson.text(ids)}")
    on_disk = [p.name for i in ids if is_patch_product(p := patches_dir / f"{i}.patch")]
    if on_disk:
        print(f"already in patches_dir: {', '.join(on_disk)}. {APPLY_INSTEAD}")
    found = (newest_earlier(patches_dir, f"{i}.patch") for i in ids)
    moved = [
        f"only in an earlier folder of patches_dir: {p.relative_to(patches_dir).as_posix()}."
        f"{newest_word(patches_dir, p.stem)}"
        for p in found
        if p and p.name not in on_disk
    ]
    if moved:
        print("\n".join(moved), ASK_FIRST)
    return 0


def render(patch_dir: Path, patches_dir: Path, scan_root: str, base: str) -> int:
    report_dir = resolve_report_dir(patches_dir)
    refuse_place(scan_root)
    top = git.toplevel(scan_root)
    top = None if top is None else git.for_disk(top)
    # The record names the base in git's full spelling where git resolves it, else as given.
    if top is not None:
        resolved = git.commit_id(top, base)
        if resolved is None:
            console.warn(f"base {base} does not resolve to a commit here; recorded as given")
        base = resolved or base
    units = load_units(patch_dir, top, base)
    from_root = report_path_from_root(report_dir, top)
    report_ref = git.from_disk(from_root)
    report_full = git.from_disk(Path(os.path.realpath(report_dir)).as_posix())
    fixed = {unit["id"] for unit in units if unit["status"] == "patch_written"}
    taken = {unit["id"] for unit in units}
    for unit in (unit for unit in units if unit["id"] in fixed):
        # Called for its refusal alone.
        read_diff(patch_dir, unit["id"], required=True)
    report = findings_if_read(report_dir) if fixed else {}
    for unit in (unit for unit in units if unit["id"] in fixed):
        unit["others"] = other_findings(unit["id"], report, fixed=fixed, taken=taken)
    unpatched = any(not said.startswith(OWN_PATCH) for unit in units for said in unit["others"])
    pass_on = f"{NO_PATCH_HERE}: tell the user so\n" if report and unpatched else ""
    if named := [unit["id"] for unit in units if may_be_part(unit)]:
        pass_on = f"{NOTES_RELAY.format(', '.join(named))}\n{pass_on}"
    if (report_dir / plugin.TRIAGE_MD_NAME).is_file():
        for unit in (unit for unit in units if unit["id"] in fixed):
            unit["others"].append(TRIAGE_REST)
    stats_by_id: dict[str, list[DiffStat] | None] = {}
    checks: dict[str, Checked] = {}
    products_dir = patch_dir / datetime.now(timezone.utc).strftime("products-%H%M%S-%f")
    products_dir.mkdir()
    if products_dir.stat().st_dev != patches_dir.stat().st_dev:
        msg = (
            f"'{patch_dir}' and '{patches_dir}' are on two file systems, so no file can be renamed "
            "from one into the other; no file is written or moved"
        )
        raise PatchError(msg)

    def write_new(name: str, data: bytes) -> None:
        atomic.write(products_dir / name, data, like=patches_dir / name)

    unit_lines: list[str] = []
    for unit in units:
        written = unit["status"] == "patch_written"
        diff = read_diff(patch_dir, unit["id"], required=written)
        stats = numstat(diff) if diff is not None else None
        stats_by_id[unit["id"]] = stats
        notice = f"; {OLDER}: tell the user so" if unit["older"] else ""
        if written and diff is not None:
            patch_path = patches_dir / f"{unit['id']}.patch"
            unchecked = NO_WARNING_YET + header_comment(unit, base, Checked(Tried.NO_ANSWER))
            check = apply_check(
                top, unchecked.encode("utf-8", "surrogateescape") + diff, patch_path
            )
            checks[unit["id"]] = check
            unit["check_said"] = check.listed
            note = note_written(unit, stats, check, report_ref, report_full)
            header = header_comment(unit, base, check)
            body = re.sub(rb"(?m)^(?!\Z)", b"# ", diff) if check.pointer else diff
            patch = header.encode("utf-8", "surrogateescape") + body
            write_new(patch_path.name, patch)
            said = [f"patch written -> {patch_path} (apply check: {check.recorded}){notice}"]
            if check.step:
                said.append(f"for the user: {check.step}")
            if check.missing:
                said.append(f"{check.missing}; the apply check suggests no file to move")
        else:
            note = note_declined(unit, stats)
            said = [f"no patch ({unit['status']}) -> {unit['id']}.md{notice}"]
        write_new(f"{unit['id']}.md", note.encode("utf-8", "surrogateescape"))
        unit_lines += [f"{unit['id']}: {line}" for line in said]
    index = index_markdown(units, base, report_dir.name, report_ref)
    write_new(plugin.PATCHES_INDEX_NAME, index.encode("utf-8", "surrogateescape"))
    records = jsonl(units, base, stats_by_id, checks)
    write_new(plugin.PATCHES_JSONL_NAME, records.encode())
    move_earlier_products(patches_dir)
    for new in sorted(products_dir.iterdir(), key=index_last):
        new.replace(patches_dir / new.name)
    print("\n".join(unit_lines))
    sweep_warnings = sweep_leftovers(patches_dir)
    swept, warnings = remove_workspaces_in(patch_dir)
    for name in swept:
        print(f"removed workspace {name}")
    removed, more_warnings = remove_patch_run(patch_dir)
    for path in removed:
        print(f"removed {path}")
    for warning in sweep_warnings + warnings + more_warnings:
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
        f"{pass_on}"
        f"wrote PATCHES.md and patches.jsonl into {patches_dir} "
        f"({patched} patched, {len(units) - patched} declined)"
    )
    return 0


def misplaced_reason(leaf: Path) -> str | None:
    """Why `leaf` is not where a scratch workspace lives, or None when it is:
    `<report>/.claude-security-run/patch-<ts>/scratch-F<n>`, none of the three
    directories above it a symbolic link, and the report no analysis's."""
    if not SCRATCH_NAME_RE.match(leaf.name):
        return "its name is not scratch-F<n>"
    return misplaced_patch_run_reason(leaf.parent)


def misplaced_patch_run_reason(patch_dir: Path) -> str | None:
    """Why `patch_dir` is not where a patch run lives, or None when it is:
    `<report>/.claude-security-run/patch-<ts>`, none of the three a symbolic link, and the report
    no analysis's."""
    run_dir = patch_dir.parent
    report_dir = run_dir.parent
    if not PATCH_DIR_RE.match(patch_dir.name):
        return f"'{patch_dir.name}' is not named patch-<timestamp>"
    if run_dir.name != plugin.RUN_DIR_NAME:
        return f"'{patch_dir.name}' is not inside {plugin.RUN_DIR_NAME}/"
    if not plugin.REPORT_DIR_RE.match(report_dir.name):
        return f"'{report_dir.name}' is not a CLAUDE-SECURITY-<timestamp> report directory"
    if plugin.holds_analysis(report_dir):
        return f"'{report_dir.name}' {ANALYSIS_REFUSAL}"
    for directory in (patch_dir, run_dir, report_dir):
        if is_link(directory):
            return f"'{directory}' is a symbolic link"
    return None


def refuse_reason(path: Path) -> str | None:
    """Why `path` may NOT be tended or deleted as a scratch workspace, or None when it may.

    Only `<report>/.claude-security-run/patch-<ts>/scratch-F<n>` holding its
    own `.git` qualifies; every other shape is refused.
    """
    leaf = Path(os.path.abspath(path))
    if is_link(leaf):
        return "it is a symbolic link"
    if not os.path.isdir(leaf):
        return "it is not a directory"
    if reason := misplaced_reason(leaf):
        return reason
    dot_git = leaf / ".git"
    if is_link(dot_git) or not os.path.isdir(dot_git):
        return "it holds no .git directory of its own"
    return None


class Workspace(NamedTuple):
    """A scratch workspace that passed the fence, and the commit it was opened at."""

    path: Path
    base: str

    @classmethod
    def at(cls, path: str) -> Workspace:
        """The scratch workspace at `path`; PatchError for anything refuse_reason names, for a
        workspace that refuse_outside() refuses, for a `.git` that is no repository of its own, and
        for a base ref that gives no commit."""
        reason = refuse_reason(Path(path))
        if reason is not None:
            msg = f"'{path}' is not a scratch workspace: {reason}"
            raise PatchError(msg)
        leaf = Path(os.path.abspath(path))
        refuse_outside(leaf, same_git=True)
        top = None if in_git_directory(str(leaf)) else git.toplevel(str(leaf))
        if top is None or not leaf.samefile(git.for_disk(top)):
            msg = f"'{path}' is not a scratch workspace: its .git is not a repository of its own"
            raise PatchError(msg)
        base = git.commit_id(str(leaf), BASE_REF)
        if base is None:
            msg = f"'{path}' is not a scratch workspace: git finds no commit at its base ref"
            raise PatchError(msg)
        return cls(leaf, base)


def scratch_git(cwd: Path | str, *args: str) -> bytes:
    """One git call in `cwd` under lib/git.py's environment, PATHSPEC_VARIABLES off, with the folder
    above `cwd` as a ceiling on git's search for a repository unless that folder's path holds
    os.pathsep: its stdout, or PatchError with git's own first line of complaint."""
    above = str(Path(os.path.abspath(cwd)).parent)
    ours = [] if os.pathsep in above else [above]
    ceilings = os.pathsep.join([*ours, git.ENV.get("GIT_CEILING_DIRECTORIES", "")])
    try:
        out = subprocess.run(
            [*git.GIT, "-C", str(cwd), *args],
            # On in the user's shell, some of these would change how git reads NOT_PYTHON_CACHES.
            env=git.ENV
            | dict.fromkeys(PATHSPEC_VARIABLES, "0")
            | {"GIT_CEILING_DIRECTORIES": ceilings},
            capture_output=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        msg = f"git {args[0]} could not run: {error}"
        raise PatchError(msg) from error
    if out.returncode != 0:
        said = out.stderr.decode("utf-8", "replace").strip().splitlines()
        msg = f"git {args[0]} failed" + (f": {said[0]}" if said else f" (exit {out.returncode})")
        raise PatchError(msg)
    return out.stdout


def refuse_incomplete_checkout(leaf: Path, *, repo_root: str, base: str) -> None:
    """PatchError when `leaf` lacks tracked files that --stage would stage as deleted."""
    listed = scratch_git(leaf, "diff-files", "--name-only", "--diff-filter=D", "-z").decode(
        "utf-8", "surrogateescape"
    )
    if absent := listed.split("\0")[:-1]:
        msg = (
            f"--base {base}: git could not check out {len(absent)} of its files (the first is "
            f"{absent[0]!r}); if '{repo_root}' is a partial clone, it has yet to fetch them"
        )
        raise PatchError(msg)


def open_scratch(path: str, *, repo_root: str, base: str) -> int:
    """Make one unit's scratch workspace: a shared clone of the repository, its hooks off,
    checked out detached at `base`; print its path."""
    leaf = Path(os.path.abspath(path))
    if reason := misplaced_reason(leaf):
        msg = f"'{path}' is not where a scratch workspace goes: {reason}"
        raise PatchError(msg)
    if not leaf.parent.is_dir():
        msg = f"'{leaf.parent}' is not a patch run directory (--prepare makes one)"
        raise PatchError(msg)
    if os.path.lexists(leaf):
        msg = f"'{path}' already exists"
        raise PatchError(msg)
    refuse_outside(leaf.parents[2], same_git=False)
    commit = resolved_base(repo_root, base)
    top = os.path.realpath(repo_root)
    hooks_off = "core.hooksPath=/dev/null"
    try:
        scratch_git(
            top, "clone", "--shared", "--no-checkout", "--quiet", "-c", hooks_off, top, str(leaf)
        )
        scratch_git(leaf, "checkout", "--detach", "--quiet", commit)
        refuse_incomplete_checkout(leaf, repo_root=repo_root, base=base)
        scratch_git(leaf, "--git-dir=.git", "update-ref", BASE_REF, commit)
    except PatchError as error:
        try:
            removal.remove_tree(leaf)
        except OSError as residue:
            detail = console.removal_failure_detail(residue)
            msg = f"{error}; and '{leaf}' could not be removed: {detail}"
            raise PatchError(msg) from error
        raise
    print(f"scratch: {leaf}")
    return 0


def notes_file(leaf: Path) -> Path:
    """The path of `F<n>.notes` for the unit whose workspace is `leaf`: beside the workspace."""
    return leaf.parent / f"{leaf.name.removeprefix(SCRATCH_PREFIX)}{NOTES_SUFFIX}"


def stage(path: str) -> int:
    """Stage everything the workspace holds that differs from its base, except what git ignores and
    untracked .pyc files directly in a __pycache__ folder, and remove the unit's `F<n>.notes`
    beside the workspace; print how many paths."""
    leaf, base = Workspace.at(path)
    notes_file(leaf).unlink(missing_ok=True)
    # git before 2.13 refuses an exclusion that stands alone, so "." comes first.
    scratch_git(leaf, "add", "-A", "--", ".", NOT_PYTHON_CACHES)
    scratch_git(leaf, "add", "-u")
    count = scratch_git(leaf, "diff", "--cached", "--name-only", "-z", base, *PINNED_DIFF).count(
        b"\0"
    )
    print(f"staged: {count} path{'' if count == 1 else 's'}")
    return 0


def clean_scratch(path: str) -> int:
    """Remove the workspace's untracked files, leaving what is staged, what git ignores and any
    untracked directory that is a repository of its own; print the workspace's path."""
    leaf = Workspace.at(path).path
    scratch_git(leaf, *CLEAN_UNTRACKED)
    print(f"cleaned: {leaf}")
    return 0


def prepared_recommendation(leaf: Path) -> str:
    """report_fix() of the prepared finding of the workspace `leaf`'s unit, with no mask.
    Empty where the prepared finding gives none. Refuses a prepared finding that is
    missing or is no JSON object, as the render does."""
    unit_id = leaf.name.removeprefix(SCRATCH_PREFIX)
    path = leaf.parent / FINDINGS_DIR_NAME / f"{unit_id}.json"
    if not path.is_file():
        msg = f"{FINDINGS_DIR_NAME}/{path.name} is missing: --prepare laid out no finding {unit_id}"
        raise PatchError(msg + "; say so in what you hand back")
    try:
        record = strictjson.load(path)
        if not is_map(record):
            msg = "it is not an object"
            raise ValueError(msg)
    except ValueError as error:
        msg = f"{FINDINGS_DIR_NAME}/{path.name} could not be read as a finding record ({error}); "
        raise PatchError(msg + "run --prepare again") from error
    return report_fix(record, unit_id, ("", ""))


def show_staged(path: str) -> int:
    """Print the report's recommendation for the unit's finding, and what the workspace holds for
    review against its base: its status, the staged paths with their change letters, and the staged
    diff, external diff and textconv drivers off."""
    leaf, base = Workspace.at(path)
    sections = {
        "recommendation": (prepared_recommendation(leaf) or NO_RECOMMENDATION).encode("utf-8"),
        "status": scratch_git(
            leaf, "-c", "status.renames=true", "status", "--porcelain", "--untracked-files=normal"
        ),
        "paths": scratch_git(leaf, "diff", "--cached", "--name-status", base, *PINNED_DIFF),
        "diff": scratch_git(leaf, "diff", "--cached", base, *PINNED_DIFF),
    }
    out = sys.stdout.buffer
    for title, body in sections.items():
        end = b"" if not body or body.endswith(b"\n") else b"\n"
        out.write(f"## {title}\n".encode() + body + end)
    out.flush()
    return 0


def keep_notes(path: str) -> int:
    """Write standard input, a verifier's notes, to the unit's `F<n>.notes` beside the workspace,
    in place of any earlier file; print that path. For an attempt's first notes, where the report
    gives a recommendation, print it and LOOK_AGAIN too. Refuses an input with nothing but white
    space, and a prepared finding that --staged refuses."""
    leaf = Workspace.at(path).path
    target = notes_file(leaf)
    fix = prepared_recommendation(leaf)
    first = not target.exists()
    notes = sys.stdin.buffer.read() if sys.stdin else b""
    if not notes.strip():
        raise PatchError(NO_NOTES_GIVEN)
    atomic.write(target, notes)
    print(f"notes: {target}")
    if first and fix:
        sys.stdout.flush()
        look = f"## recommendation\n{fix}\n## check\n{LOOK_AGAIN}\n"
        sys.stdout.buffer.write(look.encode("utf-8"))
    return 0


def write_diff(path: str) -> int:
    """Write the workspace's staged diff against its base, restaging nothing, to `F<n>.diff`
    beside it in the patch run directory; print that path and each path git reads back from
    the file."""
    leaf, base = Workspace.at(path)
    target = leaf.parent / f"{leaf.name.removeprefix(SCRATCH_PREFIX)}.diff"
    prefixes = ("--src-prefix=a/", "--dst-prefix=b/")
    diff = scratch_git(leaf, "diff", "--cached", "--binary", *prefixes, base, *PINNED_DIFF)
    target.unlink(missing_ok=True)
    if not diff.strip():
        print("diff: none")
        return 0
    target.write_bytes(diff)
    listed = scratch_git(leaf, "apply", "--numstat", str(target))
    print(f"diff: {target}")
    for applied in numstat_paths(listed):
        print(f"path: {applied}")
    return 0


def numstat_paths(listed: bytes) -> list[str]:
    """The paths `git apply --numstat` named, one per file the patch touches (a rename's new
    name), spelt as git prints them: an unusual name quoted, as `--name-status` quotes it."""
    # git ends each line with "\n" alone. splitlines() would also cut at a U+2028 in a name.
    lines = listed.decode("utf-8", "surrogateescape").split("\n")
    return [line.split("\t", 2)[2] for line in lines if line.count("\t") >= 2]


def reset_scratch(path: str) -> int:
    """Return the workspace to the base it was opened at: commits, staged and unstaged changes
    dropped, untracked files removed as --clean-scratch removes them; print its path."""
    leaf = Workspace.at(path).path
    scratch_git(leaf, "reset", "--hard", "--quiet", BASE_REF)
    scratch_git(leaf, *CLEAN_UNTRACKED)
    print(f"reset: {leaf}")
    return 0


def remove_workspace(path: Path) -> None:
    """Delete one scratch workspace, refusing anything off the fenced layout."""
    reason = refuse_reason(path)
    if reason is not None:
        msg = f"refusing to remove '{path}': {reason}"
        raise PatchError(msg)
    try:
        removal.remove_tree(path)
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
        if not path.name.startswith(SCRATCH_PREFIX):
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
    try:
        removal.remove_tree(target)
    except OSError as error:
        detail = console.removal_failure_detail(error)
        return [], [f"could not remove '{patch_dir}': {detail}"]
    try:
        run_dir.rmdir()
    except OSError:
        return [target], []
    return [target, run_dir], []


def remove_scratch(path: str) -> int:
    """Delete the workspace; print that it is gone."""
    remove_workspace(Path(path))
    print(f"removed workspace {path!r}")
    return 0


WORKSPACE_HELP = "<report>/.claude-security-run/patch-<ts>/scratch-F<n>"
WORKSPACE_FORMS: dict[str, tuple[str, Callable[[str], int]]] = {
    "--stage": (
        (
            "Stage a workspace's changes, except ignored files and untracked __pycache__/*.pyc "
            "files, and remove its unit's F<n>.notes."
        ),
        stage,
    ),
    "--clean-scratch": (
        "Remove a scratch workspace's untracked files, keeping what is staged.",
        clean_scratch,
    ),
    "--staged": (
        "Print the recommendation for a scratch workspace's finding, and what the workspace holds.",
        show_staged,
    ),
    "--keep-notes": (
        "Write standard input, a verifier's notes, beside a scratch workspace as F<n>.notes.",
        keep_notes,
    ),
    "--write-diff": ("Write a scratch workspace's staged diff beside it as F<n>.diff.", write_diff),
    "--reset-scratch": ("Return a scratch workspace to the base it was opened at.", reset_scratch),
    "--remove-scratch": ("Delete one fenced scratch workspace.", remove_scratch),
}


def open_args(argv: list[str]) -> OpenArgs:
    """The `--open-scratch` command line, parsed; a usage error exits 2."""
    parser = argparse.ArgumentParser(
        prog="patch_artifacts.py --open-scratch",
        description="Make one unit's scratch workspace: a shared clone checked out at --base.",
        allow_abbrev=False,
    )
    parser.add_argument("workspace", help=WORKSPACE_HELP)
    parser.add_argument("--repo-root", required=True, help="the repository's top level")
    parser.add_argument("--base", required=True, help="the revision the patch is built on")
    args = parser.parse_args(argv, namespace=OpenArgs())
    if not plugin.SHA_RE.match(args.base):
        parser.error(f"--base {args.base!r} is not a hex revision id")
    return args


def workspace_args(form: str, argv: list[str]) -> WorkspaceArgs:
    """The command line of a form that tends one workspace, parsed; a usage error exits 2."""
    parser = argparse.ArgumentParser(
        prog=f"patch_artifacts.py {form}", description=WORKSPACE_FORMS[form][0], allow_abbrev=False
    )
    parser.add_argument("workspace", help=WORKSPACE_HELP)
    return parser.parse_args(argv, namespace=WorkspaceArgs())


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
            f"a patch run; {', '.join(['--open-scratch', *WORKSPACE_FORMS])} each tend one of "
            "its scratch workspaces (--help on any)."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "patch_dir", help="the patch run dir holding patches.json, F<n>.diff and F<n>.paths.<round>"
    )
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
    form = argv[0] if argv else ""
    if form == "--open-scratch":
        opening = open_args(argv[1:])
        return open_scratch(opening.workspace, repo_root=opening.repo_root, base=opening.base)
    if form in WORKSPACE_FORMS:
        return WORKSPACE_FORMS[form][1](workspace_args(form, argv[1:]).workspace)
    if form == "--prepare":
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
    except (PatchError, products.ProductError) as error:
        sys.stderr.write(f"patch_artifacts.py: {error}\n")
        return 1
    except OSError as error:
        sys.stderr.write(
            f"patch_artifacts.py: could not read or write the report's files: {error}\n"
        )
        return 1


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:]))
