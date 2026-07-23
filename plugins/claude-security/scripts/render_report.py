#!/usr/bin/env python3
"""Render a scan's machine-readable artifacts from its run directory.

Writes CLAUDE-SECURITY-RESULTS.jsonl (one finding per line, fields in a fixed
order) and the CLAUDE-SECURITY-REVISION-<tag>.json stamp, places the report
markdown beside them, then removes the scan's run directory now that its
records are rendered. Filenames, JSONL field order, and verification.status
semantics are stable across releases.

Usage: render_report.py <run-dir> [--products-dir <dir>]
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import NoReturn, TypedDict, cast

JsonMap = Mapping[str, object]
Finding = dict[str, object]


class Panel(TypedDict, total=False):
    """A validated panel round: an int vote count and the fixed voter count."""

    true: int
    false: int
    voters: int


class VerificationSummary(TypedDict, total=False):
    """The stamp's `verification` object; every path names why if not verified."""

    status: str
    candidates: int
    candidates_deduped: int
    panel_votes: int
    panel_reviewed_findings: int
    panel_quorum_findings: int
    unreviewed_candidate_sites: object
    attested_findings: int
    reason: str | None
    researchers_dispatched: int
    researchers_returned: int


REPORT_FIELDS = (
    "id",
    "title",
    "impact",
    "file",
    "line",
    "description",
    "exploit_scenario",
    "preconditions",
    "category",
    "severity",
    "confidence",
    "recommendation",
    "cwe_id",
    "snippet",
    "symbol",
)

SEPARATOR_ESCAPES = {0x85: "\\u0085", 0x2028: "\\u2028", 0x2029: "\\u2029"}

SEVERITIES = ("HIGH", "MEDIUM", "LOW")
CONFIDENCES = ("low", "medium", "high")
CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}

PANEL_VOTER_COUNT = 3
PANEL_KEEP_QUORUM = 2

REVISION_PREFIX = "CLAUDE-SECURITY-REVISION-"
RUN_DIR_NAME = ".claude-security-run"
# \Z, not $: `$` also matches before a trailing newline, and this names a file.
HEX_RE = re.compile(r"^[0-9a-fA-F]{7,64}\Z")
FINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")

CATEGORY_ALIASES = {
    "sqli": "sql-injection",
    "sql injection": "sql-injection",
    "rce": "command-injection",
    "command execution": "command-injection",
    "cmdi": "command-injection",
    "xss": "xss",
    "cross-site scripting": "xss",
    "csrf": "csrf",
    "cross-site request forgery": "csrf",
    "ssrf": "ssrf",
    "path traversal": "path-traversal",
    "directory traversal": "path-traversal",
    "idor": "idor",
    "authz bypass": "improper-authorization",
    "authn bypass": "auth-bypass",
    "hardcoded credentials": "hardcoded-secret",
    "hardcoded password": "hardcoded-secret",
    "secret": "hardcoded-secret",
    "weak cryptography": "weak-crypto",
    "insecure randomness": "weak-randomness",
    "uaf": "use-after-free",
    "oob read": "out-of-bounds-read",
    "oob write": "out-of-bounds-write",
    "denial of service": "dos",
    "prototype pollution": "prototype-pollution",
}


class RenderError(Exception):
    """A refusal; the message names what the caller must fix."""


def as_map(value: object) -> JsonMap | None:
    """The value as a str-keyed mapping, or None when it is not one."""
    if isinstance(value, dict):
        return cast("JsonMap", value)
    return None


def die(message: str) -> NoReturn:
    sys.stderr.write(f"render_report.py: {message}\n")
    sys.exit(1)


def read_json(run_dir: str, name: str, required: bool = True) -> object:
    path = os.path.join(run_dir, name)
    try:
        with open(path, encoding="utf-8") as handle:
            return cast("object", json.load(handle))
    except OSError as error:
        if required:
            msg = f"{name} is missing from the run directory. Write it before running this script."
            raise RenderError(msg) from error
        return None
    except ValueError as error:
        msg = f"{name} is not valid JSON: {error}"
        raise RenderError(msg) from error


def normalize_category(raw: object) -> str:
    """Lowercase/slugify a category and fold known synonyms."""
    text = str(raw or "").strip().lower()
    if text in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[text]
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return CATEGORY_ALIASES.get(slug, slug)


def confidence_value(raw: object) -> str:
    """A finding's stated confidence, normalized to low|medium|high; refuses others."""
    if isinstance(raw, str):
        word = raw.strip().lower()
        if word in CONFIDENCE_RANK:
            return word
    msg = "confidence {!r} is not one of {}".format(raw, "/".join(CONFIDENCES))
    raise RenderError(msg)


