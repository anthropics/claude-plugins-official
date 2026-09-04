#!/usr/bin/env python3
"""Record a scan workflow's result in its run directory and say what to do next.

Reads the JSON file the Claude Code runtime writes when a workflow task
completes, folds the result's findings, votes and coverage into
findings.json, votes.json and coverage.json in the run directory (appending
to an earlier run's when this result continues one), writes the candidate
files a further verification run loads, and prints one `next:` line: the
Workflow call that continues the verification, or the instruction to write
the report. Each finding is recorded at the line of its file that its quoted
code is on, with the line the researcher declared kept beside it.

Usage:
  save_result.py <output_file> <run_dir>

Exits 0 when the result is recorded or already was, 1 when it could not be
(the `next:` line still says what to do), 2 on a usage error.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

# The lib/ package lives next to this script. Python normally adds a script's own
# directory to the import path, but not under -P or PYTHONSAFEPATH, so we add it here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, plugin, source, strictjson
from lib.chain import Chain, chain_of, pending_ranks
from lib.finding import (
    CONFIDENCE_RANK,
    SEVERITIES,
    FindingError,
    file_field,
    line_number,
    scan_prefix_shaped,
)
from lib.strictjson import JsonMap, is_int, is_list, is_map, is_str

# Rows per candidate file; workflows/scan.js derives each file's ranks from the same number.
CHUNK = 25
UNACCOUNTED_ECHO_CAP = 40
CID_RE = re.compile(r"^C([1-9][0-9]*)\Z")
WRITE_REPORT = (
    "next: write CLAUDE-SECURITY-RESULTS.md from findings.json and coverage.json per the "
    "report spec, then run render_report.py"
)


class Records(NamedTuple):
    """A scan's three records and the chain its vote record carries."""

    findings: list[JsonMap]
    votes: JsonMap
    coverage: JsonMap
    chain: Chain


class Args(argparse.Namespace):
    """The parsed command line."""

    output_file: str = ""
    run_dir: str = ""


class NotAResultError(Exception):
    """The output file holds no scan result this script can fold; the message names why."""

    fallback: str = (
        "Write the result's findings, votes and coverage from the completion notice to "
        "findings.json, votes.json and coverage.json in the run directory yourself, then "
        + WRITE_REPORT[len("next: ") :]
    )


class CannotContinueError(Exception):
    """The run directory cannot take this result; the message names why."""

    fallback: str = "stop; nothing was recorded, so say so and name the report directory"


def count(record: JsonMap, key: str) -> int:
    """A count the workflow wrote; anything but a non-negative integer cannot be folded."""
    value = record.get(key)
    if not is_int(value) or value < 0:
        msg = f"{key!r} is {value!r}, not a count"
        raise CannotContinueError(msg)
    return value


def texts(record: JsonMap, key: str) -> list[object]:
    """A list the workflow wrote, empty when absent."""
    value = record.get(key)
    return list(value) if is_list(value) else []


def rank_of(row: JsonMap) -> int:
    """A candidate row's rank, from its `cid`."""
    cid = row.get("cid")
    matched = CID_RE.match(cid) if is_str(cid) else None
    if not matched:
        msg = f"a pending row's cid is {cid!r}, not C<rank>"
        raise NotAResultError(msg)
    return int(matched[1])


def scan_settings(run_dir: Path) -> JsonMap:
    """scan-meta.json from the run directory: the settings every run of this scan shares."""
    if run_dir.name != plugin.RUN_DIR_NAME:
        msg = f"{run_dir} is not a {plugin.RUN_DIR_NAME} run directory"
        raise CannotContinueError(msg)
    try:
        meta = strictjson.load(run_dir / "scan-meta.json")
    except (OSError, ValueError) as error:
        msg = f"scan-meta.json cannot be read from {run_dir}: {error}"
        raise CannotContinueError(msg) from error
    if not is_map(meta) or not is_str(meta.get("scan_root")):
        msg = "scan-meta.json names no scan_root"
        raise CannotContinueError(msg)
    return meta


def recorded(run_dir: Path) -> Records | None:
    """The scan's records as an earlier save left them; None before the first."""
    if not os.path.isfile(run_dir / "votes.json"):
        return None
    findings, votes, coverage = (
        strictjson.load(run_dir / name) for name in ("findings.json", "votes.json", "coverage.json")
    )
    if not is_list(findings) or not is_map(votes) or not is_map(coverage):
        msg = "the run directory's records are not the shapes this script wrote"
        raise CannotContinueError(msg)
    kept = [f for f in findings if is_map(f) and is_str(f.get("id"))]
    if len(kept) != len(findings):
        msg = "findings.json holds a finding without an id"
        raise CannotContinueError(msg)
    try:
        chain = chain_of(votes.get("chain"))
    except ValueError as error:
        msg = f"votes.json chain {error}"
        raise CannotContinueError(msg) from error
    return Records(kept, votes, coverage, chain)


