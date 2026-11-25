#!/usr/bin/env python3
"""Render a scan's report from its run directory.

Writes CLAUDE-SECURITY-RESULTS.jsonl (one finding per line, fields in a fixed
order), CLAUDE-SECURITY-RESULTS.sarif (the same findings as a SARIF 2.1.0 log),
CLAUDE-SECURITY-RESULTS.md (the same findings as a report for a person) and the
CLAUDE-SECURITY-REVISION-<tag>.json stamp,
then removes the scan's run directory now that its records are
rendered. Each finding sits at the line of its file its quoted code is on and
carries an id computed from the file there, and findings that name one rule
at one line of a file are one record in every product, or, at Change Scan Effort
high, one in each section of the report that has such a finding (see one_per_site).
The session writes one part of the Markdown report: the text of its Coverage section, which is
read from coverage.md in the run directory. A render removes that file.
Filenames, JSONL field order, and verification.status semantics are stable
across releases.

Usage:
  render_report.py <run_dir> [--products-dir <dir>]

Exits 0 on success, 1 on a refusal naming what is wrong, 2 on a usage error, and 3 where
coverage.md holds no usable text.
A finding whose path cannot be carried is refused by name instead: the render
still exits 0, leaves it out of the JSONL and the SARIF results, describes it in the
Markdown report alone, and marks the stamp unverified (see verification.refused_findings).
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import uuid
from collections import Counter
from contextlib import suppress
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, TypedDict

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (
    absolute,
    atomic,
    console,
    display,
    markdown,
    plugin,
    sarif,
    secret,
    source,
    strictjson,
)
from lib.candidates import taken_from
from lib.chain import chain_of, pending_ranks
from lib.duration import elapsed_seconds
from lib.finding import (
    FINDING_ID_RE,
    PANEL_KEEP_QUORUM,
    PANEL_VOTER_COUNT,
    Confidence,
    Finding,
    FindingError,
    FindingPathError,
    Record,
    Severity,
    build_finding,
    file_field,
    finding_panels,
    findings_changed,
    highest,
    line_field,
    older_than_the_change,
    panel_complete,
    percent,
    scan_prefix_fits,
    scan_prefix_shaped,
    strength,
    unrecognized_cwes,
    vote_rounds,
)
from lib.link import is_link
from lib.remote import recordable
from lib.report import scan_report, session_text, without_diff
from lib.revision import SELF_REPORTED, RevisionError, revision_tag
from lib.strictjson import JsonMap, as_int, is_int, is_list, is_map, is_str, maps
from lib.unreadable import corrected

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class _ResearcherCounts(TypedDict, total=False):
    """The two verification counts a vote record may omit."""

    researchers_dispatched: int
    researchers_returned: int


class _RefusalRecord(TypedDict):
    id: str
    reason: str


class _RefusedFindings(TypedDict, total=False):
    """The refusals a render may add; absent entirely when every finding carried."""

    refused_findings: list[_RefusalRecord]


class VerificationSummary(_ResearcherCounts, _RefusedFindings):
    """The stamp's `verification` object; every path names why if not verified."""

    status: Literal["verified", "unverified"]
    candidates: int
    candidates_deduped: int
    panel_votes: int
    panel_reviewed_findings: int
    panel_quorum_findings: int
    unreviewed_candidate_sites: int
    incomplete_panel_candidates: int
    attested_findings: int
    reason: str | None
    reason_kind: str | None


class Meta(NamedTuple):
    """The scan meta a render reads back: the scan itself, and the fields read beside it."""

    scan: sarif.Scan
    scan_root: str
    revision: object
    revision_source: str
    model: object
    effort: object
    asked_for_max: bool


class Rendered(NamedTuple):
    """A completed render: findings, verification, stamp tag, and whether `max` was asked for.

    duration_s is None when the scan's start time is missing or unreadable; dirty_line tells the
    stamp's revision.dirty value, or is None where no line is due; follow_up_relay is the relay line
    for the stamp's run_shape.past_fix_follow_up, or None where the stamp has no such value;
    later_research_relay is the relay line on what the two later research stages left out, or None
    where coverage.json does not count it or has nothing to tell;
    left_unverified counts the candidates that the relay line on candidates left names: the chain's
    handed-on ones and those dropped without a complete round, or 0 where the chain hands none on.
    """

    findings: list[Record]
    verification: VerificationSummary
    tag: str
    asked_for_max: bool
    duration_s: int | None
    dirty_line: str | None
    follow_up_relay: str | None
    later_research_relay: str | None
    left_unverified: int


STAMP_ONLY = frozenset({
    "by_confidence",
    "pre_existing_at",
    "duration_s",
    "verification_runs",
    "past_fix_researchers",
    "past_fix_follow_up",
    "reason_kind",
    "pruned_buckets",
    "plugin_version",
})


def older_count(findings: Sequence[Record]) -> int:
    """How many of `findings` are marked older than the change."""
    return sum("older_than_the_change" in finding for finding in findings)


def findings_line(findings: Sequence[Record], refused: int) -> str:
    """The stamp's count of findings, how many of them are older than the change if any are, and
    how many more the report shows alone because they were refused."""
    older = older_count(findings)
    line = f"findings: {len(findings)}" + (f" ({older} older than the change)" if older else "")
    return line + (
        f"; {refused} more in the report only, which the files leave out" if refused else ""
    )


def dirty_line(revision: JsonMap) -> str | None:
    """The line that tells the revision's dirty value, or None where no line is due. A null is told
    only at a commit."""
    dirty = revision.get("dirty")
    if dirty is None and not revision.get("commit"):
        return None
    return f"revision.dirty: {strictjson.text(dirty)}"


class FollowUp(Enum):
    """Why past security fixes got no follow-up. Each member has coverage.json's word for it, and
    the report's text, which stands word for word in skills/claude-security/specs/report-spec.md."""

    NOT_RUN = ("not run", "These results include no follow-up of past security fixes.")
    NOTHING_LISTED = (
        "nothing listed",
        (
            "These results include no follow-up of past security fixes, because the scan listed no "
            "earlier commit whose message reads like one. If this is a shallow clone, such as a CI "
            "checkout of depth 1, scan a clone with its full history."
        ),
    )
    NONE_NEEDED = (
        "none needed",
        (
            "An agent looked at the list of commits that read like past security fixes and named "
            "no area for a further look."
        ),
    )

    def __init__(self, word: str, text: str) -> None:
        self.word = word
        self.text = text

    @classmethod
    def of(cls, word: object) -> FollowUp | None:
        """The member that has `word`. None if no member does."""
        return next((member for member in cls if member.word == word), None)


RELAY_OPENING: Final = "relay: say this to the user exactly as printed, in your results message"
RELAY_NO_FOLLOW_UP: Final = RELAY_OPENING + ", and say nothing more on past security fixes"
RELAY_LOST_RESEARCHERS: Final = (
    RELAY_NO_FOLLOW_UP
    + ", beyond how many researchers did not return and that their reading is missing"
)
RELAY_LEFT_OUT: Final = (
    RELAY_OPENING
    + ", add no count, cause or list of your own to these sentences, and name none of the places"
    + " or files that they count"
)


READ_NOTHING_REASON: Final = (
    "each answer held no finding and named no file that the agent read; the scan examined nothing"
)
RELAY_READ_NOTHING: Final = RELAY_OPENING


RELAY_UNVERIFIED: Final = (
    "relay: say this to the user exactly as printed, and say nothing more on continuing the scan"
)


STOP_OPENINGS: Final = {
    "failed": "A later verification run failed, so the scan did not finish verifying.",
    "stopped": "A later verification run was stopped, so the scan did not finish verifying.",
}


def left_unverified(continuing: int, incomplete: int) -> int:
    """The count for the line on candidates left: 0 where the chain hands none on, and otherwise the
    chain's candidates and those dropped without a complete round, which the stamp counts apart."""
    return continuing + incomplete if continuing else 0


def unverified_relay(count: int, stop: str | None) -> str:
    """The relay line on candidates left. Its first sentence names how the later run ended where
    `stop` says so."""
    opening = STOP_OPENINGS.get(stop or "", "The scan did not finish verifying.")
    return (
        f"{RELAY_UNVERIFIED}: {opening} {count} candidate(s) were left unverified, and only a new "
        "scan can verify them."
    )


