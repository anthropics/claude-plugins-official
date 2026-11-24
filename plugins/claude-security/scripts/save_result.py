#!/usr/bin/env python3
"""Record a scan workflow's result in its run directory and say what to do next.

Reads the JSON file the Claude Code runtime writes when a workflow task
completes, folds the result's findings, votes and coverage into
findings.json, votes.json and coverage.json in the run directory (appending
to an earlier run's when this result continues one), copies a large findings.json
or coverage.json to numbered parts beside it (write_parts), writes the candidate
files a further verification run loads (and, at Change Scan Effort high,
reports-behind.json: see folded), lists those candidates, up to a cap,
under `waiting` in coverage.json, and prints a summary line with the
count at each severity, a `votes:` line with each finding's panel tally, and
a `next:` line: the Workflow call that continues the verification, or the
instruction to write the report's Coverage section. Where it can be, each
finding is placed by its quoted code, with the line the researcher declared
kept beside it (placed).

If agents of this run gave no result at first and returned on a retry, a
line before the summary line names them in the order they returned, up to
a fixed length, and counts the rest. Where a further run's lists of replaced
reports came back changed for the first time, such a line says that the run is
not recorded, and the `next:` line has its call made once more.

Where a scan sent researchers, all returned and none reported a finding, a line
after the `votes:` line says so.
Where voters of a panel asked at once had given no vote when the workflow
ended, their vote not needed, a line after those says how many.

A researcher may not return, and
Claude Code may give the workflow no reason. The workflow then hands on the label
of that agent's last call that was not refused, if no other call went out under
it. coverage.json gets the error text that the JSON file holds under that label,
where it holds one, the label does not end in ")", and no other row has it. If
entries ask for a text, and no row of the file has both a label and an error,
one line on stderr counts them.

Where write_scan_meta.py named unreadable directories, coverage.json gets each as a
skipped component, and "checked", or a "partial" that lists no other directory, becomes
"not-checkable".

Usage:
  save_result.py <output_file> <run_dir>

Exits 0 when the result is recorded or already was, or when the call is to be
made once more, 1 when it could not be recorded (the `next:` line still says
what to do), 2 on a usage error.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from bisect import bisect_right
from collections import Counter
from contextlib import suppress
from fnmatch import translate
from glob import escape
from itertools import accumulate
from pathlib import Path
from typing import NamedTuple

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, plugin, source, strictjson
from lib.agent_calls import call_errors
from lib.candidates import CHUNK, candidate_file, candidate_files, taken_from
from lib.chain import Chain, chain_of, pending_ranks
from lib.display import capped, single_line
from lib.finding import (
    FINDINGS_DIGEST_KEY,
    Confidence,
    FindingError,
    Panel,
    Severity,
    file_field,
    finding_panels,
    findings_digest,
    line_number,
    link_field,
    listed_in,
    scan_prefix_fits,
    scan_prefix_shaped,
    vote_rounds,
)
from lib.git import plain_fits
from lib.markdown import one_line
from lib.revision import change_range
from lib.strictjson import JsonMap, is_int, is_list, is_map, is_str, well_formed
from lib.unreadable import UNREADABLE_NEXT, corrected, is_lowered

RETRIED_ECHO_BYTES = 16_000
UNACCOUNTED_ECHO_CAP = 40
GLOB_CHARACTERS = frozenset("*?[")
WAITING_KEY = "waiting"
WAITING_ECHO_CAP = 40
NOT_CHECKED = "the researchers' coverage accounts are not checked"
NOT_NAMED = "the report names no area where past security fixes were followed up"
CID_RE = re.compile(r"^C([1-9][0-9]*)\Z")
WRITE_REPORT = (
    f"next: write the report's Coverage section to {plugin.COVERAGE_MD_NAME} in the run directory "
    "from coverage.json (if it is too large to read at once, read what the section needs from its "
    "numbered parts beside it, such as coverage.json.2, and do not edit them; if it has no parts, "
    "use Read's offset and limit; put any file of your own in the run directory, and nowhere else) "
    "per the report spec, then run render_report.py"
)
# The form of a reason that Claude Code gave, as in workflows/scan.js.
REPORTED = "Claude Code reported: "
PROSE_CAP = 400

LOST_RESEARCHERS_KEY = "lostResearchers"


class Records(NamedTuple):
    """A scan's three records and the chain its vote record carries."""

    findings: list[JsonMap]
    votes: JsonMap
    coverage: JsonMap
    chain: Chain

    @property
    def rounds(self) -> JsonMap:
        return vote_rounds(self.votes)

    def severity_counts(self) -> Counter[Severity]:
        """How many findings carry each severity; a word that names no Severity is not counted."""
        return Counter(s for s in map(Severity.of, self.findings) if s is not None)

    def panels(self) -> list[tuple[str, Panel | None]]:
        return finding_panels(self.rounds, [str(f["id"]) for f in self.findings])


class Args(argparse.Namespace):
    """The parsed command line."""

    output_file: str = ""
    run_dir: str = ""


class NotAResultError(Exception):
    """The output file holds no scan result this script can fold; the message names why."""

    fallback: str = (
        "Write the result's findings, votes and coverage from the completion notice to "
        "findings.json ([] where that list is empty), votes.json and coverage.json in the run "
        "directory yourself, leaving pastFixPaths, lastReport and every noReason out of "
        "coverage.json, then " + WRITE_REPORT[len("next: ") :]
    )


class CannotContinueError(Exception):
    """The run directory cannot take this result; the message names why."""

    fallback: str = "stop; no result was recorded, so say so and name the report directory"


