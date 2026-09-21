#!/usr/bin/env python3
"""Render a scan's machine-readable artifacts from its run directory.

Writes CLAUDE-SECURITY-RESULTS.jsonl (one finding per line, fields in a fixed
order), CLAUDE-SECURITY-RESULTS.sarif (the same findings as a SARIF 2.1.0 log)
and the CLAUDE-SECURITY-REVISION-<tag>.json stamp, places the report markdown
beside them, then removes the scan's run directory now that its records are
rendered. Each finding sits at the line of its file its quoted code is on and
carries an id computed from the file there, and findings that name one rule
at one line of a file are one record in every product (see one_per_site).
Filenames, JSONL field order, and verification.status semantics are stable
across releases.

Usage:
  render_report.py <run_dir> [--products-dir <dir>]

Exits 0 on success, 1 on a refusal naming what is wrong, 2 on a usage error.
A finding whose path cannot be carried is refused by name instead: the render
still exits 0, delivers the products without it, and marks the stamp
unverified (see verification.refused_findings).
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
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypedDict

# The lib/ package lives next to this script. Python normally adds a script's own
# directory to the import path, but not under -P or PYTHONSAFEPATH, so we add it here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import absolute, console, cwe, plugin, sarif, secret, source, strictjson
from lib.chain import chain_of, pending_ranks
from lib.finding import (
    CONFIDENCES,
    PANEL_KEEP_QUORUM,
    PANEL_VOTER_COUNT,
    SEVERITIES,
    Finding,
    FindingError,
    FindingPathError,
    Record,
    build_finding,
    panel_complete,
    scan_prefix_shaped,
)
from lib.strictjson import JsonMap, is_int, is_list, is_map, is_str

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

    status: str
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
    """The scan meta a render reads back: the scan itself, and the stamp fields beside it."""

    scan: sarif.Scan
    scan_root: str
    revision: object
    revision_source: str
    model: object
    effort: object


class Rendered(NamedTuple):
    """A completed render: the findings, their verification, and the stamp's tag."""

    findings: list[Record]
    verification: VerificationSummary
    tag: str


REVISION_PREFIX = "CLAUDE-SECURITY-REVISION-"
STAMP_ONLY = frozenset({"duration_s", "verification_runs", "reason_kind"})
JSONL_NAME = "CLAUDE-SECURITY-RESULTS.jsonl"
SARIF_NAME = "CLAUDE-SECURITY-RESULTS.sarif"
SANITIZED_REMOTE_RE = re.compile(
    r"https://[a-z0-9.-]+(?::[0-9]+)?/(?:[A-Za-z0-9._~/-]|%[0-9A-F]{2})+\Z"
)


class Args(argparse.Namespace):
    """The parsed command line."""

    run_dir: str = ""
    products_dir: str | None = None


class RenderError(Exception):
    """A refusal; the message names what the caller must fix."""


def read_json(run_dir: Path, name: str) -> object:
    """The JSON value in a run file the render requires; a missing or malformed one is a refusal."""
    try:
        return strictjson.load(run_dir / name)
    except FileNotFoundError as error:
        msg = f"{name} is missing from the run directory. Write it before running this script."
        raise RenderError(msg) from error
    except ValueError as error:
        msg = f"{name} is not valid JSON: {error}"
        raise RenderError(msg) from error


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
        raise RenderError("votes.json must be a JSON object mapping the vote record")
    if raw.get("provenance") != plugin.VOTES_PROVENANCE:
        return None
    return raw