def panel_complete(record: object) -> Panel | None:
    """The validated panel dict for one round record, or None.

    A complete panel has `voters` equal to PANEL_VOTER_COUNT and an integer
    `true` vote count.
    """
    round_record = as_map(record)
    if round_record is None:
        return None
    panel = as_map(round_record.get("panel"))
    if panel is None:
        return None
    panel_true = panel.get("true")
    if not isinstance(panel_true, int) or isinstance(panel_true, bool):
        return None
    if panel.get("voters") != PANEL_VOTER_COUNT:
        return None
    panel_false = panel.get("false")
    return {
        "true": panel_true,
        "false": panel_false if isinstance(panel_false, int) else 0,
        "voters": PANEL_VOTER_COUNT,
    }


def vote_confidence_ceiling(rounds: object) -> str | None:
    """The vote-backed confidence ceiling for one finding, or None.

    A unanimous panel yields `high`; a keep quorum below unanimity yields
    `medium`. None means no usable vote record.
    """
    panel = panel_complete(rounds)
    if panel is None:
        return None
    return "high" if panel.get("true", 0) >= PANEL_VOTER_COUNT else "medium"


def build_finding(raw: object, index: int, rounds_by_id: JsonMap) -> Finding:
    """Validate one finding into exactly REPORT_FIELDS, in order."""
    item = as_map(raw)
    if item is None:
        msg = f"findings.json item {index} is not an object"
        raise RenderError(msg)
    finding_id = str(item.get("id") or f"F{index + 1}")
    if not FINDING_ID_RE.match(finding_id):
        msg = f"finding id {finding_id!r} is not a valid id"
        raise RenderError(msg)

    for required in ("title", "file", "description", "exploit_scenario"):
        if not item.get(required):
            msg = f"finding {finding_id} is missing required field {required!r}"
            raise RenderError(msg)

    severity = str(item.get("severity", "")).strip().upper()
    if severity not in SEVERITIES:
        msg = "finding {} severity {!r} is not one of {}".format(
            finding_id, item.get("severity"), "/".join(SEVERITIES)
        )
        raise RenderError(msg)

    confidence = confidence_value(item.get("confidence"))
    ceiling = vote_confidence_ceiling(rounds_by_id.get(finding_id))
    if ceiling is not None and CONFIDENCE_RANK[confidence] > CONFIDENCE_RANK[ceiling]:
        confidence = ceiling

    raw_line = item.get("line", 0)
    try:
        line = int(raw_line) if isinstance(raw_line, (int, float, str)) else int(str(raw_line))
    except (TypeError, ValueError, OverflowError) as error:
        msg = "finding {} line {!r} is not an integer".format(finding_id, item.get("line"))
        raise RenderError(msg) from error

    preconditions_raw: object = item.get("preconditions") or []
    if not isinstance(preconditions_raw, list):
        msg = f"finding {finding_id} preconditions must be a list"
        raise RenderError(msg)

    cwe = item.get("cwe_id")
    if cwe:
        text = str(cwe).strip().upper().replace("_", "-")
        if re.match(r"^\d{1,5}$", text):
            text = "CWE-" + text
        cwe = text if re.match(r"^CWE-\d{1,5}$", text) else None
    else:
        cwe = None

    finding = {
        "id": finding_id,
        "title": item.get("title"),
        "impact": item.get("impact") or "",
        "file": item.get("file"),
        "line": line,
        "description": item.get("description"),
        "exploit_scenario": item.get("exploit_scenario"),
        "preconditions": [str(p) for p in cast("list[object]", preconditions_raw)],
        "category": normalize_category(item.get("category")),
        "severity": severity,
        "confidence": confidence,
        "recommendation": item.get("recommendation") or "",
        "cwe_id": cwe,
        "snippet": item.get("snippet") or "",
        "symbol": item.get("symbol") or "",
    }
    return {k: finding[k] for k in REPORT_FIELDS}


def read_coverage(run_dir: str) -> tuple[JsonMap | None, str]:
    """The optional coverage.json for the informational run_shape field.

    Returns (map_or_None, source): source is "coverage.json" when the file
    is a usable object, "unavailable" when it is absent, and "unreadable" when
    it exists but is not a usable object.
    """
    name = "coverage.json"
    try:
        raw = read_json(run_dir, name, required=False)
    except RenderError:
        return None, "unreadable"
    if raw is None:
        present = os.path.exists(os.path.join(run_dir, name))
        return None, ("unreadable" if present else "unavailable")
    cov = as_map(raw)
    if cov is None:
        return None, "unreadable"
    return cov, name