class MiscopiedSettingsError(CannotContinueError):
    """No result is recorded, and the call's settings did not parse to a JSON object
    (workflows/scan.js gives the reason 'bad-args'): the call is to be made once more."""

    fallback: str = (
        "make the scan's Workflow call once more, its settings as one JSON object, not a quoted "
        "string (every key in double quotes, every closing brace), wait for it as before, and run "
        "this helper on its result; if this line comes again, stop: no result was recorded, so say "
        "so and name the report directory"
    )


class ChangedListsError(CannotContinueError):
    """Lists of replaced reports came back changed: standing gives that run one further try."""


def count(record: JsonMap, key: str) -> int:
    """A count the workflow wrote; anything but a non-negative integer cannot be folded."""
    value = record.get(key)
    if not is_int(value) or value < 0:
        msg = f"{key!r} is {value!r}, not a count"
        raise CannotContinueError(msg)
    return value


def texts(record: JsonMap, key: str) -> list[object]:
    """The list at `key`; empty where the key is absent or holds no list."""
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


def kept_entry(entry: JsonMap, errors: dict[str, str]) -> JsonMap:
    """A lost agent's entry as coverage.json keeps it: without `noReason`. Where the workflow set
    that field, Claude Code gave it no reason, and the field holds the `label` of the agent's last
    call that was not refused, and the `tail` of the reason. If `errors` has that label, the reason
    becomes REPORTED, the text on one line, cut at PROSE_CAP characters, and the tail."""
    kept = dict(entry)
    asked = kept.pop("noReason", None)
    if not is_map(asked):
        return kept
    label, tail = asked.get("label"), asked.get("tail")
    if is_str(label) and is_str(tail) and (error := errors.get(single_line(label))):
        kept["reason"] = REPORTED + capped(single_line(error), PROSE_CAP) + tail
    return kept


def with_kept_entries(result: JsonMap, errors: dict[str, str]) -> JsonMap:
    """`result`, with each lost agent's entry in its coverage as kept_entry() leaves it."""
    coverage = result.get("coverage")
    if not is_map(coverage) or not is_list(entries := coverage.get(LOST_RESEARCHERS_KEY)):
        return result
    lost = [kept_entry(entry, errors) if is_map(entry) else entry for entry in entries]
    return {**result, "coverage": {**coverage, LOST_RESEARCHERS_KEY: lost}}


def unanswerable(result: JsonMap, output: JsonMap) -> int:
    """How many lost agents' entries carry `noReason`, if no row of the output file has the two keys
    that call_errors() reads; else 0."""
    coverage = result.get("coverage")
    if not is_map(coverage) or any(
        is_map(call) and is_str(call.get("label")) and is_str(call.get("error"))
        for call in texts(output, "workflowProgress")
    ):
        return 0
    return sum(
        is_map(entry) and "noReason" in entry for entry in texts(coverage, LOST_RESEARCHERS_KEY)
    )


def result_in(output_file: Path) -> JsonMap:
    """The `result` object the runtime wrote to the workflow's output file, with each lost agent's
    entry in its coverage as kept_entry() leaves it. If entries ask for a text, and no row of the
    file has both a label and an error, one line on stderr counts them."""
    try:
        output = strictjson.load(output_file)
    except (OSError, ValueError) as error:
        msg = f"the output file cannot be read: {error}"
        raise NotAResultError(msg) from error
    if not is_map(output) or not is_map(result := output.get("result")):
        msg = "the output file holds no result object"
        raise NotAResultError(msg)
    if agents := unanswerable(result, output):
        sys.stderr.write(
            "save_result.py: no agent call in the output file has both a label and an error, "
            f"so the workflow's own reason stays for {agents} of the lost agents\n"
        )
    return with_kept_entries(result, call_errors(output))


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


class Tracked(NamedTuple):
    """The scan target's tracked files. `names` holds each file, each directory above one, and
    "" for the target itself. `roots` holds the two prefixes that a path may carry: the scan
    root's path within the repository, and its full path without the leading slash."""

    files: list[str]
    names: frozenset[str]
    roots: tuple[str, str]

    @classmethod
    def read(cls, meta: JsonMap, run_dir: Path) -> Tracked:
        """The tracked files that the scan job listed for the target. OSError or ValueError when
        the list cannot be read."""
        listed = strictjson.load(run_dir / plugin.TARGET_FILES_NAME)
        if not is_list(listed):
            msg = "not a list"
            raise ValueError(msg)
        files = [path for path in listed if is_str(path)]
        names = frozenset(name for path in files for name in ancestry(path))
        scan_prefix = str(meta.get("scan_prefix") or "")
        scan_root = str(meta.get("scan_root") or "").replace("\\", "/").strip("/") + "/"
        return cls(files, names | {""}, (scan_prefix, scan_root))

    def named(self, path: str) -> str:
        """`path` in the spelling that is among the names, or as given when none is."""
        return next((s for s in (path, *self.spellings(path)) if s in self.names), path)

    def spellings(self, path: str) -> tuple[str, ...]:
        """`path` with forward slashes, and without either root."""
        slashed = path.replace("\\", "/")
        return (slashed, *((slashed + "/").removeprefix(root).strip("/") for root in self.roots))

    def known(self, paths: list[object]) -> list[str]:
        """The tracked file or directory that each of `paths` names, once each. A path that names
        none, or the whole target, is left out."""
        named = (self.named(p) for p in paths if is_str(p))
        return list(dict.fromkeys(n for n in named if n and n in self.names))