def result_in(output_file: Path) -> JsonMap:
    """The `result` object the runtime wrote to the workflow's output file."""
    try:
        output = strictjson.load(output_file)
    except (OSError, ValueError) as error:
        msg = f"the output file cannot be read: {error}"
        raise NotAResultError(msg) from error
    result = output.get("result") if is_map(output) else None
    if not is_map(result):
        msg = "the output file holds no result object"
        raise NotAResultError(msg)
    return result


def records_in(result: JsonMap) -> tuple[Records, dict[int, JsonMap]]:
    """A run's records and its pending rows by rank, narrowed from its result."""
    raw, votes, coverage, pending = (
        result.get(key) for key in ("findings", "votes", "coverage", "pending")
    )
    findings = [f for f in raw if is_map(f) and is_str(f.get("id"))] if is_list(raw) else []
    if not is_list(raw) or len(findings) != len(raw):
        msg = "'findings' is not a list of findings with ids"
        raise NotAResultError(msg)
    if not is_map(votes) or votes.get("provenance") != plugin.VOTES_PROVENANCE:
        msg = "'votes' is not the scan workflow's vote record"
        raise NotAResultError(msg)
    if not is_map(coverage) or not is_str(coverage.get("effort")):
        msg = "'coverage' does not name the effort"
        raise NotAResultError(msg)
    if not is_list(pending):
        msg = "'pending' is not a list of candidate rows"
        raise NotAResultError(msg)
    try:
        chain = chain_of(votes.get("chain"))
    except ValueError as error:
        msg = f"'votes' chain {error}"
        raise NotAResultError(msg) from error

    rows = {rank_of(row): row for row in pending if is_map(row)}
    if len(rows) != len(pending) or sorted(rows) != pending_ranks(chain):
        msg = "'pending' rows are not the ranks the chain hands on"
        raise NotAResultError(msg)
    return Records(findings, votes, coverage, chain), rows


def ancestry(path: str) -> list[str]:
    """`path` and each directory above it, nearest last: a/b/c gives a, a/b, a/b/c."""
    parts = path.split("/")
    return ["/".join(parts[:depth]) for depth in range(1, len(parts) + 1)]


def checked(coverage: JsonMap, meta: JsonMap, run_dir: Path) -> JsonMap:
    """`coverage` carrying, under `research.tree`, its coverage accounts counted against the
    scan target's tracked files; `coverage` as given when the accounts are not checkable."""
    research = coverage.get("research")
    if not is_map(research) or research.get("checkable") is not True:
        return coverage
    listing = run_dir / plugin.TARGET_FILES_NAME
    try:
        listed = strictjson.load(listing)
    except (OSError, ValueError) as error:
        sys.stderr.write(f"save_result.py: coverage account not checked: {error}\n")
        return coverage
    if not is_list(listed):
        sys.stderr.write(f"save_result.py: coverage account not checked: {listing} is not a list\n")
        return coverage
    files = [path for path in listed if is_str(path)]
    names = {name for path in files for name in ancestry(path)}
    scan_prefix = str(meta.get("scan_prefix") or "")
    scan_root = str(meta.get("scan_root") or "").replace("\\", "/").strip("/") + "/"
    names.add("")

    def named(path: str) -> str:
        slashed = path.replace("\\", "/")
        folded = (
            (slashed + "/").removeprefix(root).strip("/") for root in (scan_prefix, scan_root)
        )
        return next((s for s in (path, slashed, *folded) if s in names), path)

    accounts = [account for account in texts(research, "components") if is_map(account)]
    inside = {named(p) for account in accounts for p in texts(account, "paths") if is_str(p)}
    read = {named(p) for account in accounts for p in texts(account, "filesRead") if is_str(p)}
    declared = (e.get("path") for a in accounts for e in texts(a, "notReached") if is_map(e))
    missed = {named(p) for p in declared if is_str(p)}
    assigned = [f for f in files if not inside.isdisjoint(["", *ancestry(f)])]
    unread = [f for f in assigned if f not in read]
    unaccounted = [f for f in unread if missed.isdisjoint(["", *ancestry(f)])]
    tree = {
        "files": len(assigned),
        "read": len(assigned) - len(unread),
        "notReached": len(unread) - len(unaccounted),
        "unaccounted": len(unaccounted),
        "unaccountedPaths": unaccounted[:UNACCOUNTED_ECHO_CAP],
        "outsideComponents": len(files) - len(assigned),
    }
    return {**coverage, "research": {**research, "tree": tree}}