def follow_up_relay(shape: Mapping[str, object]) -> str | None:
    """The relay line for run_shape's past_fix_follow_up, or None where it has no value."""
    follow_up = FollowUp.of(shape.get("past_fix_follow_up"))
    if follow_up is None:
        return None
    lost = follow_up is FollowUp.NOT_RUN and shape.get("past_fix_researchers")
    relay = RELAY_LOST_RESEARCHERS if lost else RELAY_NO_FOLLOW_UP
    return f"{relay}: {follow_up.text}"


def later_research_relay(coverage: JsonMap | None) -> str | None:
    """The relay line on what a codebase scan's two later research stages left out, with a sentence
    for each count that is over 0, and one where their list of packs was not loaded. None where
    coverage.json does not count it, or has nothing to tell."""
    later = (coverage or {}).get("laterResearch")
    left = later.get("leftOut") if is_map(later) else None
    if not is_map(left):
        return None
    leads, packs = left.get("leads"), left.get("packs")
    if not (is_int(leads) and is_int(packs)):
        return None
    said: list[str] = []
    if left.get("listNotLoaded") is True:
        said.append(
            "No reader for a whole run of neighbouring files was sent, because the list of those "
            "runs could not be loaded."
        )
    if leads > 0:
        said.append(
            "Places that researchers noted as possible flaws and that no follow-up researcher "
            f"was sent to: {leads}."
        )
    if packs > 0:
        said.append(
            "Runs of neighbouring files at which a flaw of MEDIUM or higher was reported and "
            f"that no reader for the whole run was sent to: {packs}."
        )
    if not said:
        return None
    if leads > 0 or packs > 0:
        said.append(f"The Coverage section of {plugin.RESULTS_MD_NAME} names up to 20 of each.")
    return f"{RELAY_LEFT_OUT}: {' '.join(said)}"


class Args(argparse.Namespace):
    """The parsed command line."""

    run_dir: str = ""
    products_dir: str | None = None
    stop: str | None = None


class RenderError(Exception):
    """A refusal; the message names what is wrong."""


class NoCoverageTextError(RenderError):
    """The run directory's coverage.md is missing, is no regular file, is not UTF-8, or prints no
    text."""


NO_COVERAGE_TEXT_EXIT: Final = 3
WRITE_COVERAGE_TEXT: Final = (
    "Write the report's Coverage section to it, in the run directory, before running this script."
)


class MissingFileError(RenderError):
    """A run file that read_json() was asked for is not there."""


# "Change Scan Effort: high" in any letter case, with any run of : * ` | or spaces before "high".
CLAIMS_CHANGE_SCAN_EFFORT_HIGH = re.compile(r"change scan effort[:*`| ]+high\b", re.IGNORECASE)


def refuse_unsupported_claim(written: str, mode: str, coverage: JsonMap | None) -> None:
    """Raises RenderError where `written`, the text of coverage.md as it stands in a scan in `mode`,
    says Change Scan Effort high and `coverage`, its coverage.json, does not. Nothing is refused
    for a codebase scan, or where `coverage` is None."""
    if mode == "scan" or coverage is None or plugin.at_change_scan_effort_high(coverage):
        return
    if claim := CLAIMS_CHANGE_SCAN_EFFORT_HIGH.search(markdown.printable(written)):
        msg = (
            f'{plugin.COVERAGE_MD_NAME} says "{claim[0]}", but coverage.json does not: the scan '
            "ran at the default Change Scan Effort. Say that there, without those words, "
            "and tell the user so."
        )
        raise RenderError(msg)


def read_json(run_dir: Path, name: str, *, if_missing: str) -> object:
    """The JSON value in a run file the render requires; a missing or malformed one is a refusal.
    The refusal of a missing file names the directory, and then says `if_missing`."""
    try:
        return strictjson.load(run_dir / name)
    except FileNotFoundError as error:
        msg = f"{os.path.abspath(run_dir)} holds no {name}. {if_missing}"
        raise MissingFileError(msg) from error
    except ValueError as error:
        msg = f"{name} is not valid JSON: {error}"
        raise RenderError(msg) from error


def read_meta(run_dir: Path) -> JsonMap:
    """The run's scan-meta.json; one that is missing, malformed or not an object is a refusal."""
    report = f"{plugin.REPORT_DIR_PREFIX}<timestamp>"
    if_missing = (
        "For the scan that you are rendering now, take the first of these that fits. "
        f"(1) If that scan's {report}, or another folder where this script already wrote that "
        f"scan's report, holds a stamp {plugin.revision_stamp_name('<tag>')}: "
        "the scan is already rendered there, and there is nothing left to render. "
        "Go on with that report. "
        f"(2) If (1) does not fit, and that scan's {report}/{plugin.RUN_DIR_NAME} holds "
        f"scan-meta.json: run this script on that {plugin.RUN_DIR_NAME}, "
        f"with --products-dir {report}. "
        "(3) If neither fits: that scan's scan-meta.json is lost, and the fix is a new scan, so "
        "tell the user to start one. "
        f"If that scan's {plugin.RUN_DIR_NAME} is still there, tell them also that it holds "
        "what that scan saved, and any draft report. "
        "If so, tell them to keep that directory, and any report directory that holds it: "
        f"{plugin.OLD_SCAN_KEEP_REASON}. "
        "A scan-meta.json that is made now, by hand or with write_scan_meta.py, or that comes "
        "from another scan, is not that scan's. "
        f"{plugin.OLD_SCAN_META_REASON}"
    )
    meta = read_json(run_dir, "scan-meta.json", if_missing=if_missing)
    if not is_map(meta):
        msg = "scan-meta.json is not a JSON object"
        raise RenderError(msg)
    return meta


def read_votes(run_dir: Path) -> JsonMap | None:
    """The workflow's vote record, or None when votes.json is absent or not marked as its own."""
    try:
        raw = strictjson.load(run_dir / "votes.json")
    except FileNotFoundError:
        return None
    except ValueError as error:
        msg = f"votes.json is not valid JSON: {error}"
        raise RenderError(msg) from error
    if not is_map(raw):
        msg = "votes.json must be a JSON object mapping the vote record"
        raise RenderError(msg)
    if raw.get("provenance") != plugin.VOTES_PROVENANCE:
        return None
    return raw


def read_coverage(run_dir: Path) -> tuple[JsonMap | None, str]:
    """The optional coverage.json. The stamp's run_shape comes from it, and it alone says that a
    scan ran at Change Scan Effort high.

    Returns (map_or_None, source): source is "coverage.json" when the file
    is a usable object, "unavailable" when it is absent, and "unreadable" when
    it exists but is not a usable object.
    """
    name = "coverage.json"
    try:
        raw = strictjson.load(run_dir / name)
    except FileNotFoundError:
        return None, "unavailable"
    except (OSError, ValueError):
        return None, "unreadable"
    return (raw, name) if is_map(raw) else (None, "unreadable")


COVERAGE_TEXT_CAP = 300
COVERAGE_LIST_ITEM_CAP = 200
COVERAGE_NAME_CAP = 100
REFUSED_RUN_CAP = 1000


def coverage_text(value: object, cap: int = COVERAGE_TEXT_CAP) -> str | None:
    """A coverage string, trimmed to `cap`, or None when the value is not a string."""
    return display.capped(value, cap) if is_str(value) else None


def coverage_texts(raw: object, cap: int) -> list[str]:
    """The strings among a coverage list, each trimmed to `cap`; anything else is dropped."""
    items: list[object] = raw if is_list(raw) else []
    return [text for item in items if (text := coverage_text(item, cap))]


def tree_relative(path: str, scan_root: str) -> str | None:
    """A skipped path relative to the scan root; None for an absolute spelling of anything else."""
    if not absolute.spelled(path):
        return path
    if not os.path.isabs(path):
        return None
    try:
        return absolute.relative(os.path.realpath(path), scan_root)
    except (ValueError, OSError):
        return None