def regex(glob: str) -> str | None:
    """`glob` as a regular expression, or None where re cannot compile it. Such a pattern names
    nothing."""
    translated = translate(glob)
    with suppress(re.error):
        re.compile(translated)
        return translated
    return None


def missed_by(account: JsonMap, target: Tracked) -> set[str]:
    """The names that one account's notReached paths give: each path as written, and, where that
    names no tracked path, under each of its component's paths; and for a path that names no
    tracked path either way and holds a glob character, what it matches inside the component, by
    fnmatch's rules (`*` also matches `/`). The component's own path is joined as tracked and
    read literally; a bracket in the pattern after any scan root it is spelled with still reads
    as a class."""
    own = {target.named(p) for p in texts(account, "paths") if is_str(p)}
    paths = [
        p for p in (e.get("path") for e in texts(account, "notReached") if is_map(e)) if is_str(p)
    ]
    named: set[str] = set()
    globs: set[str] = set()
    for p in paths:
        joined = (p,) if target.named(p) in target.names else (p, *(f"{o}/{p}" for o in own))
        spelled = {target.named(s) for s in joined}
        named |= spelled
        if spelled.isdisjoint(target.names) and not GLOB_CHARACTERS.isdisjoint(p):
            patterns = (p, *(f"{escape(o)}/{p}" for o in own))
            globs |= {g for s in patterns for g in target.spellings(s)}
    regexes = [r for r in map(regex, globs) if r]
    if not regexes:
        return named
    pattern = re.compile("|".join(regexes))
    inside = (n for n in target.names if not own.isdisjoint(["", *ancestry(n)]))
    return named | {n for n in inside if pattern.match(n)}


def counted(research: JsonMap, skipped: list[str], target: Tracked) -> JsonMap:
    """The coverage accounts of `research`, counted against the target's tracked files. `skipped`
    holds the paths that the inventory set aside, as the tracked files spell them. A file goes by
    the nearest path at or above it that a component or `skipped` names, and by the component
    where both name it. A file that goes by a skip counts in outsideComponents alone."""
    files, named = target.files, target.named
    accounts = [account for account in texts(research, "components") if is_map(account)]
    inside = {named(p) for account in accounts for p in texts(account, "paths") if is_str(p)}
    read = {named(p) for account in accounts for p in texts(account, "filesRead") if is_str(p)}
    missed = {name for account in accounts for name in missed_by(account, target)}
    claimed = inside.union(skipped)
    assigned = [
        f
        for f in files
        if next((n in inside for n in reversed(["", *ancestry(f)]) if n in claimed), False)
    ]
    unread = [f for f in assigned if f not in read]
    unaccounted = [f for f in unread if missed.isdisjoint(["", *ancestry(f)])]
    return {
        "files": len(assigned),
        "read": len(assigned) - len(unread),
        "notReached": len(unread) - len(unaccounted),
        "unaccounted": len(unaccounted),
        "unaccountedPaths": unaccounted[:UNACCOUNTED_ECHO_CAP],
        "outsideComponents": len(files) - len(assigned),
    }


def relayed(coverage: JsonMap, meta: JsonMap) -> JsonMap:
    """`coverage`, with a "checked" `completenessCheckOutcome` recorded as "not-checkable" where the
    workflow did not count as many directories as write_scan_meta.py listed, or that script gave
    no list. `topLevelRejected` and a line on stderr then say which."""
    listed, got = meta.get("top_level_dirs"), coverage.get("topLevelCount")
    whole = is_list(listed) and got == len(listed)
    if whole or coverage.get("completenessCheckOutcome") != "checked":
        return coverage
    made = f"a directory list of length {len(listed)}" if is_list(listed) else "no directory list"
    reason = f"write_scan_meta.py gave {made}, and the workflow counted {got}"
    sys.stderr.write(f'save_result.py: {reason}, so "checked" is recorded as "not-checkable"\n')
    return {**coverage, "completenessCheckOutcome": "not-checkable", "topLevelRejected": reason}


def checked(coverage: JsonMap, meta: JsonMap, run_dir: Path) -> JsonMap:
    """`coverage`, checked against the scan target's tracked files. `research.tree` counts the
    coverage accounts against them, as counted() says, with the paths of `skippedComponents`,
    where the accounts are checkable. `pastFixPaths` keeps, once each and as the tracked files spell
    them, only paths that name one or a directory above one, other than the target itself. With no
    readable list: `coverage` without `pastFixPaths` or a tree."""
    followed = texts(coverage, "pastFixPaths")
    coverage = {key: value for key, value in coverage.items() if key != "pastFixPaths"}
    research = coverage.get("research")
    accounted = research if is_map(research) and research.get("checkable") is True else None
    if not (accounted or followed):
        return coverage
    try:
        target = Tracked.read(meta, run_dir)
    except (OSError, ValueError) as error:
        lost = [text for text, due in ((NOT_CHECKED, accounted), (NOT_NAMED, followed)) if due]
        sys.stderr.write(
            f"save_result.py: {plugin.TARGET_FILES_NAME}: {error}, so {' and '.join(lost)}\n"
        )
        return coverage
    if paths := target.known(followed):
        coverage = {**coverage, "pastFixPaths": paths}
    elif followed:
        sys.stderr.write(
            f"save_result.py: pastFixPaths names no tracked path below the target, so {NOT_NAMED}\n"
        )
    if accounted:
        skips = [skip for skip in texts(coverage, "skippedComponents") if is_map(skip)]
        skipped = target.known([path for skip in skips for path in texts(skip, "paths")])
        tree = counted(accounted, skipped, target)
        coverage = {**coverage, "research": {**accounted, "tree": tree}}
    return coverage