COVERAGE_TEXT_CAP = 300


def coverage_text(value: object, cap: int = COVERAGE_TEXT_CAP) -> str | None:
    """A coverage string, trimmed to `cap`, or None when the value is not a string."""
    if not isinstance(value, str):
        return None
    if len(value) > cap:
        return value[:cap] + f"...[+{len(value) - cap} chars]"
    return value


def skipped_components(raw: object) -> list[dict[str, object]] | None:
    """coverage.skippedComponents as [{name, paths, reason}], or None when unusable."""
    if not isinstance(raw, list):
        return None
    out: list[dict[str, object]] = []
    for entry in cast("list[object]", raw):
        item = as_map(entry)
        if item is None:
            continue
        paths_raw = item.get("paths")
        paths_in: list[object] = (
            cast("list[object]", paths_raw) if isinstance(paths_raw, list) else []
        )
        paths = [text for text in (coverage_text(p, 200) for p in paths_in) if text]
        out.append({
            "name": coverage_text(item.get("name"), 100) or "",
            "paths": paths,
            "reason": coverage_text(item.get("reason")) or "",
        })
    return out


def coverage_enum(value: object, allowed: tuple[str, ...]) -> str | None:
    """A coverage enum field, or None when absent or not one of the known values."""
    return value if isinstance(value, str) and value in allowed else None


def run_shape(coverage: JsonMap | None, source: str, effort: object) -> dict[str, object]:
    """What shape actually ran, distinct from the effort tier that was asked."""
    shape: dict[str, object] = {"requested_effort": effort, "collapsed": None, "source": source}
    if coverage is None:
        return shape
    shape["collapsed"] = coverage.get("collapsed")
    shape["diff_files"] = coverage.get("diffFiles")
    shape["diff_lines"] = coverage.get("diffLines")
    shape["scope_files"] = coverage.get("scopeFiles")
    shape["empty_diff"] = bool(coverage.get("emptyDiff"))
    shape["empty_scope"] = bool(coverage.get("emptyScope"))
    shape["researchers_dispatched"] = coverage.get("researchersDispatched")
    shape["skipped_components"] = skipped_components(coverage.get("skippedComponents"))
    shape["completeness_check_outcome"] = coverage_enum(
        coverage.get("completenessCheckOutcome"),
        ("checked", "partial", "not-checkable", "not-applicable"),
    )
    unaccounted_raw = coverage.get("unaccountedTopLevelDirs")
    unaccounted_in: list[object] = (
        cast("list[object]", unaccounted_raw) if isinstance(unaccounted_raw, list) else []
    )
    shape["unaccounted_top_level_dirs"] = [
        text for text in (coverage_text(x, 200) for x in unaccounted_in) if text
    ]
    shape["inventory_fallback"] = coverage_enum(
        coverage.get("inventoryFallback"),
        ("inventory-failed", "empty-partition", "incomplete-partition"),
    )
    top_count = coverage.get("topLevelCount")
    shape["top_level_dir_count"] = (
        top_count if isinstance(top_count, int) and not isinstance(top_count, bool) else None
    )
    return shape