def read_coverage(run_dir: Path) -> tuple[JsonMap | None, str]:
    """The optional coverage.json for the informational run_shape field.

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


def coverage_text(value: object, cap: int = COVERAGE_TEXT_CAP) -> str | None:
    """A coverage string, trimmed to `cap`, or None when the value is not a string."""
    if not is_str(value):
        return None
    if len(value) > cap:
        return value[:cap] + f"...[+{len(value) - cap} chars]"
    return value


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
    paths = (tree_relative(path, scan_root) for path in coverage_texts(item.get("paths"), 200))
    return {
        "name": coverage_text(item.get("name"), 100) or "",
        "paths": [path for path in paths if path is not None],
        "reason": coverage_text(item.get("reason")) or "",
    }


def skipped_components(raw: object, scan_root: str) -> list[dict[str, object]] | None:
    """coverage.skippedComponents as [{name, paths, reason}], or None when unusable."""
    if not is_list(raw):
        return None
    return [skipped_component(entry, scan_root) for entry in raw if is_map(entry)]


def coverage_enum(value: object, allowed: tuple[str, ...]) -> str | None:
    """A coverage enum field, or None when absent or not one of the known values."""
    return value if is_str(value) and value in allowed else None


def coverage_count(value: object) -> int | None:
    """A coverage count field, or None when absent or not an integer."""
    return value if is_int(value) else None


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
    research: ResearchCoverage | None,
) -> dict[str, object]:
    """What shape actually ran, distinct from the effort tier that was asked."""
    shape: dict[str, object] = {"requested_effort": effort, "collapsed": None, "source": source}
    if coverage is None:
        return shape
    return {
        **shape,
        "collapsed": coverage_enum(coverage.get("collapsed"), ("small-diff", "small-scope")),
        "diff_files": coverage_count(coverage.get("diffFiles")),
        "diff_lines": coverage_count(coverage.get("diffLines")),
        "scope_files": coverage_count(coverage.get("scopeFiles")),
        "empty_diff": bool(coverage.get("emptyDiff")),
        "empty_scope": bool(coverage.get("emptyScope")),
        "researchers_dispatched": coverage_count(coverage.get("researchersDispatched")),
        "verification_runs": coverage_count(coverage.get("verificationRun")),
        "skipped_components": skipped_components(coverage.get("skippedComponents"), scan_root),
        "completeness_check_outcome": coverage_enum(
            coverage.get("completenessCheckOutcome"),
            ("checked", "partial", "not-checkable", "not-applicable"),
        ),
        "unaccounted_top_level_dirs": coverage_texts(coverage.get("unaccountedTopLevelDirs"), 200),
        "inventory_fallback": coverage_enum(
            coverage.get("inventoryFallback"),
            ("inventory-failed", "empty-partition", "incomplete-partition"),
        ),
        "top_level_dir_count": coverage_count(coverage.get("topLevelCount")),
        "target_files": coverage_count(coverage.get("targetFiles")),
        "component_cap": coverage_count(coverage.get("componentCap")),
        "research_coverage": research,
    }


def handed_on(votes: JsonMap) -> int:
    """How many candidates the vote record's chain leaves to a run that did not complete."""
    raw = votes.get("chain")
    if raw is None:
        return 0
    try:
        parsed = chain_of(raw)
    except ValueError as error:
        msg = f"votes.json chain {error}; the vote record is malformed"
        raise RenderError(msg) from error
    return len(pending_ranks(parsed))