def with_last_report(coverage: JsonMap, run_dir: Path) -> JsonMap:
    """The first run's `coverage`. Its `lastReport` gains what write_scan_meta.py took from the
    last report, by the script's own file, and the text that the report gives of it."""
    taken = taken_from(run_dir)
    if taken is None:
        return coverage
    told = coverage.get("lastReport")
    loaded = min(count(told, "loaded"), taken["held"]) if is_map(told) else 0
    text = (
        f"{loaded} of the {taken['findings']} findings of the last report, {taken['report']}, were "
        "taken from that report as candidates for this scan's verifiers. This report lists those "
        "that the verifiers confirmed. A finding of the last report that is missing from this one "
        "is not shown to be fixed by that."
    )
    return {**coverage, "lastReport": {**taken, "loaded": loaded, "text": text}}


def placed(finding: JsonMap, meta: JsonMap) -> JsonMap:
    """`finding` and each finding it lists, with file, change link and line as the render will
    carry them, and the file of each report that it replaces as the render will carry it.

    `line` becomes the line of the file its quoted snippet is on, and the line as it arrived
    moves to `declared_line`. Fields the render would refuse, and a file that the render would carry
    with a blank at an end, are left as they are.
    """
    finding_id, line, snippet = (
        finding.get("id"),
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
        or not scan_prefix_fits(prefix, scan_root=scan_root)
    ):
        return finding
    also_at = [
        entry if entry.get("also_at") else placed(entry, meta) for entry in listed_in(finding) or []
    ]
    must_exist = meta.get("mode") == "scan"

    def spelled(report: JsonMap) -> JsonMap:
        try:
            file = file_field(report, finding_id, scan_root, prefix, must_exist)
        except FindingError:
            return report
        return {**report, "file": file} if file == file.strip() else report

    filed = [spelled(report) for report in listed_in(finding, "also_filed_at") or []]
    listing = {
        **({"also_at": also_at} if also_at else {}),
        **({"also_filed_at": filed} if filed else {}),
    }
    try:
        file = file_field(finding, finding_id, scan_root, prefix, must_exist)
        via_change = link_field(finding, finding_id, scan_root, prefix)
    except FindingError:
        return {**finding, **listing, "line": line, "declared_line": line}
    return {
        **finding,
        **({"file": file} if file == file.strip() else {}),
        **({"via_change": via_change} if via_change else {}),
        **listing,
        "line": source.placed_line(source.read(scan_root, file), line, snippet or ""),
        "declared_line": line,
    }


def list_faults(run_dir: Path, run: Records, rows: dict[int, JsonMap]) -> list[str]:
    """One sentence for each candidate of verification run `run` that came back with another count
    of replaced reports than its row holds in the candidate files that write_records laid out, or,
    where that row holds any, did not come back. One that the run counts as lost is left out.
    Raises CannotContinueError where a candidate file does not open or parse, or is no object with
    a list under "candidates"."""
    files = sorted(run_dir.glob(f"candidates.{run.chain['shard']}.*.json"))
    msg = "a candidate file of this run cannot be read"
    try:
        chunks = [strictjson.load(file) for file in files]
    except (OSError, ValueError) as error:
        raise CannotContinueError(msg) from error
    if not all(is_map(chunk) and is_list(chunk.get("candidates")) for chunk in chunks):
        raise CannotContinueError(msg)
    written = {
        cid: len(texts(row, plugin.BEHIND_FILED))
        for chunk in chunks
        if is_map(chunk)
        for row in texts(chunk, "candidates")
        if is_map(row) and is_str(cid := row.get("cid"))
    }
    back: dict[str, int] = {}
    for round_ in filter(is_map, run.rounds.values()):
        if is_str(cid := round_.get("candidate")):
            back[cid] = len(texts(round_, "replaces"))
    for row in rows.values():
        if is_str(cid := row.get("cid")):
            back[cid] = len(texts(row, plugin.BEHIND_FILED))
    lost = {
        cid
        for fid in texts(run.coverage, "lostCandidates")
        if is_str(fid)
        and is_map(round_ := run.rounds.get(fid))
        and is_str(cid := round_.get("candidate"))
    }
    return [
        f"{cid} came back with {back[cid]} replaced report(s) "
        f"where its candidate file holds {filed}"
        if cid in back
        else f"{cid}, which replaced {filed} report(s), did not come back"
        for cid, filed in sorted(written.items(), key=lambda item: (len(item[0]), item[0]))
        if cid not in lost and back.get(cid, 0) != filed
    ]


def reports_behind(given: object) -> dict[str, JsonMap]:
    """By candidate id, what the first run's result gives of a candidate at Change Scan Effort high
    (`given`): its list of replaced reports (`alsoFiledAt`), and that list as a round has it
    (`places`)."""
    return {
        cid: {
            plugin.BEHIND_FILED: list(filter(is_map, texts(held, plugin.BEHIND_FILED))),
            plugin.BEHIND_PLACES: list(filter(is_str, texts(held, plugin.BEHIND_PLACES))),
        }
        for cid, held in (given.items() if is_map(given) else ())
        if is_map(held)
    }