def placed(finding: JsonMap, meta: JsonMap) -> JsonMap:
    """`finding` at the line of its file that its quoted snippet is on, its declared line kept.

    `line` becomes the line of the finding's file under the scan root that
    places it (source.placed_line) and the line as it arrived moves to
    `declared_line`; both hold the arriving line when the file cannot be
    read or nothing in it places the finding. A finding whose line or snippet
    is not a shape the render accepts is returned as it is.
    """
    finding_id, line, snippet = (
        finding["id"],
        line_number(finding.get("line")),
        finding.get("snippet"),
    )
    scan_root, prefix = meta.get("scan_root"), meta.get("scan_prefix") or ""
    if (
        line is None
        or not (snippet is None or is_str(snippet))
        or not is_str(finding_id)
        or not is_str(scan_root)
        or not is_str(prefix)
        or not scan_prefix_shaped(prefix)
    ):
        return finding
    try:
        file = file_field(finding, finding_id, scan_root, prefix, meta.get("mode") == "scan")
        text = source.read(scan_root, file)
    except FindingError:
        text = None
    return {**finding, "line": source.placed_line(text, line, snippet or ""), "declared_line": line}


def report_order(finding: JsonMap) -> tuple[int, int]:
    """Sort key: severity, then confidence, strongest first; unknown values last."""
    severity = str(finding.get("severity", "")).upper()
    confidence = str(finding.get("confidence", "")).lower()
    return (
        SEVERITIES.index(severity) if severity in SEVERITIES else len(SEVERITIES),
        -CONFIDENCE_RANK.get(confidence, 0),
    )


def merged(scan: Records, run: Records) -> Records:
    """The scan's records with one further verification run folded in."""
    handed = pending_ranks(scan.chain)
    if run.chain["shard"] != scan.chain["shard"] + 1:
        msg = (
            f"this is run {run.chain['shard']} but run {scan.chain['shard']} was the last recorded"
        )
        raise CannotContinueError(msg)
    if run.coverage.get("received") != len(handed):
        received = run.coverage.get("received")
        msg = f"the run was handed {received!r} candidates, not the {len(handed)} pending"
        raise CannotContinueError(msg)
    if run.coverage.get("effort") != scan.coverage.get("effort"):
        msg = "the run's effort is not the scan's"
        raise CannotContinueError(msg)

    findings = scan.findings + [f for f in run.findings if f not in scan.findings]
    ids = [f["id"] for f in findings]
    if len(ids) != len(set(ids)):
        msg = "the run reuses a finding id the scan already has"
        raise CannotContinueError(msg)

    scan_rounds, run_rounds = scan.votes.get("rounds"), run.votes.get("rounds")
    if not is_map(scan_rounds) or not is_map(run_rounds):
        msg = "'rounds' is not an object"
        raise CannotContinueError(msg)
    repanelled = {r.get("candidate") for r in run_rounds.values() if is_map(r)}
    rounds = {
        rid: r
        for rid, r in scan_rounds.items()
        if not (is_map(r) and r.get("continued") is True and r.get("candidate") in repanelled)
    }
    if rounds.keys() & run_rounds.keys():
        msg = "the run reuses a round id the scan already has"
        raise CannotContinueError(msg)

    votes = {
        **scan.votes,
        "panel_votes": count(scan.votes, "panel_votes") + count(run.votes, "panel_votes"),
        "unreviewed_candidate_sites": count(scan.votes, "unreviewed_candidate_sites")
        - len(handed)
        + count(run.votes, "unreviewed_candidate_sites"),
        "rounds": {**rounds, **run_rounds},
        "chain": run.chain,
    }
    coverage = (
        scan.coverage
        if scan.coverage.get("verificationRun") == run.chain["shard"]
        else {
            **scan.coverage,
            "adversarialCasualties": texts(scan.coverage, "adversarialCasualties")
            + texts(run.coverage, "adversarialCasualties"),
            "lostCandidates": texts(scan.coverage, "lostCandidates")
            + texts(run.coverage, "lostCandidates"),
            "severityLowered": texts(scan.coverage, "severityLowered")
            + texts(run.coverage, "severityLowered"),
            "dispatchRefusals": count(scan.coverage, "dispatchRefusals")
            + count(run.coverage, "dispatchRefusals"),
            "continued": run.coverage.get("continued"),
            "verificationRun": run.chain["shard"],
        }
    )
    return Records(sorted(findings, key=report_order), votes, coverage, run.chain)


def write_json(run_dir: Path, name: str, value: object, indent: int = 2) -> None:
    """Write one record through a temporary name, so it is never seen half-written."""
    partial = run_dir / f"{name}.partial"
    partial.write_bytes((strictjson.text(value, indent=indent) + "\n").encode())
    partial.replace(run_dir / name)