def verification_summary(
    findings: Sequence[Finding],
    votes: JsonMap,
    votes_present: bool = True,
    continuing: int = 0,
    refused: Sequence[_RefusalRecord] = (),
) -> VerificationSummary:
    """Compute the stamp's verification object from the vote record and the render's refusals.

    status is 'verified' only when the vote record proves a complete panel
    round for every finding the report contains and for every other candidate
    it holds a round for, and the render refused nothing; otherwise
    'unverified' with a `reason` in prose and a fixed `reason_kind` word.
    `incomplete_panel_candidates` counts the unreported candidates whose round
    is not complete. votes_present is False when read_votes returned None;
    `continuing` is handed_on(votes), the candidates left to a verification run
    that did not complete. `refused` lists the findings the render refused,
    which the summary repeats under `refused_findings`.
    """
    raw_rounds = votes.get("rounds")
    rounds: JsonMap = raw_rounds if is_map(raw_rounds) else {}
    panels = [(f["id"], panel_complete(rounds.get(f["id"]))) for f in findings]
    incomplete = sorted(finding_id for finding_id, panel in panels if panel is None)
    reviewed = [panel for _, panel in panels if panel is not None]
    quorum = sum(panel["true"] >= PANEL_KEEP_QUORUM for panel in reviewed)
    reported = {f["id"] for f in findings}
    dropped_incomplete = sorted(
        round_id
        for round_id, record in rounds.items()
        if round_id not in reported and panel_complete(record) is None
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

    kind: str | None = None
    reason: str | None = None
    if not votes_present:
        kind = "no-vote-record"
        reason = (
            "votes.json is absent from the run directory or is not the scan workflow's record: "
            "the verification pipeline left no vote record, so nothing about this report can "
            "be attested"
        )
    elif "candidates" not in votes:
        kind = "no-candidate-count"
        reason = (
            "votes.json has no 'candidates' field: the vote record does not prove the pipeline "
            "ran, so nothing about this report can be attested"
        )
    elif dispatched and returned == 0:
        kind = "nothing-examined"
        reason = (
            f"{dispatched} research agent(s) were dispatched but none returned; the scan "
            "examined nothing"
        )
    elif incomplete:
        kind = "finding-panel-incomplete"
        reason = (
            f"these findings have no complete {PANEL_VOTER_COUNT}-voter panel round: "
            f"{', '.join(incomplete)}"
        )
    elif findings and quorum != len(findings):
        kind = "finding-below-quorum"
        reason = (
            f"{len(findings) - quorum} of {len(findings)} reported findings did not reach the "
            "keep quorum, so the report contains findings the panel rejected"
        )
    elif not findings and not rounds and candidates:
        kind = "candidates-not-paneled"
        reason = f"{candidates} candidates were recorded but none was paneled"
    elif not findings and rounds and not any(map(panel_complete, rounds.values())):
        kind = "no-panel-completed"
        reason = (
            f"{len(rounds)} panel round(s) were dispatched but none completed a full "
            f"{PANEL_VOTER_COUNT}-voter review; no candidate was actually verified"
        )
    elif dropped_incomplete:
        kind = "candidate-panel-incomplete"
        reason = (
            f"{len(dropped_incomplete)} candidate(s) were dropped without a complete "
            f"{PANEL_VOTER_COUNT}-voter panel round: {', '.join(dropped_incomplete)}"
        )
    elif continuing:
        kind = "continuation-incomplete"
        reason = continuation_text(continuing)
    refusals = list(refused)
    if refusals:
        names = ", ".join(record["id"] for record in refusals)
        refusal_reason = (
            f"{len(refusals)} finding(s) were refused at render and are absent "
            f"from this report: {names}"
        )
        reason = f"{reason}; {refusal_reason}" if reason else refusal_reason
        kind = kind or "findings-refused"
    summary: VerificationSummary = {
        "status": "verified" if reason is None else "unverified",
        "candidates": candidates,
        "candidates_deduped": as_count("candidates_deduped"),
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


def revision_tag(revision: object) -> str:
    """The stamp's filename tag: <sha12>[-dirty], or UNVERSIONED."""
    if not is_map(revision):
        msg = f"the run's revision {revision!r} is not an object, so it cannot name the stamp file"
        raise RenderError(msg)
    sha = revision.get("commit") or revision.get("head")
    if not sha:
        return "UNVERSIONED"
    if not is_str(sha) or not plugin.SHA_RE.match(sha):
        msg = f"the run's revision {sha!r} is not a hex commit id, so it cannot name the stamp file"
        raise RenderError(msg)
    return sha[:12] + ("" if revision.get("dirty") is False else "-dirty")


def scan_of(meta: JsonMap) -> Meta:
    """The scan meta the run records, every field shape-checked; a wrong one is a refusal."""
    scan_id = meta.get("scan_id")
    try:
        value = uuid.UUID(scan_id) if is_str(scan_id) else None
    except ValueError:
        value = None
    if value is None or value.version is None or not 1 <= value.version <= 5:
        msg = (
            f"scan-meta.json scan_id {scan_id!r} is not a version 1-5 UUID; "
            "rerun write_scan_meta.py to mint one"
        )
        raise RenderError(msg)
    mode = meta.get("mode")
    if not is_str(mode) or mode not in plugin.MODES:
        msg = f"scan-meta.json mode {mode!r} is not a scan mode; rerun write_scan_meta.py"
        raise RenderError(msg)
    scan_root = meta.get("scan_root")
    if not is_str(scan_root) or not scan_root.strip():
        msg = f"scan-meta.json scan_root {scan_root!r} is not a path; rerun write_scan_meta.py"
        raise RenderError(msg)
    prefix = meta.get("scan_prefix")
    if prefix is None:
        prefix = ""
    if not is_str(prefix) or not scan_prefix_shaped(prefix):
        msg = (
            f"scan-meta.json scan_prefix {prefix!r} is not a path prefix; rerun write_scan_meta.py"
        )
        raise RenderError(msg)
    remote = meta.get("remote")
    if remote is not None and (not is_str(remote) or not SANITIZED_REMOTE_RE.match(remote)):
        msg = (
            f"scan-meta.json remote {remote!r} is not a sanitized repository URL; "
            "rerun write_scan_meta.py"
        )
        raise RenderError(msg)
    scope = meta.get("scope", [])
    entries = [entry for entry in scope if is_str(entry)] if is_list(scope) else []
    if not is_list(scope) or len(entries) != len(scope):
        msg = (
            f"scan-meta.json scope {scope!r} is not the list of paths the scan covered; "
            "rerun write_scan_meta.py"
        )
        raise RenderError(msg)
    revision: object = meta.get("revision")
    if revision is None:
        revision = {}
    revision_source = meta.get("revision_source", "self-reported")
    if not is_str(revision_source):
        msg = (
            f"scan-meta.json revision_source {revision_source!r} does not name what vouches for "
            "the revision; rerun write_scan_meta.py"
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
    return Meta(scan, scan_root, revision, revision_source, meta.get("model"), meta.get("effort"))


def elapsed_seconds(started_at: object, now: datetime) -> int | None:
    """Whole seconds from scan-meta.json's started_at to now, floored at 0.

    None when started_at is absent, unparseable or timezone-naive.
    """
    if not is_str(started_at):
        return None
    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        return None
    return max(int((now - started).total_seconds()), 0) if started.tzinfo else None


def jsonl_text(findings: Sequence[Record]) -> str:
    """The findings as JSONL: one record per line as the products carry it, findings.json order."""
    return "".join(strictjson.text(secret.withheld(item)) + "\n" for item in findings)


def strength(finding: Finding) -> tuple[int, int]:
    """A finding's rank among those at one site: severity first, then confidence."""
    return -SEVERITIES.index(finding["severity"]), CONFIDENCES.index(finding["confidence"])


def one_per_site(findings: Sequence[Record], scan: sarif.Scan) -> tuple[list[Record], list[str]]:
    """The findings reduced to one per site, and one disclosure sentence per finding merged away.

    A site is a rule at a line of a file (sarif.site), which is what a result
    stands for to a SARIF or JSONL consumer, so the products carry one record
    for it: of the findings at one site the strongest is kept, the first of
    them in findings.json order when they tie, and each of the others is
    named in a sentence with the finding it was merged into. A finding with
    no site, one whose line was never determined, is kept as it is.
    """
    sites = [sarif.site(item, scan) for item in findings]
    by_site: dict[sarif.Site, list[Record]] = {}
    for item, where in zip(findings, sites):
        if where is not None:
            by_site.setdefault(where, []).append(item)
    kept = {where: max(group, key=strength) for where, group in by_site.items()}
    merged = [
        f"finding {other['id']} names the same site as finding {kept[where]['id']}, "
        f"{where.path}:{where.line} under rule {where.rule}; merged into it"
        for where, group in by_site.items()
        for other in group
        if other is not kept[where]
    ]
    unmerged = [
        item if where is None else kept[where]
        for item, where in zip(findings, sites)
        if where is None or item is by_site[where][0]
    ]
    return unmerged, merged


def unrecognized_cwes(findings: Sequence[Finding]) -> list[str]:
    """One disclosure sentence per finding whose declared CWE the pinned release does not define."""
    return [
        f"finding {item['id']} cwe_id {item['cwe_id']} is not a weakness in "
        f"CWE {cwe.catalog.version}; filed as Uncategorized"
        for item in findings
        if not cwe.catalog.defines(cwe.id_number(item["cwe_id"]))
    ]


def continuation_text(continuing: int) -> str:
    """The sentence the stamp's reason and the log's notification share for an unfinished chain."""
    return f"{continuing} candidate(s) were handed to a verification run that did not complete"


def notifications_of(
    shape: Mapping[str, object],
    research: ResearchCoverage | None,
    verification: VerificationSummary,
    merged: Sequence[str],
    unrecognized: Sequence[str],
    symlinks: Sequence[str],
    revision: object,
    continuing: int,
    refused: Sequence[_RefusalRecord],
) -> list[dict[str, object]]:
    """The invocation notifications: skipped, capped, merged, mislabeled, refused or unverified.

    `research` is research_coverage's. The sentences of `merged` (one_per_site)
    are disclosed at level note, those
    of `unrecognized` (unrecognized_cwes) at level warning. `symlinks` names
    the root-level symbolic links the scan's extent left out unfollowed;
    `continuing` is handed_on(votes); `refused` is the render's per-finding
    path refusals, each disclosed at level warning.
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
        text = f"Top-level directories the accepted partition left unaccounted: {names}"
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
        notes.append(note("coverage/unverified-by-cap", "warning", text))
    if dropped := verification["incomplete_panel_candidates"]:
        text = (
            f"{dropped} candidate(s) were dropped without a complete "
            f"{PANEL_VOTER_COUNT}-voter panel round"
        )
        notes.append(note("verification/incomplete-panel", "warning", text))
    if continuing:
        text = continuation_text(continuing)
        notes.append(note("verification/continuation-incomplete", "warning", text))
    notes += [note("finding/merged", "note", text) for text in merged]
    notes += [note("cwe/unrecognized", "warning", text) for text in unrecognized]
    notes += [
        note(
            "verification/refused-finding",
            "warning",
            f"Finding {record['id']} was refused at render and is absent from "
            f"this report: {record['reason']}",
        )
        for record in refused
    ]
    if verification["status"] == "unverified":
        notes.append(note("verification/unverified", "error", verification["reason"] or ""))
    return notes


def built_or_refused(
    raw: object,
    index: int,
    rounds_by_id: JsonMap,
    scan_root: str,
    scan_prefix: str,
    must_exist: bool,
) -> Finding | FindingPathError:
    """One finding carried, or the named path refusal that kept it out of the report."""
    try:
        return build_finding(raw, index, rounds_by_id, scan_root, scan_prefix, must_exist)
    except FindingPathError as error:
        return error


def render(run_dir: Path, products_dir: Path) -> Rendered:
    """Read the run's records, validate them, build every product, then write them, stamp last."""
    meta = read_json(run_dir, "scan-meta.json")
    if not is_map(meta):
        raise RenderError("scan-meta.json must be a JSON object")
    findings_in = read_json(run_dir, "findings.json")
    if not is_list(findings_in):
        raise RenderError("findings.json must be a JSON array (use [] for no findings)")
    coverage, coverage_source = read_coverage(run_dir)
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
    scan, scan_root, revision, revision_source, model, effort = scan_of(meta)
    tag = revision_tag(revision)

    outcomes = [
        built_or_refused(raw, i, rounds_by_id, scan_root, scan.prefix, scan.mode == "scan")
        for i, raw in enumerate(findings_in)
    ]
    built = [item for item in outcomes if not isinstance(item, FindingPathError)]
    path_errors = [item for item in outcomes if isinstance(item, FindingPathError)]
    refused: list[_RefusalRecord] = [
        {"id": item.finding_id, "reason": f"its file {item.wrong}"} for item in path_errors
    ]
    counted = Counter([f["id"] for f in built] + [record["id"] for record in refused])
    repeated = sorted(finding_id for finding_id, count in counted.items() if count > 1)
    if repeated:
        msg = f"findings.json uses these finding ids more than once: {', '.join(repeated)}"
        raise RenderError(msg)
    sources = {
        path: text
        for path in {f["file"] for f in built}
        if (text := source.read(scan_root, path)) is not None
    }
    refused_secrets = [e.snippet for e in path_errors if secret.is_credential_cwe(e.cwe)]
    records = sarif.placed(built, scan, sources, refused_secrets=refused_secrets)
    findings, merged = one_per_site(records, scan)

    markdown_path = run_dir / "CLAUDE-SECURITY-RESULTS.md"
    if not os.path.isfile(markdown_path):
        raise RenderError(
            "CLAUDE-SECURITY-RESULTS.md is missing. Write the human-readable "
            "report before running this script."
        )
    markdown = markdown_path.read_bytes()
    try:
        markdown.decode("utf-8")
    except UnicodeDecodeError as error:
        msg = f"CLAUDE-SECURITY-RESULTS.md is not valid UTF-8: {error}"
        raise RenderError(msg) from error

    counts = Counter(f["severity"] for f in findings)
    continuing = handed_on(votes)
    verification = verification_summary(
        findings,
        votes,
        votes_present=votes_raw is not None,
        continuing=continuing,
        refused=refused,
    )
    research = research_coverage(coverage.get("research") if coverage else None)
    shape = run_shape(coverage, coverage_source, effort, scan_root, research)
    generated = datetime.now(timezone.utc).replace(microsecond=0)
    stamp: dict[str, object] = {
        "generated_at": generated.isoformat(),
        "duration_s": elapsed_seconds(meta.get("started_at"), generated),
        "scan_id": str(scan.id),
        "mode": scan.mode,
        "scan_prefix": scan.prefix,
        "scope": list(scan.scope),
        "revision": revision,
        "revision_source": revision_source,
        "model": model,
        "effort": effort,
        "run_shape": shape,
        "findings": {
            "total": len(findings),
            "critical": counts["CRITICAL"],
            "high": counts["HIGH"],
            "medium": counts["MEDIUM"],
            "low": counts["LOW"],
        },
        "verification": verification,
    }

    jsonl = jsonl_text(findings)
    run_properties = {
        key: {k: v for k, v in value.items() if k not in STAMP_ONLY} if is_map(value) else value
        for key, value in stamp.items()
        if key not in STAMP_ONLY and (key != "model" or value is not None)
    }
    panels = {
        f["id"]: panel for f in findings if (panel := panel_complete(rounds_by_id.get(f["id"])))
    }
    unrecognized = unrecognized_cwes(findings)
    unfinished = [continuation_text(continuing)] if continuing else []
    refusal_lines = [f"refused {error.finding_id}: {error}" for error in path_errors]
    for text in merged + unrecognized + unfinished + refusal_lines:
        sys.stderr.write(f"render_report.py: {text}\n")
    symlinks = coverage_texts(meta.get("unfollowed_symlinks"), 200)
    notifications = notifications_of(
        shape, research, verification, merged, unrecognized, symlinks, revision, continuing, refused
    )
    sarif_log = sarif.log(findings, scan, plugin.version(), run_properties, panels, notifications)
    sarif_doc = strictjson.text(sarif_log, indent=2) + "\n"
    for stale in products_dir.iterdir():
        if stale.name.startswith(REVISION_PREFIX) and stale.suffix == ".json":
            stale.unlink()
    (products_dir / JSONL_NAME).write_bytes(jsonl.encode())
    (products_dir / SARIF_NAME).write_bytes(sarif_doc.encode())
    markdown_out = products_dir / "CLAUDE-SECURITY-RESULTS.md"
    # realpath, not Path.resolve(): on 3.9 for Windows resolve() raises on volumes realpath accepts.
    relocated = os.path.realpath(markdown_path) != os.path.realpath(markdown_out)
    if relocated:
        markdown_out.write_bytes(markdown)
    stamp_path = products_dir / f"{REVISION_PREFIX}{tag}.json"
    stamp_path.write_bytes((strictjson.text(stamp, indent=2) + "\n").encode())
    if relocated:
        markdown_path.unlink()

    return Rendered(findings, verification, tag)


def remove_run_dir(run_dir: Path, products_dir: Path) -> str:
    """Remove the scan's run directory once rendered; returns a one-line status."""
    # abspath folds ".." without following symlinks, so the check below sees this path's own name.
    target = Path(os.path.abspath(run_dir))
    if target.name != plugin.RUN_DIR_NAME:
        return f"kept {run_dir} (not a {plugin.RUN_DIR_NAME} run directory)"
    if os.path.realpath(target) == os.path.realpath(products_dir):
        return f"kept {run_dir} (it holds the products)"
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
        description="Render a scan's machine-readable artifacts from its run directory.",
        allow_abbrev=False,
    )
    parser.add_argument("run_dir", help="the run directory holding the scan's records")
    parser.add_argument(
        "--products-dir", help="where the products are written (default: the run directory)"
    )
    return parser


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
    except (RenderError, FindingError) as error:
        sys.stderr.write(f"render_report.py: {error}\n")
        return 1
    except OSError as error:
        sys.stderr.write(f"render_report.py: could not read or write the report's files: {error}\n")
        return 1
    removal = remove_run_dir(run_dir, products_dir)
    count = len(rendered.findings)
    stamp_name = f"{REVISION_PREFIX}{rendered.tag}.json"
    print(
        f"wrote {JSONL_NAME}, {SARIF_NAME} ({count} finding{'' if count == 1 else 's'}) "
        f"and {stamp_name} into {products_dir}"
    )
    print(f"stamp: {stamp_name}")
    print(f"verification.status: {rendered.verification['status']}")
    if reason := rendered.verification["reason"]:
        print(f"verification.reason: {reason}")
    print(removal)
    return 0


if __name__ == "__main__":
    console.tolerate_undecodable_names()
    sys.exit(main(sys.argv[1:]))