def recorded_behind(run_dir: Path) -> dict[str, JsonMap]:
    """plugin.BEHIND_NAME as folded wrote it at the first run: the entries of reports_behind.
    Raises CannotContinueError where the file does not open or parse, or is no object whose every
    entry holds the two lists."""
    msg = f"{plugin.BEHIND_NAME} cannot be read"
    try:
        kept = strictjson.load(run_dir / plugin.BEHIND_NAME)
    except (OSError, ValueError) as error:
        raise CannotContinueError(msg) from error
    lists = (plugin.BEHIND_FILED, plugin.BEHIND_PLACES)
    whole = {
        cid: held
        for cid, held in (kept.items() if is_map(kept) else ())
        if is_map(held) and all(is_list(held.get(key)) for key in lists)
    }
    if not is_map(kept) or len(whole) != len(kept):
        raise CannotContinueError(msg)
    return whole


def other_places(run: Records, behind: dict[str, JsonMap]) -> list[str]:
    """One sentence for each candidate of verification run `run` whose round names other replaced
    reports than `behind` holds for it, in whatever order."""

    def named(record: JsonMap, key: str) -> list[tuple[bool, str]]:
        return sorted(
            (True, well_formed(place)) if is_str(place) else (False, "")
            for place in texts(record, key)
        )

    return [
        f"{cid} came back with other replaced reports than the first run handed on"
        for round_ in filter(is_map, run.rounds.values())
        if is_str(cid := round_.get("candidate"))
        and cid in behind
        and "replaces" in round_
        and named(round_, "replaces") != named(behind[cid], plugin.BEHIND_PLACES)
    ]


def with_own_list(finding: JsonMap, run: Records, behind: dict[str, JsonMap]) -> JsonMap:
    """`finding` of `run` with its `also_filed_at` out of `behind`, not out of the run, where
    `behind` has its candidate."""
    fid = finding.get("id")
    round_ = run.rounds.get(fid) if is_str(fid) else None
    cid = round_.get("candidate") if is_map(round_) else None
    if not is_str(cid) or cid not in behind:
        return finding
    filed = [
        {
            "file": entry.get("file"),
            "line": entry.get("line"),
            "cwe_id": entry.get("cweId"),
            "other_cwe_ids": entry.get("otherCweIds"),
            "title": entry.get("title"),
        }
        for entry in filter(is_map, texts(behind[cid], plugin.BEHIND_FILED))
    ]
    if filed:
        return {**finding, "also_filed_at": filed}
    return {key: value for key, value in finding.items() if key != "also_filed_at"}


def report_order(finding: JsonMap) -> tuple[bool, int, int]:
    """Sort key: the report's two groups in turn: the findings with no mark, then those
    marked `older_than_the_change`; within each group severity, then confidence, strongest first,
    unknown values last."""
    severity = Severity.of(finding)
    confidence = str(finding.get("confidence", "")).lower()
    return (
        "older_than_the_change" in finding,
        -(severity.value if severity else 0),
        -Confidence.__members__.get(confidence, 0),
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
    key = plugin.CHANGE_SCAN_EFFORT_KEY
    if run.coverage.get(key) != scan.coverage.get(key):
        msg = "the run's Change Scan Effort is not the scan's"
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
    if scan_rounds.keys() & run_rounds.keys():
        msg = "the run reuses a round id the scan already has"
        raise CannotContinueError(msg)

    votes = {
        **scan.votes,
        "panel_votes": count(scan.votes, "panel_votes") + count(run.votes, "panel_votes"),
        "unreviewed_candidate_sites": count(scan.votes, "unreviewed_candidate_sites")
        - len(handed)
        + count(run.votes, "unreviewed_candidate_sites"),
        "rounds": {**scan_rounds, **run_rounds},
        "chain": run.chain,
    }
    optional = {
        name: lines
        for name in ("replacedNotKept", "droppedOnDocuments")
        if (lines := texts(scan.coverage, name) + texts(run.coverage, name))
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
            "raised": texts(scan.coverage, "raised") + texts(run.coverage, "raised"),
            "findingsNotJoined": texts(scan.coverage, "findingsNotJoined")
            + texts(run.coverage, "findingsNotJoined"),
            "preExisting": texts(scan.coverage, "preExisting") + texts(run.coverage, "preExisting"),
            "preExistingAt": texts(scan.coverage, "preExistingAt")
            + texts(run.coverage, "preExistingAt"),
            "outsideScope": texts(scan.coverage, "outsideScope")
            + texts(run.coverage, "outsideScope"),
            **optional,
            "dispatchRefusals": count(scan.coverage, "dispatchRefusals")
            + count(run.coverage, "dispatchRefusals"),
            "continued": run.coverage.get("continued"),
            "verificationRun": run.chain["shard"],
        }
    )
    return Records(sorted(findings, key=report_order), votes, coverage, run.chain)


def with_waiting_list(coverage: JsonMap, rows: dict[int, JsonMap], chain: Chain) -> JsonMap:
    """`coverage`, with the candidates that wait for the next run listed under WAITING_KEY:
    one line for each of the first WAITING_ECHO_CAP, by rank, with its place, its title and why it
    waits. If none waits: `coverage` without that key."""
    rest = {key: held for key, held in coverage.items() if key != WAITING_KEY}
    if not rows:
        return rest
    retry = set(chain["retry"])
    waiting = [
        capped(one_line(f"{row.get('file')}:{row.get('line')}, {row.get('title')}"), PROSE_CAP)
        + ": "
        + ("no complete panel at its first try" if rank in retry else "no recorded panel result")
        for rank, row in sorted(rows.items())[:WAITING_ECHO_CAP]
    ]
    return {**rest, WAITING_KEY: waiting}