def verification_summary(
    findings: list[Finding],
    votes: JsonMap,
    votes_present: bool = True,
) -> VerificationSummary:
    """Compute the stamp's verification object from the vote record.

    status is 'verified' only when the vote record proves the panel ran for
    every finding the report contains; otherwise 'unverified' with a `reason`.
    votes_present is False when votes.json was absent from the run directory.
    """
    rounds = as_map(votes.get("rounds")) or {}
    panel_reviewed = 0
    panel_quorum = 0
    incomplete: list[str] = []

    for finding in findings:
        finding_id = str(finding.get("id", ""))
        panel = panel_complete(rounds.get(finding_id))
        if panel is None:
            incomplete.append(finding_id)
            continue
        panel_reviewed += 1
        if panel.get("true", 0) >= PANEL_KEEP_QUORUM:
            panel_quorum += 1

    def as_count(key: str) -> int:
        """A vote count as a non-negative int; a wrong shape is a refusal."""
        value = votes.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            msg = (
                f"votes.json field {key!r} is not a non-negative integer ({value!r}); the "
                "vote record is malformed"
            )
            raise RenderError(msg)
        return value

    def optional_count(key: str) -> int | None:
        """A count that may be absent: None when so, else as_count's contract."""
        if key not in votes:
            return None
        return as_count(key)

    candidates_recorded = "candidates" in votes
    researchers_dispatched = optional_count("researchers_dispatched")
    researchers_returned = optional_count("researchers_returned")

    summary: dict[str, object] = {
        "status": "verified",
        "candidates": as_count("candidates"),
        "candidates_deduped": as_count("candidates_deduped"),
        "panel_votes": as_count("panel_votes"),
        "panel_reviewed_findings": panel_reviewed,
        "panel_quorum_findings": panel_quorum,
        "unreviewed_candidate_sites": as_count("unreviewed_candidate_sites"),
        "attested_findings": 0,
        "reason": None,
    }
    if researchers_dispatched is not None:
        summary["researchers_dispatched"] = researchers_dispatched
    if researchers_returned is not None:
        summary["researchers_returned"] = researchers_returned

    reportable: list[Finding] = findings
    if not votes_present:
        summary["status"] = "unverified"
        summary["reason"] = (
            "votes.json is absent from the run directory: the verification "
            "pipeline left no vote record, so nothing about this report can be "
            "attested"
        )
    elif not candidates_recorded:
        summary["status"] = "unverified"
        summary["reason"] = (
            "votes.json has no 'candidates' field: the vote record does not "
            "prove the pipeline ran, so nothing about this report can be attested"
        )
    elif researchers_dispatched and researchers_returned == 0:
        summary["status"] = "unverified"
        summary["reason"] = (
            f"{researchers_dispatched} research agent(s) were dispatched but none returned; "
            "the scan examined nothing"
        )
    elif incomplete:
        summary["status"] = "unverified"
        summary["reason"] = (
            f"these findings have no complete {PANEL_VOTER_COUNT}-voter panel round: "
            f"{', '.join(sorted(incomplete))}"
        )
    elif reportable and panel_quorum != len(reportable):
        summary["status"] = "unverified"
        summary["reason"] = (
            f"{len(reportable) - panel_quorum} of {len(reportable)} reported findings did not "
            "reach the keep quorum, so the report contains findings the panel rejected"
        )
    elif not findings and not votes.get("rounds") and summary["candidates"]:
        summary["status"] = "unverified"
        summary["reason"] = f"{summary['candidates']} candidates were recorded but none was paneled"
    elif not findings and rounds and not any(panel_complete(record) for record in rounds.values()):
        summary["status"] = "unverified"
        summary["reason"] = (
            f"{len(rounds)} panel round(s) were dispatched but none completed a full "
            f"{PANEL_VOTER_COUNT}-voter review; no candidate was actually verified"
        )
    return cast("VerificationSummary", cast("object", summary))


def revision_tag(revision: object) -> str:
    """The stamp's filename tag: <sha12>[-dirty], or UNVERSIONED."""
    rev = as_map(revision) or {}
    sha = rev.get("commit") or rev.get("head")
    if not sha:
        return "UNVERSIONED"
    if not (isinstance(sha, str) and HEX_RE.match(sha)):
        msg = f"the run's revision {sha!r} is not a hex commit id, so it cannot name the stamp file"
        raise RenderError(msg)
    return sha[:12] + ("" if rev.get("dirty") is False else "-dirty")


def atomic_write(path: str, text: str) -> None:
    """Write `text` atomically: a temp file in the same directory, then replace."""
    directory = os.path.dirname(path)
    handle, temp = tempfile.mkstemp(dir=directory, prefix=".render.")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp)
        raise


def jsonl_line(finding: Finding) -> str:
    """One finding, fixed field order, separators escaped."""
    text = json.dumps(finding, ensure_ascii=False, sort_keys=False)
    return text.translate(SEPARATOR_ESCAPES)