def skipped_component(item: JsonMap, scan_root: str) -> dict[str, object]:
    paths = (
        tree_relative(path, scan_root)
        for path in coverage_texts(item.get("paths"), COVERAGE_LIST_ITEM_CAP)
    )
    return {
        "name": coverage_text(item.get("name"), COVERAGE_NAME_CAP) or "",
        "paths": [path for path in paths if path is not None],
        "reason": coverage_text(item.get("reason")) or "",
    }


def skipped_components(raw: object, scan_root: str) -> list[dict[str, object]] | None:
    """coverage.skippedComponents as [{name, paths, reason}], or None when unusable."""
    if not is_list(raw):
        return None
    return [skipped_component(entry, scan_root) for entry in raw if is_map(entry)]


def set_aside_places(raw: object, scan_root: str, prefix: str) -> list[dict[str, object]]:
    """coverage.preExistingAt as [{file, line, cwe}], with 0 for an unknown CWE or an absent line.
    An entry that names no file of the repository, or whose line is not a number, is dropped."""
    places: list[dict[str, object]] = []
    for entry in maps(raw):
        with suppress(FindingError):
            places.append({
                "file": percent(file_field(entry, "", scan_root, prefix, must_exist=True)),
                "line": line_field(entry, "line", "", 0),
                "cwe": max(as_int(entry.get("cwe")), 0),
            })
    return places


class PrunedBucket(TypedDict):
    """One stamp pruned_buckets entry: a group and the research lens it went without."""

    group: str
    lens: str


def pruned_buckets(raw: object) -> list[PrunedBucket] | None:
    """coverage.prunedBuckets as [{group, lens}], or None when unusable; junk is dropped."""
    if not is_list(raw):
        return None
    parts = (text.rpartition(":") for text in raw if is_str(text))
    return [
        {
            "group": display.capped(group, COVERAGE_LIST_ITEM_CAP),
            "lens": display.capped(lens, COVERAGE_LIST_ITEM_CAP),
        }
        for group, sep, lens in parts
        if sep and group and lens
    ]


def coverage_enum(value: object, allowed: tuple[str, ...]) -> str | None:
    """A coverage enum field, or None when absent or not one of the known values."""
    return value if is_str(value) and value in allowed else None


def coverage_count(value: object) -> int | None:
    """A coverage count field, or None when absent or not an integer."""
    return value if is_int(value) else None


def coverage_length(value: object) -> int | None:
    """How many entries a coverage list field holds, or None when absent or not a list."""
    return len(value) if is_list(value) else None


class ResearchCoverage(TypedDict):
    """The stamp's research_coverage: the coverage account's counts, and whether a list was cut."""

    files: int
    read: int
    not_reached: int
    unaccounted: int
    outside_components: int
    capped: bool


def research_coverage(raw: object) -> ResearchCoverage | None:
    """coverage.research as the stamp carries it, or None when the account was not checked."""
    tree = raw.get("tree") if is_map(raw) else None
    if not is_map(raw) or not is_map(tree):
        return None
    files, read, not_reached, unaccounted, outside = (
        tree.get(key) for key in ("files", "read", "notReached", "unaccounted", "outsideComponents")
    )
    if not (
        is_int(files)
        and is_int(read)
        and is_int(not_reached)
        and is_int(unaccounted)
        and is_int(outside)
    ):
        return None
    return {
        "files": files,
        "read": read,
        "not_reached": not_reached,
        "unaccounted": unaccounted,
        "outside_components": outside,
        "capped": raw.get("capped") is True,
    }


def run_shape(
    coverage: JsonMap | None,
    source: str,
    effort: object,
    scan_root: str,
    prefix: str,
    research: ResearchCoverage | None,
) -> dict[str, object]:
    """What shape actually ran, distinct from the effort tier that was recorded."""
    shape: dict[str, object] = {"requested_effort": effort, "collapsed": None, "source": source}
    if coverage is None:
        return shape
    replaced = {
        "candidates_replaced": coverage_count(coverage.get("candidatesReplaced")),
        "candidates_written": coverage_count(coverage.get("candidatesWritten")),
        "candidates_rewritten": coverage_count(coverage.get("candidatesRewritten")),
    }
    return {
        **shape,
        "collapsed": coverage_enum(coverage.get("collapsed"), ("small-scope",)),
        "diff_files": coverage_count(coverage.get("diffFiles")),
        "diff_lines": coverage_count(coverage.get("diffLines")),
        "pre_existing": coverage_length(coverage.get("preExisting")),
        "pre_existing_at": set_aside_places(coverage.get("preExistingAt"), scan_root, prefix),
        "scope_files": coverage_count(coverage.get("scopeFiles")),
        "empty_diff": bool(coverage.get("emptyDiff")),
        "empty_scope": bool(coverage.get("emptyScope")),
        "researchers_dispatched": coverage_count(coverage.get("researchersDispatched")),
        "verification_runs": coverage_count(coverage.get("verificationRun")),
        "past_fix_researchers": coverage_count(coverage.get("pastFixResearchers")),
        "past_fix_follow_up": coverage_enum(
            coverage.get("pastFixFollowUp"), tuple(member.word for member in FollowUp)
        ),
        "skipped_components": skipped_components(coverage.get("skippedComponents"), scan_root),
        "pruned_buckets": pruned_buckets(coverage.get("prunedBuckets")),
        "completeness_check_outcome": coverage_enum(
            coverage.get("completenessCheckOutcome"),
            ("checked", "partial", "not-checkable", "not-applicable"),
        ),
        "unaccounted_top_level_dirs": coverage_texts(
            coverage.get("unaccountedTopLevelDirs"), COVERAGE_LIST_ITEM_CAP
        ),
        "inventory_fallback": coverage_enum(
            coverage.get("inventoryFallback"),
            ("inventory-failed", "empty-partition", "incomplete-partition"),
        ),
        "top_level_dir_count": coverage_count(coverage.get("topLevelCount")),
        "target_files": coverage_count(coverage.get("targetFiles")),
        "component_cap": coverage_count(coverage.get("componentCap")),
        "research_coverage": research,
        **{name: count for name, count in replaced.items() if count is not None},
    }


def handed_on(votes: JsonMap) -> int:
    """How many candidates the vote record's chain leaves for a further run."""
    raw = votes.get("chain")
    if raw is None:
        return 0
    try:
        parsed = chain_of(raw)
    except ValueError as error:
        msg = f"votes.json chain {error}; the vote record is malformed"
        raise RenderError(msg) from error
    return len(pending_ranks(parsed))


def named_round(round_id: str) -> str:
    """The text a reason shows for a round id: the id if it fits FINDING_ID_RE, else a phrase."""
    return round_id if FINDING_ID_RE.match(round_id) else "an id that is not valid"


def stood_for(count: int, how: str) -> str:
    """The `count` findings a reported finding stands for, `how` saying in what way; no words
    for none."""
    if count == 1:
        return f"1 finding {how} a reported finding"
    return f"{count} findings {how} reported findings" if count else ""


def rows_not_loaded(run_dir: Path, coverage: JsonMap | None) -> int:
    """How many of the rows of the last report that write_scan_meta.py wrote the coverage record
    does not count as loaded: all of them where it gives no integer `lastReport.loaded`."""
    try:
        taken = taken_from(run_dir)
    except ValueError as error:
        raise RenderError(str(error)) from error
    if taken is None:
        return 0
    told = coverage.get("lastReport") if coverage else None
    loaded = told.get("loaded") if is_map(told) else None
    return taken["held"] - min(max(loaded, 0), taken["held"]) if is_int(loaded) else taken["held"]