def write_records(run_dir: Path, records: Records, rows: dict[int, JsonMap]) -> None:
    """The three records and the next run's candidate files; votes.json last."""
    write_json(run_dir, "findings.json", records.findings)
    write_json(run_dir, "coverage.json", records.coverage)
    shard = records.chain["shard"] + 1
    ranks = sorted(rows)
    for number, start in enumerate(range(0, len(ranks), CHUNK), start=1):
        chunk = {
            "runDir": str(run_dir),
            "shard": shard,
            "chunk": number,
            "candidates": [rows[rank] for rank in ranks[start : start + CHUNK]],
        }
        write_json(run_dir, f"candidates.{shard}.{number}.json", chunk, indent=1)
    write_json(run_dir, "votes.json", records.votes)


def summary(records: Records) -> str:
    """One line on where the scan stands."""
    rounds = records.votes.get("rounds")
    return (
        f"recorded verification run {records.chain['shard']}: {len(records.findings)} findings, "
        f"{len(rounds) if is_map(rounds) else 0} rounds, "
        f"{len(pending_ranks(records.chain))} pending, "
        f"{len(texts(records.coverage, 'lostCandidates'))} lost"
    )


def next_step(run_dir: Path, meta: JsonMap, chain: Chain) -> str:
    """The `next:` line: the Workflow call that panels what is pending, or the report."""
    if not pending_ranks(chain):
        return WRITE_REPORT
    args = {
        "scanRoot": meta.get("scan_root"),
        "runDir": str(run_dir),
        "mode": meta.get("mode"),
        "effort": meta.get("effort"),
        "verify": {
            "shard": chain["shard"] + 1,
            "idBase": chain["next_id"],
            "pending": chain["pending"],
            "retry": chain["retry"],
        },
    }
    return (
        "next: make this Workflow call exactly as printed, wait for it with keep-waiting.sh "
        "as before, then run save_result.py on its output file\n"
        f'Workflow({{ name: "claude-security:scan", args: {strictjson.text(args)} }})'
    )


def otherwise(run_dir: Path, fallback: str) -> str:
    """The `next:` line when this result could not be recorded."""
    if os.path.isfile(run_dir / "votes.json"):
        return WRITE_REPORT + "; its stamp will name what was not verified"
    return f"next: {fallback}"


def standing(run_dir: Path, meta: JsonMap, scan: Records | None, result: JsonMap) -> Records:
    """The scan's records once `result` is taken into account, written if that changed them.

    `meta` is the scan's settings (scan_settings), which placing a finding reads.
    """
    if result.get("started") is False:
        if scan is None:
            msg = "the workflow did not accept its settings, so no scan ran"
            raise CannotContinueError(msg)
        return scan
    run, rows = records_in(result)
    made_for = result.get("runDir")
    if not is_str(made_for) or os.path.abspath(made_for) != str(run_dir):
        msg = f"the result names {made_for!r} as its run directory, not this one"
        raise CannotContinueError(msg)
    if scan is None and run.chain["shard"] != 1:
        msg = f"this is run {run.chain['shard']} but nothing is recorded yet"
        raise CannotContinueError(msg)
    if scan is not None and run.chain["shard"] <= scan.chain["shard"]:
        return scan
    run = run._replace(
        findings=[placed(item, meta) for item in run.findings],
        coverage=checked(run.coverage, meta, run_dir),
    )
    records = run if scan is None else merged(scan, run)
    write_records(run_dir, records, rows)
    return records


def save(output_file: Path, run_dir: Path) -> None:
    """Fold the result into the run directory and print where the scan stands."""
    meta = scan_settings(run_dir)
    records = standing(run_dir, meta, recorded(run_dir), result_in(output_file))
    print(summary(records))
    print(next_step(run_dir, meta, records.chain))


def argument_parser() -> argparse.ArgumentParser:
    """The command line: the workflow's output file and the scan's run directory."""
    parser = argparse.ArgumentParser(
        prog="save_result.py",
        description="Record a scan workflow's result in its run directory and say what to do next.",
        allow_abbrev=False,
    )
    parser.add_argument("output_file", help="the file the workflow's completion notice names")
    parser.add_argument("run_dir", help="the scan's run directory")
    return parser


def main(argv: list[str]) -> int:
    args = argument_parser().parse_args(argv, namespace=Args())
    output_file = Path(os.path.abspath(args.output_file))
    # abspath folds ".." without following symlinks, so later checks see this path's own name.
    run_dir = Path(os.path.abspath(args.run_dir))
    try:
        save(output_file, run_dir)
    except (NotAResultError, CannotContinueError) as error:
        sys.stderr.write(f"save_result.py: {error}\n")
        print(otherwise(run_dir, error.fallback))
        return 1
    except (OSError, ValueError) as error:
        sys.stderr.write(f"save_result.py: could not read or write the run's files: {error}\n")
        print(otherwise(run_dir, CannotContinueError.fallback))
        return 1
    return 0


if __name__ == "__main__":
    console.tolerate_undecodable_names()
    sys.exit(main(sys.argv[1:]))