def render(run_dir: str, products_dir: str) -> tuple[list[Finding], VerificationSummary, str]:
    meta_raw = read_json(run_dir, "scan-meta.json")
    findings_raw = read_json(run_dir, "findings.json")
    votes: object = read_json(run_dir, "votes.json", required=False)
    coverage, coverage_source = read_coverage(run_dir)
    votes_present = votes is not None
    if votes is None:
        votes = {}

    if not isinstance(findings_raw, list):
        raise RenderError("findings.json must be a JSON array (use [] for no findings)")
    meta = as_map(meta_raw)
    if meta is None:
        raise RenderError("scan-meta.json must be a JSON object")
    votes_map = as_map(votes)
    if votes_map is None:
        raise RenderError("votes.json must be a JSON object mapping the vote record")
    rounds_raw = votes_map.get("rounds")
    rounds_by_id: JsonMap = {} if rounds_raw is None else (as_map(rounds_raw) or {})
    if rounds_raw is not None and not isinstance(rounds_raw, dict):
        kind = type(rounds_raw).__name__
        msg = f"votes.json 'rounds' must be an object keyed by finding id, not {kind}"
        raise RenderError(msg)
    findings = [
        build_finding(raw, i, rounds_by_id)
        for i, raw in enumerate(cast("list[object]", findings_raw))
    ]

    seen = {}
    for finding in findings:
        if finding["id"] in seen:
            msg = "finding id {!r} appears twice in findings.json".format(finding["id"])
            raise RenderError(msg)
        seen[finding["id"]] = True

    markdown_path = os.path.join(run_dir, "CLAUDE-SECURITY-RESULTS.md")
    if not os.path.isfile(markdown_path):
        raise RenderError(
            "CLAUDE-SECURITY-RESULTS.md is missing. Write the human-readable "
            "report before running this script."
        )
    with open(markdown_path, encoding="utf-8", newline="") as handle:
        markdown = handle.read()

    counts: dict[str, int] = dict.fromkeys(SEVERITIES, 0)
    for finding in findings:
        counts[str(finding.get("severity", ""))] += 1

    verification = verification_summary(findings, votes_map, votes_present=votes_present)
    revision: object = meta.get("revision") or {}
    tag = revision_tag(revision)

    atomic_write(
        os.path.join(products_dir, "CLAUDE-SECURITY-RESULTS.jsonl"),
        "".join(jsonl_line(f) + "\n" for f in findings),
    )
    markdown_out = os.path.join(products_dir, "CLAUDE-SECURITY-RESULTS.md")
    if os.path.realpath(markdown_path) != os.path.realpath(markdown_out):
        atomic_write(markdown_out, markdown)
        os.unlink(markdown_path)

    stamp: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scan_root": meta.get("scan_root"),
        "products_dir": products_dir,
        "mode": meta.get("mode"),
        "scope": meta.get("scope") or [],
        "revision": revision,
        "revision_source": meta.get("revision_source") or "self-reported",
        "model": meta.get("model"),
        "effort": meta.get("effort"),
        "run_shape": run_shape(coverage, coverage_source, meta.get("effort")),
        "findings": {
            "total": len(findings),
            "high": counts["HIGH"],
            "medium": counts["MEDIUM"],
            "low": counts["LOW"],
        },
        "verification": verification,
    }
    for stale in os.listdir(products_dir):
        if stale.startswith(REVISION_PREFIX) and stale.endswith(".json"):
            os.unlink(os.path.join(products_dir, stale))
    atomic_write(
        os.path.join(products_dir, f"{REVISION_PREFIX}{tag}.json"),
        json.dumps(stamp, indent=2) + "\n",
    )

    return findings, verification, tag


def remove_run_dir(run_dir: str, products_dir: str) -> str:
    """Remove the scan's run directory once rendered; returns a one-line status."""
    target = os.path.normpath(os.path.abspath(run_dir))
    if os.path.basename(target) != RUN_DIR_NAME:
        return f"kept {run_dir} (not a {RUN_DIR_NAME} run directory)"
    if os.path.realpath(target) == os.path.realpath(products_dir):
        return f"kept {run_dir} (it holds the products)"
    try:
        shutil.rmtree(target)
    except OSError as error:
        detail = error.args[0] if error.args else error
        return f"WARNING: could not remove run directory {run_dir}: {detail}"
    return f"removed run directory {run_dir}"


def main(argv: list[str]) -> int:
    products_dir: str | None = None
    args = list(argv)
    if len(args) == 3 and args[1] == "--products-dir":
        products_dir = args.pop(2)
        args.pop(1)
    if len(args) != 1:
        die("usage: render_report.py <run-dir> [--products-dir <dir>]")
    run_dir = args[0]
    if not os.path.isdir(run_dir):
        die(f"not a directory: {run_dir}")
    products_dir = products_dir or run_dir
    if not os.path.isdir(products_dir):
        die(f"products directory is not a directory: {products_dir}")
    try:
        findings, verification, tag = render(run_dir, products_dir)
    except RenderError as error:
        die(str(error))
    except OSError as error:
        die(f"could not read or write the report's files: {error}")
    removal = remove_run_dir(run_dir, products_dir)
    print(
        f"wrote CLAUDE-SECURITY-RESULTS.jsonl ({len(findings)} finding"
        f"{'' if len(findings) == 1 else 's'}) and {REVISION_PREFIX}{tag}.json "
        f"into {products_dir}"
    )
    print(f"stamp: {REVISION_PREFIX}{tag}.json")
    print(f"verification.status: {verification.get('status')}")
    reason = verification.get("reason")
    if reason:
        print(f"verification.reason: {reason}")
    print(removal)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