def verification_summary(
    findings: Sequence[Finding],
    votes: JsonMap,
    *,
    merged_away: Sequence[str],
    votes_present: bool,
    continuing: int,
    refused: Sequence[_RefusalRecord],
    not_recorded: str,
    not_loaded: int,
    digest_differs: bool,
    returned_blind: int = 0,
) -> VerificationSummary:
    """Compute the stamp's verification object from the vote record and the render's refusals.

    status is 'verified' only when the vote record proves a complete panel
    round for every finding the report contains and for every other candidate that
    `candidates_deduped` counts, the round of each finding that is reported, listed or merged
    reaches the keep quorum, no candidate waits for a further run, the report accounts for every
    complete round at the keep quorum, the render refused nothing, and `digest_differs` is False;
    otherwise 'unverified' with a `reason` in prose and a fixed `reason_kind` word.
    The report accounts for a round whose finding it holds, lists, merges into another finding
    or refuses by name. `reason` lists the other such rounds, each by its id if the id is valid.
    `incomplete_panel_candidates` counts the unreported candidates whose round
    is not complete. `merged_away` holds the ids of the findings one_per_site
    merged into others. votes_present is False when read_votes returned None;
    `continuing` is handed_on(votes), the candidates left for a further verification
    run, and `reason` counts them whatever ground comes first.
    Where `not_recorded` has its line, save_result.py refused that run.
    `not_loaded` is rows_not_loaded(): where it is above 0, the status is 'unverified'.
    `refused` lists the findings the render refused,
    which the summary repeats under `refused_findings`.
    `digest_differs` says that findings.json does not match the digest in votes.json.
    `returned_blind` is without_diff(): with such a researcher, "none returned" has other words.
    """
    rounds = vote_rounds(votes)
    panels = finding_panels(rounds, [f["id"] for f in findings])
    also = finding_panels(rounds, [entry["id"] for f in findings for entry in f["also_at"]])
    away = finding_panels(rounds, list(merged_away))
    incomplete = sorted(i for i, panel in (*panels, *also, *away) if panel is None)
    reviewed = [panel for _, panel in panels if panel is not None]
    quorum = sum(panel["true"] >= PANEL_KEEP_QUORUM for panel in reviewed)
    refuted, gone = (
        sum(panel is not None and panel["true"] < PANEL_KEEP_QUORUM for _, panel in others)
        for others in (also, away)
    )
    reported = {finding_id for finding_id, _ in (*panels, *also, *away)}
    dropped_incomplete = sorted(
        named_round(round_id)
        for round_id, record in rounds.items()
        if round_id not in reported and panel_complete(record) is None
    )
    accounted = reported | {record["id"] for record in refused}
    missing = sorted(
        named_round(round_id)
        for round_id, record in rounds.items()
        if round_id not in accounted
        and (panel := panel_complete(record))
        and panel["true"] >= PANEL_KEEP_QUORUM
    )

    def as_count(key: str) -> int:
        """A vote count as a non-negative int; a wrong shape is a refusal."""
        raw = votes.get(key, 0)
        if not is_int(raw) or raw < 0:
            msg = (
                f"votes.json field {key!r} is not a non-negative integer ({raw!r}); the "
                "vote record is malformed"
            )
            raise RenderError(msg)
        return raw

    candidates = as_count("candidates")
    dispatched = as_count("researchers_dispatched") if "researchers_dispatched" in votes else None
    returned = as_count("researchers_returned") if "researchers_returned" in votes else None
    read_nothing = as_count("researchers_read_nothing")
    deduped = as_count("candidates_deduped")
    counted = deduped or (0 if rounds else candidates)

    kind: str | None = None
    reason: str | None = None
    if not votes_present:
        kind = "no-vote-record"
        reason = (
            "the scan's records hold no usable vote record, so nothing about this report can be "
            "attested"
        )
    elif "candidates" not in votes:
        kind = "no-candidate-count"
        reason = (
            "the scan's vote record gives no count of candidates, so nothing about this report "
            "can be attested"
        )
    elif dispatched and returned == 0:
        kind = "nothing-examined"
        reason = (
            f"{dispatched} research agent(s) were dispatched but none returned; the scan "
            "examined nothing"
        )
        if read_nothing == dispatched:
            reason = f"{dispatched} research agent(s) were dispatched, and {READ_NOTHING_REASON}"
    elif incomplete:
        kind = "finding-panel-incomplete"
        reason = f"these findings have no complete panel round: {', '.join(incomplete)}"
    elif findings and (quorum != len(findings) or refuted or gone):
        kind = "finding-below-quorum"
        short = len(findings) - quorum
        named = [
            f"{short} of {len(findings)} reported findings" if short else "",
            stood_for(refuted, "listed under"),
            stood_for(gone, "merged into"),
        ]
        *first, last = filter(None, named)
        who = f"{', '.join(first)}, and {last}," if first else last
        what = "a finding" if short + refuted + gone == 1 else "findings"
        reason = (
            f"{who} did not reach the keep quorum, so the report contains {what} the panel "
            "did not confirm"
        )
    elif not findings and rounds and not any(map(panel_complete, rounds.values())):
        kind = "no-panel-completed"
        reason = (
            f"{len(rounds)} panel round(s) were recorded but none completed a full "
            "review; no candidate was actually verified"
        )
    elif dropped_incomplete:
        kind = "candidate-panel-incomplete"
        reason = (
            f"{len(dropped_incomplete)} candidate(s) have no complete panel round in the scan's "
            f"records: {', '.join(dropped_incomplete)}"
        )
    elif digest_differs:
        kind = "finding-panel-incomplete"
        reason = (
            "the findings were changed after the scan saved them, so the panel's votes do not "
            "cover this report"
        )
    elif missing:
        kind = "kept-candidate-not-reported"
    elif continuing:
        kind = "continuation-incomplete"
    elif (unaccounted := max(counted - len(rounds), 0)) or not_loaded:
        kind = "candidates-not-paneled"
        no_round = (
            f"{unaccounted} candidate(s) have no panel round in the scan's records, so nothing "
            "shows that a panel reviewed them"
        )
        no_row = (
            f"{not_loaded} finding(s) of the last report were to be checked again, and the scan's "
            "record does not count them as loaded"
        )
        grounds = ((unaccounted, no_round), (not_loaded, no_row))
        reason = "; ".join(text for count, text in grounds if count)
    if kind == "nothing-examined" and returned_blind:
        reason = (
            f"{dispatched} research agent(s) were dispatched but none returned with its reading, "
            "so the change counts as not examined"
        )
    if missing:
        gap = (
            f"{len(missing)} finding(s) the verifiers confirmed are missing from the JSONL and the "
            f"SARIF results: {', '.join(missing)}"
        )
        reason = f"{reason}; {gap}" if reason else gap
    if continuing:
        left = continuation_text(continuing, not_recorded)
        reason = f"{reason}; {left}" if reason else left
    refusals = list(refused)
    if refusals:
        names = ", ".join(record["id"] for record in refusals)
        refusal_reason = (
            f"{len(refusals)} finding(s) were refused at render and are absent from the JSONL "
            f"and the SARIF results: {names}"
        )
        reason = f"{reason}; {refusal_reason}" if reason else refusal_reason
        kind = kind or "findings-refused"
    summary: VerificationSummary = {
        "status": plugin.VERIFIED if reason is None else plugin.UNVERIFIED,
        "candidates": candidates,
        "candidates_deduped": deduped,
        "panel_votes": as_count("panel_votes"),
        "panel_reviewed_findings": len(reviewed),
        "panel_quorum_findings": quorum,
        "unreviewed_candidate_sites": as_count("unreviewed_candidate_sites"),
        "incomplete_panel_candidates": len(dropped_incomplete),
        "attested_findings": 0,
        "reason": reason,
        "reason_kind": kind,
    }
    if dispatched is not None:
        summary["researchers_dispatched"] = dispatched
    if returned is not None:
        summary["researchers_returned"] = returned
    if refusals:
        summary["refused_findings"] = refusals
    return summary