def write_json(run_dir: Path, name: str, value: object, indent: int = 2) -> None:
    """Write one record through a temporary name, so it is never seen half-written. findings.json
    and coverage.json then get their parts (write_parts)."""
    partial = run_dir / f"{name}.partial"
    data = (strictjson.text(value, indent=indent) + "\n").encode()
    partial.write_bytes(data)
    partial.replace(run_dir / name)
    if name in READ_IN_PARTS:
        write_parts(run_dir / name, data)


READ_IN_PARTS = frozenset({"findings.json", "coverage.json"})
PART_BYTES = 24_000
PART_RE = re.compile(rb"(?s:.{0,%d})\n|.+\n?" % (PART_BYTES - 1))


def parts_of(record: Path) -> list[Path]:
    """The entries beside `record` that bear its name, a dot and a number with no leading zero."""
    part_name = re.compile(rf"{re.escape(record.name)}\.[1-9][0-9]*")
    return [each for each in record.parent.iterdir() if part_name.fullmatch(each.name)]


def write_parts(record: Path, data: bytes) -> None:
    """Copy `data`, the bytes of `record`, to <record>.1, <record>.2 and on, in place of its earlier
    parts. A record of PART_BYTES or less gets none. A failed write or removal raises nothing,
    prints one line on stderr, and leaves no part but one that cannot be removed."""
    parts: list[bytes] = PART_RE.findall(data) if len(data) > PART_BYTES else []
    try:
        for stale in parts_of(record):
            stale.unlink()
        for number, part in enumerate(parts, start=1):
            record.with_name(f"{record.name}.{number}").write_bytes(part)
    except OSError as error:
        with suppress(OSError):
            for each in parts_of(record):
                with suppress(OSError):
                    each.unlink()
        with suppress(OSError):
            sys.stderr.write(
                f"save_result.py: the parts of {record.name} could not be replaced "
                f"({error.strerror or type(error).__name__}): read {record.name} with Read's "
                "offset and limit, not its parts\n"
            )


def for_the_session(coverage: JsonMap) -> JsonMap:
    """`coverage` with only `leftOut` of laterResearch, which the report and the relay read, so
    that the session, which reads coverage.json, does not retell the stages' other counts."""
    later = coverage.get("laterResearch")
    if not is_map(later):
        return coverage
    return {**coverage, "laterResearch": {k: v for k, v in later.items() if k == "leftOut"}}


def write_records(run_dir: Path, records: Records, rows: dict[int, JsonMap]) -> None:
    """The three records and the next run's candidate files; votes.json last, with the digest of
    findings.json."""
    write_json(run_dir, "findings.json", records.findings)
    write_json(run_dir, "coverage.json", for_the_session(records.coverage))
    shard = records.chain["shard"] + 1
    handed_on = [rows[rank] for rank in sorted(rows)]
    for name, chunk in candidate_files(run_dir, shard, handed_on):
        write_json(run_dir, name, chunk, indent=1)
    digest = findings_digest(run_dir)
    write_json(run_dir, "votes.json", {**records.votes, FINDINGS_DIGEST_KEY: digest})


def retried_line(labels: list[object]) -> str:
    """The line that names the agents that returned on a retry, in the order they returned, until
    the list would pass RETRIED_ECHO_BYTES, and counts the rest."""
    encoding = console.paths_encoding()
    sizes = (
        len(strictjson.text(label).encode(encoding, "backslashreplace")) + 2 for label in labels
    )
    fit = bisect_right(list(accumulate(sizes)), RETRIED_ECHO_BYTES)
    named, rest = labels[:fit], labels[fit:]
    more = f", and {len(rest)} more" if rest else ""
    return (
        "agents that returned on a retry, after failed or skipped calls: "
        f"{strictjson.text(named)}{more}"
    )


def rows_per_file(run_dir: Path, shard: int) -> int:
    """How many rows run `shard`'s first candidate file holds; if that file gives no count, CHUNK,
    with a line on stderr."""
    name = candidate_file(shard, 1)
    try:
        first = strictjson.load(run_dir / name)
        rows = first.get("candidates") if is_map(first) else None
        if is_list(rows) and rows:
            return len(rows)
        reason = "it holds no candidate rows"
    except OSError as error:
        reason = error.strerror or type(error).__name__
    except ValueError as error:
        reason = str(error)
    sys.stderr.write(
        f"save_result.py: could not read the row count from {name} ({reason}). The next Workflow "
        f"call says rowsPerFile {CHUNK}. That run loses the rows of any file it cannot read, and "
        "can lose more if the files hold another number of rows. Make the call anyway; the next "
        "run of save_result.py counts the lost rows, or says that it could not record the run.\n"
    )
    return CHUNK


def none_found_line(votes: JsonMap) -> str | None:
    """The line for a scan that sent researchers, all of which returned and reported no finding;
    else None."""
    found = votes.get("candidates")
    sent, back = votes.get("researchers_dispatched"), votes.get("researchers_returned")
    if is_int(found) and is_int(sent) and is_int(back) and found == 0 and sent == back >= 1:
        return (
            f"research: {back} of {sent} researchers returned, and none reported a finding (the "
            "completion notice may count them under `agents_empty_result`)"
        )
    return None


def without_vote_line(result: JsonMap) -> str | None:
    """The line that counts the verifiers whose vote was not needed and that had given no vote
    when the workflow ended; else None."""
    count = result.get("votersWithoutVote")
    if is_int(count) and count >= 1:
        return (
            f"panel: {count} verifier(s) whose vote was not needed had given no vote when the "
            "workflow ended (the completion notice may count them under `agents_error`)"
        )
    return None


def summary(records: Records) -> str:
    """Two lines: where the scan stands, with the count at each severity, then each
    finding's tally, or "?" when its panel is not complete, in findings.json's order. A tally
    also says how many of its votes call the flaw older than the change, if any do.
    """
    counts = records.severity_counts()
    by_severity = ", ".join(f"{counts[severity]} {severity.name}" for severity in Severity)
    tallies = [
        f"{i} {p['true']}/{p['voters']}" + (f" ({n} older)" if (n := p.get("predates")) else "")
        if p
        else f"{i} ?"
        for i, p in records.panels()
    ]
    return (
        f"recorded verification run {records.chain['shard']}: {len(records.findings)} findings "
        f"({by_severity}), "
        f"{len(records.rounds)} rounds, "
        f"{len(pending_ranks(records.chain))} pending, "
        f"{len(texts(records.coverage, 'lostCandidates'))} lost\n"
        f"votes: {', '.join(tallies) or 'no findings'}"
    )


def next_step(run_dir: Path, meta: JsonMap, records: Records) -> str:
    """The `next:` line: the Workflow call that panels what is pending, or the instruction to write
    the report's Coverage section."""
    chain = records.chain
    if not pending_ranks(chain):
        return WRITE_REPORT + (UNREADABLE_NEXT if is_lowered(records.coverage) else "")
    scope, reviewed_range = meta.get("scope"), records.coverage.get("range")
    scan_root = meta.get("scan_root")
    shard = chain["shard"] + 1
    args = {
        "scanRoot": scan_root,
        "runDir": str(run_dir),
        "mode": meta.get("mode"),
        "effort": meta.get("effort"),
        "scope": scope if is_list(scope) and scope else None,
        "range": reviewed_range if is_str(reviewed_range) else None,
        **(
            {"gitFromCwd": True}
            if is_str(reviewed_range) and is_str(scan_root) and plain_fits(scan_root)
            else {}
        ),
        **(
            {plugin.CHANGE_SCAN_EFFORT_KEY: plugin.CHANGE_SCAN_EFFORT_HIGH}
            if plugin.at_change_scan_effort_high(records.coverage)
            else {}
        ),
        **({"guided": True} if plugin.context_of(records.coverage) else {}),
        "verify": {
            "shard": shard,
            "idBase": chain["next_id"],
            "pending": chain["pending"],
            "retry": chain["retry"],
            "rowsPerFile": rows_per_file(run_dir, shard),
        },
    }
    return (
        "next: make this Workflow call exactly as printed, wait for it with keep-waiting.sh "
        "as before, then run save_result.py on its output file\n" + plugin.scan_call(args)
    )


def otherwise(run_dir: Path, fallback: str) -> str:
    """What to print when this result could not be recorded: the `next:` line, and after it any
    relay line of plugin.lost_findings_text's."""
    if not os.path.isfile(run_dir / "votes.json"):
        return f"next: {fallback}"
    if os.path.isfile(run_dir / "findings.json"):
        return WRITE_REPORT + "; its stamp will say what was not verified"
    return f"next: stop; findings.json is lost. {plugin.lost_findings_text(run_dir)}"


def folded(
    run_dir: Path,
    meta: JsonMap,
    scan: Records | None,
    run: Records,
    rows: dict[int, JsonMap],
    *,
    given: object,
    further_run_at_high: bool,
) -> tuple[Records, dict[int, JsonMap]]:
    """The scan's records with `run` folded in, and the rows to hand on; `scan` itself where an
    earlier save folded it. Raises CannotContinueError where the run cannot be recorded, and its
    subclass ChangedListsError where list_faults or other_places speaks.
    `further_run_at_high` says that `run` is next in turn behind a `scan` that awaiting_at_high
    gives. Then the refusal's words go into the stamp and the SARIF log, so they hold no advice to
    the Lead, and the run is also held to list_faults and other_places. At Change Scan Effort high
    a finding's list of replaced reports comes from the save's own entries (reports_behind of
    `given` at the first run, recorded_behind at a further one) wherever they hold the finding's
    candidate, and a row's wherever the list that they hold for the row's candidate is not empty;
    other lists are the run's, and other_places does not check them. At that setting the first run
    also writes plugin.BEHIND_NAME."""
    revision = meta.get("revision")
    reviewed_range = run.coverage.get("range")
    recorded_range = change_range(revision) if is_map(revision) else None
    if is_str(reviewed_range) and reviewed_range != recorded_range:
        msg = (
            f"the result reviewed {reviewed_range} but this scan recorded "
            f"{recorded_range or 'no change'}, so it is not a review of the change that was listed"
        )
        if not further_run_at_high:
            msg += ": run the scan again with the Workflow call that write_scan_meta.py prints"
        raise CannotContinueError(msg)
    if scan is None and run.chain["shard"] != 1:
        msg = f"this is run {run.chain['shard']} but no result is recorded yet"
        raise CannotContinueError(msg)
    if scan is not None and run.chain["shard"] <= scan.chain["shard"]:
        return scan, rows
    at_high = plugin.at_change_scan_effort_high((run if scan is None else scan).coverage)
    behind: dict[str, JsonMap] = {}
    if at_high:
        behind = reports_behind(given) if scan is None else recorded_behind(run_dir)
    run = run._replace(
        findings=[placed(with_own_list(item, run, behind), meta) for item in run.findings],
        coverage=checked(relayed(run.coverage, meta), meta, run_dir),
    )
    if scan is None:
        run = run._replace(coverage=with_last_report(run.coverage, run_dir))
    records = run if scan is None else merged(scan, run)
    if further_run_at_high and (
        faults := list_faults(run_dir, run, rows) or other_places(run, behind)
    ):
        raise ChangedListsError("; ".join(faults))
    if at_high and scan is None:
        write_json(run_dir, plugin.BEHIND_NAME, behind)
    own_lists: dict[str, list[object]] = {
        cid: filed for cid, held in behind.items() if (filed := texts(held, plugin.BEHIND_FILED))
    }
    return records, {
        rank: {**row, plugin.BEHIND_FILED: own_lists[cid]}
        if is_str(cid := row.get("cid")) and cid in own_lists
        else row
        for rank, row in rows.items()
    }