def scan_of(meta: JsonMap) -> Meta:
    """The scan meta the run records. Its id, mode, root, prefix, scope and revision source are
    checked, and a wrong one is a refusal.

    A remote is left out instead when another version of the plugin saved it, when this
    plugin's manifest names no version, or when it is not in the recorded form.
    """
    scan_id = meta.get("scan_id")
    try:
        value = uuid.UUID(scan_id) if is_str(scan_id) else None
    except ValueError:
        value = None
    if value is None or value.version not in sarif.GUID_VERSIONS:
        msg = f"scan-meta.json scan_id {scan_id!r} is not a version 1-5 UUID"
        raise RenderError(msg)
    mode = meta.get("mode")
    if not is_str(mode) or mode not in plugin.MODES:
        msg = f"scan-meta.json mode {mode!r} is not a scan mode"
        raise RenderError(msg)
    scan_root = meta.get("scan_root")
    if not is_str(scan_root) or not scan_root.strip():
        msg = f"scan-meta.json scan_root {scan_root!r} is not a path"
        raise RenderError(msg)
    prefix = meta.get("scan_prefix")
    if prefix is None:
        prefix = ""
    if not is_str(prefix) or not scan_prefix_shaped(prefix):
        msg = f"scan-meta.json scan_prefix {prefix!r} is not a path prefix"
        raise RenderError(msg)
    try:
        os.path.realpath(scan_root)
    except (OSError, ValueError) as error:
        msg = f"scan-meta.json scan_root {scan_root!r} cannot be resolved"
        raise RenderError(msg) from error
    if not scan_prefix_fits(prefix, scan_root=scan_root):
        msg = f"scan-meta.json scan_prefix {prefix!r} is deeper than scan_root {scan_root!r}"
        raise RenderError(msg)
    version = plugin.version()
    saved = meta.get("remote")
    own = version is not None and meta.get("plugin_version") == version
    remote = saved if own and is_str(saved) and recordable(saved) else None
    scope = meta.get("scope", [])
    entries = [entry for entry in scope if is_str(entry)] if is_list(scope) else []
    if not is_list(scope) or len(entries) != len(scope):
        msg = f"scan-meta.json scope {scope!r} is not the list of paths the scan covered"
        raise RenderError(msg)
    revision: object = meta.get("revision")
    if revision is None:
        revision = {}
    revision_source = meta.get("revision_source", SELF_REPORTED)
    if not is_str(revision_source):
        msg = (
            f"scan-meta.json revision_source {revision_source!r} does not name what vouches for "
            "the revision"
        )
        raise RenderError(msg)
    clean_commit: str | None = None
    if is_map(revision) and revision.get("dirty") is False:
        commit = revision.get("commit")
        clean_commit = commit if is_str(commit) and plugin.SHA_RE.match(commit) else None
    scan = sarif.Scan(
        id=value,
        mode=mode,
        prefix=prefix,
        remote=remote,
        scope=tuple(entries),
        revision=clean_commit,
    )
    return Meta(
        scan,
        scan_root,
        revision,
        revision_source,
        meta.get("model"),
        meta.get("effort"),
        meta.get("asked_for_max") is True,
    )


def read_scan(run_dir: Path) -> tuple[JsonMap, Meta, str]:
    """The run's scan-meta.json as read and as scan_of() returns it, and its stamp file's tag.

    Where scan-meta.json is malformed or a field fails its check, the refusal advises a new scan,
    and says which scan-meta.json files are not the run's own. Where it is missing, the refusal
    gives three cases for the caller to choose from.
    """
    try:
        meta = read_meta(run_dir)
        narrowed = scan_of(meta)
        return meta, narrowed, revision_tag(narrowed.revision)
    except MissingFileError:
        raise
    except (RenderError, RevisionError) as error:
        msg = (
            f"{error}; the fix is a new scan, so tell the user to start one. "
            "Tell them also that this render wrote nothing, and that the run directory still "
            "holds what its scan saved, and any draft report. "
            "Tell them to keep that directory, and any report directory that holds it: "
            f"{plugin.OLD_SCAN_KEEP_REASON}. "
            "A scan-meta.json that is edited or made now, by hand or with write_scan_meta.py, or "
            "that comes from another scan, is not that scan's. "
            f"{plugin.OLD_SCAN_META_REASON}"
        )
        raise RenderError(msg) from error


UNVERIFIED_MEANS = (
    "An unverified status does not show the code is clean; a new scan may give a verified status."
)
STATUS_GOVERNS = "If the text below states another status, the status on this line is correct."


def with_status(text: str, verification: VerificationSummary, not_recorded: str = "") -> str:
    """`text`, the human-readable report, under a first line that gives the stamp's status and
    reason, then UNVERIFIED_MEANS, and last STATUS_GOVERNS. The reason
    has "see Coverage" in place of `not_recorded`, save_result.py's line on a run that it refused,
    and is folded to one line, with "<" written as "&lt;". The report of a verified scan is
    returned as it is."""
    if verification["status"] == plugin.VERIFIED:
        return text
    reason = verification["reason"] or ""
    if not_recorded:
        reason = reason.replace(f"not recorded ({not_recorded})", "not recorded (see Coverage)")
    reason = markdown.one_line(markdown.apart(reason)).replace("<", "&lt;")
    status = f"Verification status: **{verification['status']}**: {reason}."
    return f"{status} {UNVERIFIED_MEANS} {STATUS_GOVERNS}\n\n{text}"


PANEL_ACCOUNT_LABEL = "**From the scan's records:**"
PANEL_ACCOUNT_RANK = "If other text in this report gives a different count, use this one."
REASONS_WITHOUT_A_COUNT = ("no-vote-record", "no-candidate-count", "nothing-examined")


def panel_account(
    summary: VerificationSummary,
    findings: Sequence[Finding],
    merged_away: Sequence[str],
    votes: JsonMap,
    not_loaded: int,
    returned_blind: int = 0,
) -> str:
    """The paragraph of counts from the scan's records, or one fixed line if they give none, none
    of the researchers sent returned, or a researcher's reading is missing and there is no
    candidate. Where `returned_blind`, which is without_diff(), is above 0, "none returned" alone
    does not bring the line.
    `merged_away` is verification_summary's. `not_loaded` is rows_not_loaded(), which a sentence
    of its own gives, apart from the candidates."""
    rounds = vote_rounds(votes)
    named = {*merged_away, *(entry["id"] for f in findings for entry in (f, *f["also_at"]))}
    refused = {record["id"] for record in summary.get("refused_findings", ())}
    whole = {i: panel for i, r in rounds.items() if (panel := panel_complete(r))}
    below = {i for i, panel in whole.items() if panel["true"] < PANEL_KEEP_QUORUM}
    short = len(below - named - refused)
    missing = len(whole.keys() - below - named - refused)
    reports, joined = summary["candidates"], summary["candidates_deduped"]
    candidates = max(joined or reports, len({*rounds, *named, *refused}))
    sent = summary.get("researchers_dispatched", 0)
    lost = summary.get("researchers_returned", sent) < sent
    keeps_count = summary["reason_kind"] == "nothing-examined" and returned_blind > 0
    no_count = summary["reason_kind"] in REASONS_WITHOUT_A_COUNT and not keeps_count
    if no_count or (lost and not candidates):
        return f"{PANEL_ACCOUNT_LABEL} The scan's records give no usable count of candidates."
    unrecorded = candidates - len(whole.keys() | refused)
    gloss = " (several reports can make one candidate)" if candidates < reports else ""
    said = [f"Candidates{gloss}: {candidates}."]
    if gloss:
        said.insert(0, f"Reports that the researchers handed in: {reports}.")
    enough = f"{PANEL_KEEP_QUORUM} verifiers"
    lacks_one = summary["reason_kind"] == "kept-candidate-not-reported" and not refused
    if candidates and (summary["status"] == plugin.VERIFIED or lacks_one):
        alone = summary["panel_quorum_findings"]
        absent = f"; not in this report: {missing}" if missing else ""
        said.append(
            f"Candidates confirmed by at least {enough}: {len(named) + missing} "
            f"(reported on their own: {alone}; listed under or merged into another finding: "
            f"{len(named) - alone}{absent})."
        )
    if candidates:
        said.append(f"Candidates left out since fewer than {enough} voted to report them: {short}.")
    if refused:
        said.append(f"Candidates refused at render for a fault in their record: {len(refused)}.")
    if unrecorded:
        said.append(f"No complete panel on record (dropped, lost or still waiting): {unrecorded}.")
    if not_loaded:
        said.append(
            "Findings of the last report that the scan's record does not count as loaded: "
            f"{not_loaded}."
        )
    if on_two := sum(panel["voters"] < PANEL_VOTER_COUNT for panel in whole.values()):
        said.append(
            "Candidates decided on two verifiers' votes, because those two settled the result: "
            f"{on_two}."
        )
    return " ".join([PANEL_ACCOUNT_LABEL, *said, PANEL_ACCOUNT_RANK])


class Place(NamedTuple):
    """A site, in one section of the report."""

    site: sarif.Site
    older_than_the_change: bool


def one_per_site(findings: Sequence[Record], scan: sarif.Scan) -> tuple[list[Record], list[str]]:
    """The findings reduced to one per site (at Change Scan Effort high, one per site and section
    of the report), and one disclosure sentence per finding merged away.

    A site is a rule at a line of a file (sarif.site), which is what a result
    stands for to a SARIF or JSONL consumer, so the products carry one record
    for it: of the findings at one site the strongest is kept, the first of
    them in findings.json order when they tie, and each of the others is
    named in a sentence with the finding it was merged into. merged_into
    says what the kept record takes from the others. A finding with no site,
    one whose line was never determined, is kept as it is. A finding marked
    `older_than_the_change` merges only with findings that have the mark, so
    at Change Scan Effort high a site has at most one record for each section of the report.
    Where a site has both, each bears the hard-coded-credential CWE ids of the other, so neither
    quotes a line that either calls a hard-coded credential.
    """

    def place(item: Record) -> Place | None:
        where = sarif.site(item, scan)
        if where is None:
            return None
        return Place(where, "older_than_the_change" in item)

    places = [place(item) for item in findings]
    by_place: dict[Place, list[Record]] = {}
    for item, at in zip(findings, places):
        if at is not None:
            by_place.setdefault(at, []).append(item)
    strongest = {at: max(group, key=strength) for at, group in by_place.items()}
    sections = Counter(at.site for at in by_place)
    merged = [
        f"finding {other['id']} names the same site as finding {strongest[at]['id']}, "
        f"{percent(at.site.path)}:{at.site.line} under rule {at.site.rule}; merged into it, and it "
        "shows the highest severity and the highest confidence of the findings at that site"
        + (" in its section of the report" if sections[at.site] > 1 else "")
        for at, group in by_place.items()
        for other in group
        if other is not strongest[at]
    ]
    kept = with_lent_credentials({
        at: merged_into(strongest[at], group) for at, group in by_place.items()
    })
    unmerged = [
        item if at is None else kept[at]
        for item, at in zip(findings, places)
        if at is None or item is by_place[at][0]
    ]
    return unmerged, merged


def with_lent_credentials(kept: Mapping[Place, Record]) -> dict[Place, Record]:
    """`kept`, each record bearing the hard-coded-credential CWE ids of all the records at its
    site."""
    lent = [
        (at.site, cwe_id)
        for at, record in kept.items()
        for cwe_id in (record["cwe_id"], *record["other_cwe_ids"])
        if secret.is_credential_id(cwe_id)
    ]
    return {
        at: bearing(record, [cwe_id for site, cwe_id in lent if site == at.site])
        for at, record in kept.items()
    }


def bearing(record: Record, cwe_ids: Sequence[str]) -> Record:
    """`record` with `cwe_ids` among its further CWE ids, its own `cwe_id` and repeats left out."""
    further = dict.fromkeys([*record["other_cwe_ids"], *cwe_ids])
    return {**record, "other_cwe_ids": [i for i in further if i != record["cwe_id"]]}


def merged_into(kept: Record, group: Sequence[Record]) -> Record:
    """`kept`, the most severe of `group`, with the CWE ids and the `also_at` and `also_filed_at`
    entries of the findings merged into it, at the highest confidence in `group`."""
    others = [
        cwe_id
        for item in group
        for cwe_id in (item["cwe_id"], *item["other_cwe_ids"])
        if cwe_id != kept["cwe_id"]
    ]
    rest = [item for item in group if item is not kept]
    listed = [entry for item in rest for entry in item["also_at"]]
    filed = [entry for item in (kept, *rest) for entry in item.get("also_filed_at", [])]
    _, confidence = highest(map(strength, group))
    merged: Record = {
        **kept,
        "confidence": confidence.name,
        "other_cwe_ids": list(dict.fromkeys([*kept["other_cwe_ids"], *others])),
        "also_at": [*kept["also_at"], *listed],
    }
    if filed:
        merged["also_filed_at"] = filed
    return merged


def continuation_text(continuing: int, not_recorded: str) -> str:
    """The sentence the stamp's reason and the log's notification share for an unfinished chain.
    `not_recorded` is save_result.py's line on a run that it refused, or empty."""
    if not_recorded:
        handed = f"{continuing} candidate(s) were handed to a verification run that"
        return f"{handed} completed and was not recorded ({not_recorded})"
    return (
        f"{continuing} candidate(s) were left for a further verification run, and the scan's "
        "records hold no complete review or verdict on them"
    )


def notifications_of(
    shape: Mapping[str, object],
    research: ResearchCoverage | None,
    verification: VerificationSummary,
    merged: Sequence[str],
    left_out: Sequence[str],
    unrecognized: Sequence[str],
    symlinks: Sequence[str],
    revision: object,
    continuing: int,
    refused: Sequence[_RefusalRecord],
    *,
    not_recorded: str,
) -> list[dict[str, object]]:
    """The invocation notifications: skipped, capped, merged, left out, mislabeled, refused or
    unverified.

    `research` is research_coverage's. The sentences of `merged` (one_per_site)
    and of `left_out` (an `also_filed_at` entry whose path cannot be carried)
    are disclosed at level note, those of `unrecognized` (unrecognized_cwes)
    at level warning. `symlinks` names
    the root-level symbolic links the scan's extent left out unfollowed;
    `continuing` is handed_on(votes). `not_recorded` words the notice of it (continuation_text),
    and adds a clause to coverage/unverified-by-cap. `refused` is the render's per-finding path
    refusals, each disclosed at level warning.
    """
    note = sarif.notification
    skipped = shape.get("skipped_components")
    notes = [
        note("coverage/skipped-component", "note", f"Skipped component {s['name']}: {s['reason']}")
        for s in (skipped if is_list(skipped) else [])
        if is_map(s)
    ]
    if is_map(revision) and revision.get("sparse") is True:
        absent = revision.get("not_checked_out_dirs")
        names = ", ".join(d for d in (absent if is_list(absent) else []) if is_str(d))
        text = "Sparse checkout: only the checked-out part of the repository was scanned"
        if names:
            text += f"; tracked top-level directories not checked out: {names}"
        notes.append(note("coverage/sparse-checkout", "note", text))
    unaccounted = shape.get("unaccounted_top_level_dirs")
    if is_list(unaccounted) and unaccounted:
        names = ", ".join(d for d in unaccounted if is_str(d))
        text = f"Directories that no component or skipped area accounts for: {names}"
        notes.append(note("coverage/unaccounted-top-level-dirs", "note", text))
    if symlinks:
        names = ", ".join(symlinks)
        text = f"Root-level symbolic links not followed, left out of the scan's extent: {names}"
        notes.append(note("coverage/unfollowed-symlinks", "note", text))
    if research and (research["not_reached"] or research["unaccounted"]):
        floor, ceiling = ("at least ", "at most ") if research["capped"] else ("", "")
        text = (
            f"Research coverage: of {research['files']} files in the components researched, "
            f"{floor}{research['read']} read to a conclusion, "
            f"{research['not_reached']} declared not reached, "
            f"{ceiling}{research['unaccounted']} in no researcher's account; "
            f"{research['outside_components']} more outside every component"
        )
        notes.append(note("coverage/files-not-reached", "note", text))
    if unreviewed := verification["unreviewed_candidate_sites"]:
        text = f"{unreviewed} candidate site(s) were recorded but never reviewed by the panel"
        if not_recorded:
            text += ", or reviewed in a verification run that was not recorded"
        notes.append(note("coverage/unverified-by-cap", "warning", text))
    if dropped := verification["incomplete_panel_candidates"]:
        text = f"{dropped} candidate(s) have no complete panel round in the scan's records"
        notes.append(note("verification/incomplete-panel", "warning", text))
    if continuing:
        text = continuation_text(continuing, not_recorded)
        notes.append(note("verification/continuation-incomplete", "warning", text))
    notes += [note("finding/merged", "note", text) for text in merged]
    notes += [note("finding/report-left-out", "note", text) for text in left_out]
    notes += map(sarif.unrecognized_cwe_note, unrecognized)
    notes += [
        note(
            "verification/refused-finding",
            "warning",
            f"Finding {record['id']} was refused at render and is absent from the JSONL and "
            f"the SARIF results: {record['reason']}",
        )
        for record in refused
    ]
    if verification["status"] == plugin.UNVERIFIED:
        notes.append(sarif.unverified_note(verification["reason"] or ""))
    return notes