def awaiting_at_high(scan: Records | None) -> Records | None:
    """`scan` where it ran at Change Scan Effort high and hands candidates on to a further
    verification run; else None."""
    if scan is None or not plugin.at_change_scan_effort_high(scan.coverage):
        return None
    return scan if pending_ranks(scan.chain) else None


def run_named(result: JsonMap) -> int | None:
    """The verification run's number as a result that records_in refused names it; None where it
    gives no integer."""
    votes = result.get("votes")
    chain = votes.get("chain") if is_map(votes) else None
    shard = chain.get("shard") if is_map(chain) else None
    return shard if is_int(shard) else None


def leave_refusal_line(run_dir: Path, scan: Records, why: str) -> str:
    """Leave a line on the refused verification run, the one next in turn behind `scan`, in
    coverage.json's runNotRecorded, if that file can be written, and return the message that tells
    the Lead of it. Nothing else of the run is written."""
    told = f"verification run {scan.chain['shard'] + 1}: {why}"
    advice = (
        "leave its findings out of the report, and say under Coverage that it was not recorded, "
        "and why"
    )
    try:
        write_json(run_dir, "coverage.json", {**scan.coverage, plugin.RUN_NOT_RECORDED_KEY: told})
    except OSError as error:
        return (
            f"{told}, so this run is not recorded, and coverage.json could not be written "
            f"({error.strerror or type(error).__name__}): {advice}"
        )
    return f"{told}, so this run is not recorded: {advice} (coverage.{plugin.RUN_NOT_RECORDED_KEY})"


def standing(run_dir: Path, meta: JsonMap, scan: Records | None, result: JsonMap) -> Records:
    """The scan's records once `result` is taken into account, written if that changed them.
    At Change Scan Effort high a refusal of the run that is next in turn goes to leave_refusal_line.
    The first one over changed lists, once its line stands, is printed, and the scan is returned
    without the run.

    `meta` is the scan's settings (scan_settings).
    """
    if result.get("started") is False:
        if scan is None:
            if result.get("reason") == "bad-args":
                msg = "the workflow's settings did not parse to a JSON object, so no scan ran"
                raise MiscopiedSettingsError(msg)
            msg = "the workflow did not accept its settings, so no scan ran"
            raise CannotContinueError(msg)
        return scan
    made_for = result.get("runDir")
    made_here = is_str(made_for) and os.path.abspath(made_for) == str(run_dir)
    waiting = awaiting_at_high(scan)
    line_key = plugin.RUN_NOT_RECORDED_KEY
    try:
        run, rows = records_in(result)
    except NotAResultError as error:
        if waiting is None or not made_here:
            raise
        if run_named(result) not in {None, waiting.chain["shard"] + 1}:
            raise
        msg = leave_refusal_line(run_dir, waiting, f"its result cannot be read ({error})")
        raise CannotContinueError(msg) from error
    if not made_here:
        msg = f"the result names {made_for!r} as its run directory, not this one"
        raise CannotContinueError(msg)
    if waiting is not None and run.chain["shard"] != waiting.chain["shard"] + 1:
        waiting = None
    try:
        records, rows = folded(
            run_dir,
            meta,
            scan,
            run,
            rows,
            given=result.get("reportsBehind"),
            further_run_at_high=waiting is not None,
        )
    except CannotContinueError as error:
        if waiting is None:
            raise
        msg = leave_refusal_line(run_dir, waiting, str(error))
        first = isinstance(error, ChangedListsError) and line_key not in waiting.coverage
        left = recorded(run_dir) if first else None
        if left is not None and line_key in left.coverage:
            print(
                f"verification run {run.chain['shard']} is not recorded, because lists of replaced "
                f"reports came back changed (coverage.{line_key}): make its call once more"
            )
            return left
        raise CannotContinueError(msg) from error
    if records is scan:
        return records
    if waiting is not None and line_key in records.coverage:
        rest = {key: held for key, held in records.coverage.items() if key != line_key}
        records = records._replace(coverage=rest)
    records = records._replace(coverage=with_waiting_list(records.coverage, rows, records.chain))
    records = records._replace(coverage=corrected(records.coverage, meta))
    write_records(run_dir, records, rows)
    return records


def save(output_file: Path, run_dir: Path) -> None:
    """Fold the result into the run directory and print where the scan stands."""
    meta = scan_settings(run_dir)
    result = result_in(output_file)
    records = standing(run_dir, meta, recorded(run_dir), result)
    if result.get("started") is not False and (labels := texts(result, "returnedOnRetry")):
        print(retried_line(labels))
    print(summary(records))
    if line := none_found_line(records.votes):
        print(line)
    if result.get("started") is not False and (line := without_vote_line(result)):
        print(line)
    print(next_step(run_dir, meta, records))


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
        return 0 if isinstance(error, MiscopiedSettingsError) else 1
    except (OSError, ValueError) as error:
        sys.stderr.write(f"save_result.py: could not read or write the run's files: {error}\n")
        print(otherwise(run_dir, CannotContinueError.fallback))
        return 1
    return 0


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:]))