class Outcomes(NamedTuple):
    """What one raw findings.json record yields."""

    found: list[Finding | FindingPathError]
    # The findings it lists whose paths are not refused. Empty where its own path is refused.
    listed: list[Finding]
    uncarried: list[FindingPathError]


def built_or_refused(
    raw: object,
    index: int,
    rounds_by_id: JsonMap,
    scan_root: str,
    scan_prefix: str,
    must_exist: bool,
    *,
    blank_alone: bool,
) -> Outcomes:
    """What one raw record yields. A record refused for its path lists none: each finding it
    listed is yielded as a finding or a path refusal of its own."""
    try:
        built = build_finding(
            raw,
            index,
            rounds_by_id,
            scan_root,
            scan_prefix,
            must_exist,
            blank_alone=blank_alone,
        )
    except FindingPathError as error:
        return Outcomes([error, *error.listed], [], [])
    return Outcomes([built.finding, *built.refused], built.carried, built.uncarried)


def left_out_of(where: str, errors: Sequence[FindingPathError]) -> list[str]:
    """One sentence for each replaced report in `errors`: it is absent from `where`."""
    return [
        f"Finding {error.finding_id}: also_filed_at entry {error.filed_entry} is absent from "
        f"{where}: its file {error.wrong}"
        for error in errors
    ]


def render(run_dir: Path, products_dir: Path) -> Rendered:
    """Read the run's records, validate them, build every product, then write them, stamp last,
    and remove coverage.md."""
    if plugin.holds_analysis(Path(os.path.abspath(products_dir))):
        msg = f"{products_dir} is an attack surface analysis's folder: name another directory"
        raise RenderError(msg)
    meta, narrowed, tag = read_scan(run_dir)
    scan, scan_root, revision, revision_source, model, effort, asked_for_max = narrowed
    if_missing = (
        plugin.lost_findings_text(run_dir)
        if os.path.isfile(run_dir / "votes.json")
        else "Run save_result.py on the scan's output file and follow its `next:` line."
    )
    findings_in = read_json(run_dir, "findings.json", if_missing=if_missing)
    if not is_list(findings_in):
        msg = "findings.json must be a JSON array"
        raise RenderError(msg)
    coverage, coverage_source = read_coverage(run_dir)
    if coverage is not None:
        coverage = corrected(coverage, meta)
    ran_at_change_scan_effort_high = bool(coverage) and plugin.at_change_scan_effort_high(coverage)
    votes_raw = read_votes(run_dir)
    votes: JsonMap = {} if votes_raw is None else votes_raw
    rounds_raw = votes.get("rounds")
    rounds_by_id: JsonMap = {}
    if rounds_raw is not None:
        if not is_map(rounds_raw):
            kind = type(rounds_raw).__name__
            msg = f"votes.json 'rounds' must be an object keyed by finding id, not {kind}"
            raise RenderError(msg)
        rounds_by_id = rounds_raw

    results = [
        built_or_refused(
            raw,
            i,
            rounds_by_id,
            scan_root,
            scan.prefix,
            scan.mode == "scan",
            blank_alone=ran_at_change_scan_effort_high,
        )
        for i, raw in enumerate(findings_in)
    ]
    outcomes = [outcome for result in results for outcome in result.found]
    listed_by_id = {f["id"]: f for result in results for f in result.listed}
    built = [item for item in outcomes if not isinstance(item, FindingPathError)]
    if ran_at_change_scan_effort_high:
        built = [older_than_the_change(item, rounds_by_id) for item in built]
    path_errors = [item for item in outcomes if isinstance(item, FindingPathError)]
    uncarried = [error for result in results for error in result.uncarried]
    left_out = left_out_of("this log and the JSONL", uncarried)
    all_uncarried = [*uncarried, *(entry for refusal in path_errors for entry in refusal.uncarried)]
    refused: list[_RefusalRecord] = [
        {"id": item.finding_id, "reason": f"its file {item.wrong}{item.gone_with}"}
        for item in path_errors
    ]
    credentials = sorted(
        entry["id"]
        for f in built
        for entry in f["also_at"]
        if secret.is_credential_id(entry["cwe_id"])
    ) + sorted({
        f"{f['id']} also_filed_at"
        for f in (*built, *(error.finding for error in path_errors))
        for entry in f.get("also_filed_at", [])
        if any(map(secret.is_credential_id, (entry["cwe_id"], *entry["other_cwe_ids"])))
    })
    if credentials:
        msg = (
            "a hard-coded credential is only ever a finding of its own; findings.json lists "
            f"these under another finding: {', '.join(credentials)}"
        )
        raise RenderError(msg)
    listed = [entry["id"] for f in built for entry in f["also_at"]]
    counted = Counter([f["id"] for f in built] + listed + [record["id"] for record in refused])
    repeated = sorted(finding_id for finding_id, count in counted.items() if count > 1)
    if repeated:
        msg = f"findings.json uses these finding ids more than once: {', '.join(repeated)}"
        raise RenderError(msg)
    sources = {
        path: text
        for path in {f["file"] for f in (*built, *listed_by_id.values())}
        if (text := source.read(scan_root, path)) is not None
    }
    refused_secrets = [e.snippet for e in path_errors if any(map(secret.is_credential_cwe, e.cwes))]
    records = sarif.placed(
        built, scan, sources, listed=listed_by_id, refused_secrets=refused_secrets
    )
    findings, merged = one_per_site(records, scan)
    kept = {f["id"] for f in findings}

    coverage_path = run_dir / plugin.COVERAGE_MD_NAME
    if not os.path.isfile(coverage_path):
        msg = (
            f"{plugin.COVERAGE_MD_NAME} is missing. {WRITE_COVERAGE_TEXT} "
            "If this script already rendered this run, there is nothing left to render."
        )
        raise NoCoverageTextError(msg)
    try:
        raw_text = coverage_path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        msg = f"{plugin.COVERAGE_MD_NAME} is not valid UTF-8: {error}"
        raise NoCoverageTextError(msg) from error
    session_coverage = session_text(raw_text)
    if not session_coverage.strip():
        msg = f"{plugin.COVERAGE_MD_NAME} holds no text. {WRITE_COVERAGE_TEXT}"
        raise NoCoverageTextError(msg)
    refuse_unsupported_claim(raw_text, scan.mode, coverage)

    counts = Counter(f["severity"] for f in findings)
    graded = Counter(strength(f) for f in findings if "older_than_the_change" not in f)
    older = older_count(findings)
    continuing = handed_on(votes)
    line = (
        coverage.get(plugin.RUN_NOT_RECORDED_KEY)
        if coverage and ran_at_change_scan_effort_high
        else None
    )
    told = line if is_str(line) and continuing else ""
    not_recorded = display.capped(display.written_out(told), REFUSED_RUN_CAP)
    merged_away = [record["id"] for record in records if record["id"] not in kept]
    not_loaded = rows_not_loaded(run_dir, coverage)
    returned_blind = without_diff(coverage)
    digest_differs = findings_changed(run_dir, votes)
    verification = verification_summary(
        findings,
        votes,
        merged_away=merged_away,
        votes_present=votes_raw is not None,
        continuing=continuing,
        refused=refused,
        not_recorded=not_recorded,
        not_loaded=not_loaded,
        digest_differs=digest_differs,
        returned_blind=returned_blind,
    )
    research = research_coverage(coverage.get("research") if coverage else None)
    shape = run_shape(coverage, coverage_source, effort, scan_root, scan.prefix, research)
    generated = datetime.now(timezone.utc).replace(microsecond=0)
    duration = elapsed_seconds(meta.get("started_at"), generated)
    stamp: dict[str, object] = {
        "generated_at": generated.isoformat(),
        "duration_s": duration,
        "scan_id": str(scan.id),
        "mode": plugin.STAMP_MODES[scan.mode],
        "plugin_version": plugin.version(),
        "scan_prefix": scan.prefix,
        "scope": list(scan.scope),
        "revision": revision,
        "revision_source": revision_source,
        "model": model,
        "effort": "high" if ran_at_change_scan_effort_high else effort,
        **(
            {"change_scan_effort": plugin.CHANGE_SCAN_EFFORT_HIGH}
            if ran_at_change_scan_effort_high
            else {}
        ),
        "run_shape": shape,
        "findings": {
            "total": len(findings),
            "critical": counts["CRITICAL"],
            "high": counts["HIGH"],
            "medium": counts["MEDIUM"],
            "low": counts["LOW"],
            "by_confidence": {
                severity.name.lower(): {
                    confidence.name: graded[severity, confidence] for confidence in Confidence
                }
                for severity in Severity
            },
            **({"older_than_the_change": older} if older else {}),
        },
        "verification": verification,
    }

    jsonl = sarif.jsonl_text(findings)
    body = scan_report(
        scan,
        scan.remote or Path(scan_root).name,
        stamp,
        findings,
        path_errors,
        rounds=rounds_by_id,
        digest_differs=digest_differs,
        disclosed=[
            *merged,
            *left_out_of("this report, the SARIF log and the JSONL", all_uncarried),
        ],
        listed=listed_by_id,
        session_coverage=session_coverage,
        coverage=coverage,
        account=panel_account(
            verification, findings, merged_away, votes, not_loaded, returned_blind
        ),
    )
    report = with_status(body, verification, not_recorded).encode("utf-8", "backslashreplace")
    run_properties = {
        key: {k: v for k, v in value.items() if k not in STAMP_ONLY} if is_map(value) else value
        for key, value in stamp.items()
        if key not in STAMP_ONLY and (key != "model" or value is not None)
    }
    panels = {
        f["id"]: panel
        for f in findings
        if not digest_differs and (panel := panel_complete(rounds_by_id.get(f["id"])))
    }
    unrecognized = unrecognized_cwes(findings)
    unfinished = [continuation_text(continuing, not_recorded)] if continuing else []
    refusal_lines = [
        f"refused {error.finding_id}: {error}{error.gone_with}" for error in path_errors
    ]
    refusal_lines += [
        f"left out {error.finding_id} also_filed_at entry {error.filed_entry}: {error}"
        for error in all_uncarried
    ]
    for text in merged + unrecognized + unfinished + refusal_lines:
        sys.stderr.write(f"render_report.py: {display.written_out(text)}\n")
    symlinks = coverage_texts(meta.get("unfollowed_symlinks"), COVERAGE_LIST_ITEM_CAP)
    notifications = notifications_of(
        shape,
        research,
        verification,
        merged,
        left_out,
        unrecognized,
        symlinks,
        revision,
        continuing,
        refused,
        not_recorded=not_recorded,
    )
    sarif_log = sarif.log(findings, scan, plugin.version(), run_properties, panels, notifications)
    sarif_doc = strictjson.text(sarif_log, indent=2) + "\n"
    for stale in products_dir.iterdir():
        if plugin.is_revision_stamp(stale):
            stale.unlink()
    atomic.write(products_dir / plugin.JSONL_NAME, jsonl.encode())
    atomic.write(products_dir / plugin.SARIF_NAME, sarif_doc.encode())
    atomic.write(products_dir / plugin.RESULTS_MD_NAME, report)
    stamp_path = products_dir / plugin.revision_stamp_name(tag)
    atomic.write(stamp_path, (strictjson.text(stamp, indent=2) + "\n").encode())
    coverage_path.unlink()

    return Rendered(
        findings,
        verification,
        tag,
        asked_for_max,
        duration,
        dirty_line(revision) if is_map(revision) else None,
        follow_up_relay(shape),
        later_research_relay(coverage),
        left_unverified(continuing, verification["incomplete_panel_candidates"]),
    )


def remove_run_dir(run_dir: Path, products_dir: Path) -> str:
    """Remove the scan's run directory once rendered; returns a one-line status."""
    # abspath folds ".." without following symlinks, so the check below sees this path's own name.
    target = Path(os.path.abspath(run_dir))
    if target.name != plugin.RUN_DIR_NAME:
        return f"kept {run_dir} (not a {plugin.RUN_DIR_NAME} run directory)"
    if os.path.realpath(target) == os.path.realpath(products_dir):
        return f"kept {run_dir} (it holds the products)"
    if not plugin.REPORT_DIR_RE.match(target.parent.name):
        return f"kept {run_dir} (not inside a CLAUDE-SECURITY-<timestamp> report directory)"
    for directory in (target, target.parent):
        if is_link(directory):
            return f"kept {run_dir} ('{directory}' is a symbolic link)"
    try:
        shutil.rmtree(str(target))
    except OSError as error:
        detail = console.removal_failure_detail(error)
        return f"WARNING: could not remove run directory {run_dir}: {detail}"
    return f"removed run directory {run_dir}"


def argument_parser() -> argparse.ArgumentParser:
    """The command line: which run directory to render, and where its products go."""
    parser = argparse.ArgumentParser(
        prog="render_report.py",
        description="Render a scan's report from its run directory.",
        allow_abbrev=False,
    )
    parser.add_argument("run_dir", help="the run directory holding the scan's records")
    parser.add_argument(
        "--products-dir", help="where the products are written (default: the run directory)"
    )
    parser.add_argument(
        "--stop",
        choices=sorted(STOP_OPENINGS),
        help="how a later verification run ended, as its notice says",
    )
    return parser


def stamped_target_relay(stamp_path: Path) -> str | None:
    """plugin.folder_target_relay() for the results message, from the stamp at `stamp_path`. None
    unless that is the stamp of a codebase scan with no scope below its repository's top."""
    stamp = strictjson.load(stamp_path)
    if not is_map(stamp) or stamp.get("mode") != plugin.STAMP_MODES["scan"] or stamp.get("scope"):
        return None
    prefix = stamp.get("scan_prefix")
    return plugin.folder_target_relay(prefix, done=True) if is_str(prefix) and prefix else None


def main(argv: list[str]) -> int:
    parser = argument_parser()
    args = parser.parse_args(argv, namespace=Args())
    if not os.path.isdir(args.run_dir):
        parser.error(f"not a directory: {args.run_dir}")
    products = args.products_dir or args.run_dir
    if not os.path.isdir(products):
        parser.error(f"products directory is not a directory: {products}")
    run_dir, products_dir = Path(args.run_dir), Path(products)
    try:
        rendered = render(run_dir, products_dir)
        stamp_name = plugin.revision_stamp_name(rendered.tag)
        target_relay = stamped_target_relay(products_dir / stamp_name)
    except (RenderError, FindingError) as error:
        sys.stderr.write(f"render_report.py: {error}\n")
        return NO_COVERAGE_TEXT_EXIT if isinstance(error, NoCoverageTextError) else 1
    except OSError as error:
        sys.stderr.write(f"render_report.py: could not read or write the report's files: {error}\n")
        return 1
    warning = plugin.worktree_warning(products_dir)
    removal = remove_run_dir(run_dir, products_dir)
    count = len(rendered.findings)
    tally = f"{count} finding{'' if count == 1 else 's'}"
    print(
        f"wrote {plugin.JSONL_NAME}, {plugin.SARIF_NAME} ({tally}) "
        f"and {stamp_name} into {products_dir}"
    )
    print(f"stamp: {stamp_name}")
    print(f"verification.status: {rendered.verification['status']}")
    if reason := rendered.verification["reason"]:
        print(f"verification.reason: {reason}")
    print(findings_line(rendered.findings, len(rendered.verification.get("refused_findings", ()))))
    print(f"duration_s: {strictjson.text(rendered.duration_s)}")
    if target_relay:
        print(target_relay)
    if rendered.dirty_line:
        print(rendered.dirty_line)
    print(removal)
    if warning:
        print(f"{RELAY_OPENING}: {warning}")
    if reason and READ_NOTHING_REASON in reason:
        print(f"{RELAY_READ_NOTHING}: {reason}")
    if rendered.follow_up_relay:
        print(rendered.follow_up_relay)
    if rendered.later_research_relay:
        print(rendered.later_research_relay)
    if rendered.left_unverified:
        print(unverified_relay(rendered.left_unverified, args.stop))
    if rendered.asked_for_max:
        print(plugin.RETIRED_MAX_RELAY)
    return 0


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:]))
