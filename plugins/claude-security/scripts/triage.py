#!/usr/bin/env python3
"""Triage a list of existing findings: name the lists at hand (`lists`), say what a triage would
check (`count`), lay the findings out for the triage workflow (`load`), and write up the votes that
come back (`report`). The first two create nothing. Where patches can be offered, the results
directory becomes a report of the valid findings that can be patched, which Suggest patches takes.

Usage:
  triage.py lists
  triage.py count <list> [--from <place>]
  triage.py load <list> [--from <place>]
  triage.py report <output_file>

Exits 0 when done, 1 on a refusal or an error, and 2 on a usage error, such as a folder given to
report; stderr says why.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median_high
from typing import TYPE_CHECKING, NamedTuple, TypedDict, cast
from urllib.parse import unquote

# Under -P or PYTHONSAFEPATH Python does not add this script's directory, where lib/ lives.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import absolute, console, git, plugin, strictjson
from lib.agent_calls import call_errors
from lib.display import capped, single_line
from lib.finding import (
    LINK_SITE,
    OVERRULED_NOTE,
    PANEL_KEEP_QUORUM,
    PANEL_VOTER_COUNT,
    Severity,
    percent,
    repository_file,
    unpercent,
)
from lib.markdown import at_most, inline, one_line, span
from lib.removal import remove_tree
from lib.revision import Revision, dirty, revision_tag
from lib.sarif import PROPERTY_BAG
from lib.strictjson import JsonMap, as_map, clean, is_int, is_list, is_map, is_str, maps

if TYPE_CHECKING:
    from collections.abc import Iterator

MOST = 100
MOST_NAMED = 10
LISTS_OFFERED = 3
# Where the run directory holds each finding, as <id>.json, for workflows/triage.js to name.
FINDINGS_DIR = "findings"
RUN_JSON = "run.json"
LIST_JSON = "list.json"
TRIAGE_JSONL_NAME = "FINDINGS-TRIAGE.jsonl"
TRIAGE_SARIF_NAME = "FINDINGS-TRIAGE.sarif"
COPY_INDENT = 2
TRIAGE_KEY = "claudeSecurityPluginTriage"
ID_RE = re.compile(plugin.PATCH_UNIT_ID_PATTERN)
ROOTED_RE = re.compile(r"[/\\]|[A-Za-z]:[/\\]")
CWE_ID_RE = re.compile(r"CWE-[1-9][0-9]{0,4}")
NO_PROBLEM = ("pass", "notApplicable", "informational")
FILE_URI = re.compile(r"\Afile:(?://(?:localhost)?)?(?:/(?=[A-Za-z]:)|(?=/(?!/)))")
# The provenance value that workflows/triage.js writes into its result.
PROVENANCE = "workflows/triage.js"
CONFIRMS, REJECTS = "TRUE_POSITIVE", "FALSE_POSITIVE"
QUESTIONS = ("present", "ships", "reachable", "gain")
UNREAD = "COULD_NOT_READ"
VALID, NOT_CHECKED, NOT_VALIDATED = "valid", "not checked", "not validated"
HEADINGS = {
    VALID: "Valid, in the order to fix them",
    NOT_CHECKED: "Not checked: a verifier gave no usable answer, or was refused a file",
    NOT_VALIDATED: "Not validated",
}
# Each verifier's question, by its name in workflows/triage.js.
LENSES = ("REACHABILITY", "IMPACT", "DEFENSES")
# The most characters of an error that are quoted; workflows/triage.js cuts a thrown one there too.
REASON_CAP = 160
HOW = (
    "Three verifiers check each finding for a complete attack path. Each looks hardest at one "
    "question: can an attacker reach the code (REACHABILITY), does it matter (IMPACT), does "
    "something already stop it (DEFENSES)? Before its verdict each verifier also answers four "
    "questions: is the flaw there, does the code ship, can an untrusted party reach it, and does "
    "that party gain anything. A verifier that finds a path but answers NO to any of them counts "
    "as finding none. A finding is valid if at least two find such a path and the third also "
    "answers. It is not validated if at least two find none. Otherwise it is not checked. The "
    "severity after a valid finding's id comes from the verifiers that confirmed it. One more "
    "agent, the prioritize step, puts the valid findings in the order to fix them."
)
# Five spaces: the only indent that nests a sub-item under both "- " and "100. ".
SUB_ITEM = "     - "
GIVE_A_LIST = "Give a SARIF file, or the folder of a scan's report by the Claude Security plugin."
WHY_NOT = {
    True: (
        "git found uncommitted changes. To get patches, commit them or set them aside, then start "
        "a triage"
    ),
    None: (
        "git could not name a commit for this folder, or could not tell whether the checkout has "
        "uncommitted changes. To get patches, start a triage where git can tell both"
    ),
}
CAVEATS = (
    "This triage validated only the findings in the list. It did not search the code for other "
    'problems. "Valid" does not prove that a finding is real, or that it matters in your project. '
    '"Not validated" does not prove that the code is safe. The report\'s last section, "About this '
    'report", says how a finding is judged.'
)
REJECTED_REAL = (
    "The verifiers can reject a real finding. This is more likely when the finding's text is "
    "short, so read the reasons below. If a reason says that the code was not found, start a new "
    "triage in the folder that the list's paths start from."
)
NO_CALLER = (
    "At least two verifiers found the flaw in code that nothing calls or runs yet, so "
    f"{TRIAGE_SARIF_NAME} does not mark it as suppressed."
)


class TriageError(Exception):
    """A refusal, in words for the user."""


class Entry(TypedDict):
    """What a list says of a finding."""

    id: str
    tool: object
    rule: object
    title: object
    file: str | None
    line: int | None
    rating: object


LISTS_OWN = frozenset(Entry.__annotations__) - {"id"}


class Listed(Entry):
    """A finding as its verifiers read it, with its SARIF `rule` and `result` under `reported`."""

    reported: dict[str, JsonMap]


class PatchBase(TypedDict):
    """The checkout that patches would be written against. `dirty` is None where it is unknown."""

    top: str
    prefix: str
    commit: str | None
    dirty: bool | None


class Run(PatchBase):
    """What run.json holds for report: the patch base at the start, the words on the findings, and
    each finding's place in the list as [run, result]."""

    which: str
    more: str
    places: dict[str, list[int]]


class Judged(TypedDict):
    """What a finding's votes come to."""

    verdict: str
    severity: str | None
    checks: str
    votes: list[JsonMap]


class Spot(TypedDict):
    """A line of a file, spelled like the `file` and `line` of a line of the JSONL."""

    file: str
    line: int


class Overruled(TypedDict):
    """A verifier's note that it reported a finding against a file: the file and line, spelled
    like a Spot's, with no line where the verifier gave none, and the verifier's words."""

    file: str
    line: int | None
    why: str


class Row(Entry, Judged):
    """A line of the triage's JSONL: a finding, what its votes come to, its place in the order."""

    cwe_id: str | None
    order: int | None
    why: str
    found_at: Spot | None
    overruled: Overruled | None


NOT_HANDED = frozenset({"votes", "why", "found_at", "overruled", "tool", "rating"})


def at(value: object, *path: object) -> object:
    """The value at `path` in nested JSON objects and arrays; None where the path ends early."""
    for key in path:
        if is_map(value) and is_str(key):
            value = value.get(key)
        elif is_list(value) and is_int(key) and 0 <= key < len(value):
            value = value[key]
        else:
            return None
    return value


def quoted(words: object, missing: str = "") -> str:
    """Words that are not the plugin's own, as a code span on one line; `missing` for no words."""
    text = clean(words)
    return span(text) if text else missing


def unvoted(result: JsonMap) -> JsonMap:
    """A SARIF result without an earlier report's record of its verifiers' votes, or a triage's
    verdict and suppression."""
    result = cleared(result)
    if is_str(text := at(result, "message", "text")):
        result = {**result, "message": {**as_map(result["message"]), "text": unnoted(text)}}
    properties, bag = result.get("properties"), at(result, "properties", PROPERTY_BAG)
    if not (is_map(properties) and is_map(bag)):
        return result
    kept = {key: bag[key] for key in bag if key != "verification"}
    if is_str(description := kept.get("description")):
        kept["description"] = unnoted(description)
    return {**result, "properties": {**properties, PROPERTY_BAG: kept}}


def unnoted(text: str) -> str:
    """`text` without the paragraphs that hold a voter's note (OVERRULED_NOTE)."""
    return "\n\n".join(part for part in text.split("\n\n") if OVERRULED_NOTE not in part)


def anchored(file: str) -> bool:
    """Whether `file` is a URL, or starts at a root or at a drive's root. A name such as a:b.py
    does neither, though Windows reads it as a path on a drive."""
    return "://" in file or ROOTED_RE.match(file) is not None


def path_of(run: JsonMap, place: object) -> str | None:
    """The path that the SARIF artifactLocation `place` spells, percent-decoded and without the
    `file:` prefix that FILE_URI matches; None if it has no `uri`. A relative path starts from the
    folder of its `uriBaseId`, as far as the run's `originalUriBaseIds` give relative folders."""
    if not at(place, "uri"):
        return None
    path: str | None = None
    seen: set[str] = set()
    while is_str(uri := at(place, "uri")):
        part = FILE_URI.sub("", unquote(uri, errors="surrogateescape"))
        fixed = anchored(part)
        if path is None:
            path = part
        elif not fixed:
            path = posixpath.join(part, path)
        base = at(place, "uriBaseId")
        if fixed or not is_str(base) or base in seen:
            break
        seen.add(base)
        place = at(run, "originalUriBaseIds", base)
    return path


def findings(run: JsonMap, prefix: str) -> Iterator[tuple[int, Listed]]:
    """The results of one SARIF run, each with its index in the run's `results`, and with the id
    that it carries, or an empty one. A relative file that the run spells from the top level is
    spelled anew from the triage's folder, whose place in the repository is `prefix`. Any other
    file keeps the spelling that path_of() gives."""
    parts = [*maps(at(run, "tool", "extensions")), at(run, "tool", "driver")]
    rules = {clean(rule.get("id")): rule for part in parts for rule in maps(at(part, "rules"))}
    rules.pop("", None)
    from_top = at(run, "properties", PROPERTY_BAG, "revision", "versioned") is True
    results = run.get("results")
    for index, given in enumerate(results if is_list(results) else []):
        if not is_map(given):
            continue
        result = unvoted(given)
        rule_id = result.get("ruleId") or at(result, "rule", "id")
        named = at(result, "rule", "toolComponent")
        part = at(run, "tool", "extensions", at(named, "index")) if named else parts[-1]
        by_place = at(part, "rules", result.get("ruleIndex", at(result, "rule", "index")))
        own = (rule for rule in maps(at(part, "rules")) if rule_id and rule.get("id") == rule_id)
        rule = by_place if is_map(by_place) else next(own, rules.get(clean(rule_id), {}))
        location = at(result, "locations", 0, "physicalLocation")
        artifact = at(location, "artifactLocation")
        listed = at(run, "artifacts", at(artifact, "index"), "location")
        file = path_of(run, artifact if at(artifact, "uri") else listed)
        if file and prefix and from_top and not anchored(file):
            file = posixpath.relpath(file, prefix)
        line = at(location, "region", "startLine")
        unrated = "warning" if result.get("kind", "fail") == "fail" else None
        finding: Listed = {
            "id": clean(at(result, "properties", PROPERTY_BAG, "id")),
            "tool": at(run, "tool", "driver", "name"),
            "rule": rule_id or rule.get("id"),
            "title": clean(at(result, "properties", PROPERTY_BAG, "title"))
            or at(result, "message", "text")
            or at(rule, "shortDescription", "text"),
            "file": file,
            "line": line if is_int(line) and line > 0 else None,
            "rating": result.get("level") or at(rule, "defaultConfiguration", "level") or unrated,
            "reported": {"rule": rule, "result": result},
        }
        yield index, finding


def set_aside(result: JsonMap) -> bool:
    """Whether its tool marks a SARIF result as no open problem: by its kind, as no longer found, or
    as suppressed. A result is suppressed if it has a suppression, and the `status` of each of its
    suppressions is "accepted" or absent."""
    statuses = [s.get("status", "accepted") for s in maps(result.get("suppressions"))]
    return (
        result.get("kind") in NO_PROBLEM
        or result.get("baselineState") == "absent"
        or (bool(statuses) and all(s == "accepted" for s in statuses))
    )


def list_file(source: str) -> Path:
    """The absolute path of the list that `source` names: `source`, or, where that is a directory,
    the file in it with the name of a scan report's SARIF file. No link is resolved."""
    path = Path(os.path.abspath(source))
    return path / plugin.SARIF_NAME if os.path.isdir(path) else path


class Window(NamedTuple):
    """What a triage takes from a list: the findings by their ids, the words that say which findings
    those are, the sentences on what it leaves out, the place of the first finding after these if
    there is one, each finding's place in the log as [run, result], and the log as it was read."""

    findings: dict[str, Listed]
    which: str
    more: str
    following: int | None
    places: dict[str, list[int]]
    log: JsonMap


def read_list(source: str, first: int, prefix: str) -> Window:
    """Up to MOST findings of the SARIF 2.1.0 file that `source` names, from place `first` on. The
    ids are the report's own, or F1, F2, ... by place among the results that their tool did not set
    aside. `prefix` is the working directory's place in the repository.
    Refuse a file that cannot be read, does not give its `version` as 2.1.0 or is an attack surface
    analysis's, and a `first` at which the list has no finding."""
    path = list_file(source)
    folder = Path(os.path.realpath(path.parent))
    inside = absolute.relative(str(folder / path.name), os.path.realpath(Path.cwd()))
    shown = quoted(f"./{inside}" if inside else str(path))
    try:
        log = strictjson.load(path, encoding="utf-8-sig")
    except OSError as error:
        msg = f"{shown} cannot be read: {error.strerror}. {GIVE_A_LIST}"
        raise TriageError(msg) from None
    except ValueError as error:
        msg = f"{shown} cannot be read as JSON in UTF-8 ({quoted(str(error))}). Give a SARIF file."
        raise TriageError(msg) from None
    if not is_map(log) or log.get("version") != "2.1.0":
        msg = f"{shown} is not a SARIF 2.1.0 file. {GIVE_A_LIST}"
        raise TriageError(msg)
    given = log.get("runs")
    runs = given if is_list(given) else []
    if plugin.ANALYSIS_STAMP_MODE in (at(run, "properties", PROPERTY_BAG, "mode") for run in runs):
        msg = (
            f"{shown} belongs to an attack surface analysis, which a triage does not check. "
            f"{GIVE_A_LIST}"
        )
        raise TriageError(msg)
    listed = [
        ([number, index], finding)
        for number, run in enumerate(runs)
        if is_map(run)
        for index, finding in findings(run, prefix)
    ]
    found = [(place, f) for place, f in listed if not set_aside(f["reported"]["result"])]
    ids = [finding["id"] for _, finding in found]
    if len(set(ids)) < len(ids) or not all(map(ID_RE.fullmatch, ids)):
        for number, (_, finding) in enumerate(found, 1):
            finding["id"] = f"F{number}"
    skips = len(listed) - len(found)
    results = "result" if skips == 1 else "results"
    problems = "an open problem" if skips == 1 else "open problems"
    skipped = (
        f" The triage skips {skips} {results} that the list does not report as {problems}."
        if skips
        else ""
    )
    last = min(first - 1 + MOST, len(found))
    if not 0 < first <= last:
        noun = "finding" if len(found) == 1 else "findings"
        there = f" There is no finding {first}." if found else ""
        msg = f"{shown} has {len(found) or 'no'} {noun}.{there}{skipped}"
        raise TriageError(msg)
    chosen = {finding["id"]: finding for _, finding in found[first - 1 : last]}
    places = {finding["id"]: place for place, finding in found[first - 1 : last]}
    tools = ", ".join(sorted({clean(f["tool"]) for f in chosen.values()} - {""}))
    which = f"findings {first} to {last}" if first < last else f"finding {first}"
    which += f" of {len(found)} in {shown} (from {quoted(tools, 'an unnamed tool')})"
    following = last + 1 if last < len(found) else None
    more = f" A triage validates at most {MOST} findings." if following else ""
    return Window(
        findings=chosen,
        which=which,
        more=skipped + more,
        following=following,
        places=places,
        log=log,
    )


def lists(_: Args) -> None:
    """Print up to LISTS_OFFERED lists in the working directory, each on an `option:` line: its
    `.sarif` files by name, then its scan reports, the newest first. One of those places is kept for
    the newest report. A scan report is a directory that has a report's name, holds a scan's SARIF
    file, and is no attack surface analysis's."""
    here = sorted(Path().iterdir())
    loose = [path.name for path in here if path.suffix.lower() == ".sarif" and os.path.isfile(path)]
    scans = [
        path.name
        for path in reversed(here)
        if plugin.REPORT_DIR_RE.match(path.name)
        and os.path.isfile(path / plugin.SARIF_NAME)
        and not plugin.holds_analysis(path)
    ]
    for name in (loose[: LISTS_OFFERED - 1 if scans else LISTS_OFFERED] + scans)[:LISTS_OFFERED]:
        print(f"option: {name}")


def working_directory() -> str:
    """The working directory's path, where the triage runs. Refuse a path that does not come back
    the same when its printed bytes are read as UTF-8."""
    root = str(Path.cwd())
    if console.read_as_utf8(root) != root:
        msg = "The folder's path is not read as UTF-8 here. Move the project to an ASCII-only path."
        raise TriageError(msg)
    return root


def patch_base(scan_root: str, source: str) -> PatchBase:
    """What Suggest patches would write patches against in the checkout at `scan_root`. As for a
    scan, a report folder does not count as an uncommitted change. Nor does a SARIF file (.sarif or
    .sarif.json), or the list's own file."""
    top, commit = git.toplevel(scan_root) or "", git.commit_id(scan_root, "HEAD")
    inside = absolute.relative(os.path.realpath(list_file(source)), os.path.realpath(top))
    own = [f":(top,exclude,literal){inside}"] if inside else []
    sarif = (":(top,exclude,glob,icase)**/*.sarif", ":(top,exclude,glob,icase)**/*.sarif.json")
    status = "--no-literal-pathspecs", "status", "--porcelain", "--untracked-files=all", "--", ":/"
    prefix = git.run(scan_root, "rev-parse", "--show-prefix")
    changes = git.run(scan_root, *status, *sarif, *own) if commit and prefix is not None else None
    return {
        "top": top,
        "prefix": prefix or "",
        "commit": commit,
        "dirty": None if changes is None else dirty(changes),
    }


def seen_in(file: str, root: str) -> str | None:
    """The POSIX path below `root` (an absolute, normalized path) of the regular file that `file`
    names there; None if none is seen. A spelling that leads out of `root` is not looked up."""
    path = os.path.normpath(Path(root, file))
    below = absolute.relative(path, root)
    return below if below and os.path.isfile(path) else None


def absent(file: str | None, root: str) -> bool:
    """Whether a finding names a file that is not seen in `root`."""
    return bool(file) and not seen_in(file, root)


def count(args: Args) -> None:
    """Say what a triage of the list would check, why it would offer no patches, if so, and which of
    those findings name a file that it does not find in the folder."""
    scan_root = working_directory()
    base = patch_base(scan_root, args.source)
    window = read_list(args.source, args.first, base["prefix"])
    found, which, more = window.findings, window.which, window.more
    if window.following:
        more += " When this triage ends, you will get the command for the next ones."
    if missing := [name for name, finding in found.items() if absent(finding["file"], scan_root)]:
        more += (
            f" For {at_most(MOST_NAMED, missing)}, the file was not found in this folder. If the "
            "list's paths start from another folder, start the triage there."
        )
    why_not = WHY_NOT.get(base["dirty"])
    warning = f" This triage will offer no patches, because {why_not}." if why_not else ""
    print(
        f"says: This triage will validate {which}. {PANEL_VOTER_COUNT} independent verifiers check "
        f"each finding.{warning}{more} This may take a while and may use a significant number of "
        "tokens. You will need to leave Claude Code open while it completes. Outside auto mode, "
        "Claude Code may ask for your permission many times."
    )


def encoded(*records: object, indent: int | None = None) -> bytes:
    """JSON values, or lines of text, as a file holds them, each ending its line."""
    lines = (r if is_str(r) else strictjson.text(r, indent=indent) for r in records)
    return "".join(f"{line}\n" for line in lines).encode("utf-8", "backslashreplace")


def load(args: Args) -> None:
    """Lay the findings out for the workflow and for report, and print the call to make."""
    scan_root = working_directory()
    base = patch_base(scan_root, args.source)
    window = read_list(args.source, args.first, base["prefix"])
    listed = encoded(window.log, indent=COPY_INDENT)
    started = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    results = Path(scan_root, f"{plugin.REPORT_DIR_PREFIX}{started}")
    more = window.more
    if window.following:
        copy = quoted(f"./{results.name}/{TRIAGE_SARIF_NAME}")
        more += (
            f" To validate the next ones, run /claude-security triage {copy} from "
            f"{window.following}. That file holds the list with this triage's verdicts, so all "
            "verdicts stay in one file."
        )
    run: Run = {"which": window.which, "more": more, "places": window.places, **base}
    run_dir = results / plugin.RUN_DIR_NAME
    results.mkdir()
    (run_dir / FINDINGS_DIR).mkdir(parents=True)
    (run_dir / RUN_JSON).write_bytes(encoded(run, indent=1))
    (results / ".gitignore").write_bytes(b"*\n")
    (run_dir / LIST_JSON).write_bytes(listed)
    found = window.findings
    for name, finding in found.items():
        (run_dir / FINDINGS_DIR / f"{name}.json").write_bytes(encoded(finding, indent=1))
    call = {
        "scanRoot": scan_root,
        "runDir": str(run_dir),
        "ids": list(found),
        "belowTop": bool(base["prefix"]),
    }
    print(
        "relay: in one response with the Workflow call, and before it, say this to the user "
        "exactly as printed: Validating "
        f"{len(found)} finding{'s' if len(found) > 1 else ''} against the code. Results appear "
        "only when the whole run is done. Until then, do not change the code. Where Claude Code "
        "offers /workflows, it shows the progress.\n"
        "next: make this Workflow call exactly as printed, wait for it with keep-waiting.sh, then "
        "run triage.py report on its output file\n"
        f'Workflow({{ name: "claude-security:triage", args: {strictjson.text(call)} }})'
    )


def workflow_result(output_file: str) -> tuple[JsonMap, Path, dict[str, list[JsonMap]]]:
    """The workflow's output, the run directory that its result names, and each finding's votes.
    Refuse a result without PROVENANCE, a run directory of another shape or with no run.json, and
    votes that are not for exactly the findings there."""
    output = strictjson.load(Path(output_file))
    result = at(output, "result")
    panels = at(result, "results")
    votes = {name: maps(panel) for name, panel in (panels.items() if is_map(panels) else ())}
    run_dir = Path(clean(at(result, "runDir")))
    if (
        not is_map(output)
        or at(result, "provenance") != PROVENANCE
        or run_dir.name != plugin.RUN_DIR_NAME
        or not plugin.REPORT_DIR_RE.match(run_dir.parent.name)
        or not os.path.isfile(run_dir / RUN_JSON)
        or votes.keys() != {path.stem for path in (run_dir / FINDINGS_DIR).glob("F*.json")}
    ):
        msg = (
            "This triage already has its report, its results folder was moved or deleted, or the "
            "workflow left no whole result. If it has no report, start a new triage of the list."
        )
        raise TriageError(msg)
    return output, run_dir, votes


def failures(output: JsonMap) -> dict[str, str]:
    """Claude Code's word, by phase, on why an agent gave no usable answer: the error that the
    workflow caught, else the first that call_errors() has for that phase, on one line and cut at
    REASON_CAP."""
    errors = call_errors(output)
    # workflows/triage.js labels the ordering agent's call "order". Each other call is a verifier's.
    ordering = errors.pop("order", "")
    lost = {"Prioritize": ordering, "Validate": next(iter(errors.values()), "")}
    return {
        phase: clean(at(output, "result", "failure", phase))
        or capped(single_line(error), REASON_CAP)
        for phase, error in lost.items()
    }


def judge(votes: list[JsonMap]) -> Judged:
    """A finding's verdict, from the workflow's votes. It is valid if all voters answer,
    UNREAD too, and a quorum confirms it. It is not validated if too many voters reject it for the
    rest to reach a quorum. Else it is not checked. Also a valid finding's severity: the upper
    median of those that the confirming votes give."""
    yes = [vote for vote in votes if vote.get("verdict") == CONFIRMS]
    no = [vote for vote in votes if vote.get("verdict") == REJECTS]
    grades = list(filter(None, map(Severity.of, yes)))
    silent = PANEL_VOTER_COUNT - len(votes)
    rejected = PANEL_VOTER_COUNT - len(no) < PANEL_KEEP_QUORUM
    confirmed = not silent and len(yes) >= PANEL_KEEP_QUORUM
    verdict = NOT_VALIDATED if rejected else VALID if confirmed else NOT_CHECKED
    rated = verdict == VALID and bool(grades)
    tally = f"{len(yes)} of {PANEL_VOTER_COUNT} verifiers found a complete attack path"
    if unread := sum(vote.get("verdict") == UNREAD for vote in votes):
        were = "was refused a file that its answer turns on"
        if unread > 1:
            were = "were refused a file that their answers turn on"
        tally += f"; {unread} {were}"
    if silent:
        answered = [vote.get("lens") for vote in votes]
        unanswered = [lens for lens in LENSES if lens not in answered]
        named = f" ({', '.join(unanswered)})" if len(unanswered) == silent else ""
        tally += f"; {silent} gave no usable answer{named}"
    return {
        "verdict": verdict,
        "severity": median_high(grades).name if rated else None,
        "checks": f"{tally}.",
        "votes": votes,
    }


def found_at(finding: Listed, judgement: Judged, root: str, prefix: str) -> Spot | None:
    """Where a valid finding's flaw is, if its file is absent() from the triage's folder `root`: in
    the file of `root` that the confirming verifiers name most often, the most-named line of any
    such file, the first named among ties. None for any other finding, or where they name no such
    line. `prefix` is the folder's place in the repository."""
    if judgement["verdict"] != VALID or not absent(finding["file"], root):
        return None
    sites = (
        LINK_SITE.fullmatch(clean(at(vote, "present", "at")))
        for vote in judgement["votes"]
        if vote.get("verdict") == CONFIRMS
    )
    seen = [(file, site[2]) for site in sites if site and (file := seen_in(site[1], root))]
    if not seen:
        return None
    files = [file for file, _ in seen]
    file, line = max(seen, key=lambda pair: (files.count(pair[0]), seen.count(pair)))
    return {"file": percent(repository_file(prefix, file=file)), "line": int(line)}


_BRACKETED = r"""(?:\([^\s:`,*"'()\\/]*\)|\[{1,2}[^\s:`,*"'\[\]\\/]*\]{1,2})"""
OVERRULED_PLACE = re.compile(
    rf"""(?:(?!{_BRACKETED}[\\/])[\s`*("'\[])*"""
    rf"""((?:[A-Za-z]:(?=[\\/]))?(?:{_BRACKETED}|[^\s:`,)*"'\]])+)"""
    r"(?::([1-9][0-9]{0,14}))?"
)


def overruled_at(judgement: Judged, root: str, prefix: str) -> Overruled | None:
    """The note of a valid finding's first confirming vote that reports it against a file seen in
    the triage's folder `root`: that file as the row's `file` is spelled, its line if the vote gave
    one, and the words."""
    if judgement["verdict"] != VALID:
        return None
    for vote in judgement["votes"]:
        site = OVERRULED_PLACE.match(clean(at(vote, "overruled", "place")))
        why = clean(at(vote, "overruled", "why"))
        if vote.get("verdict") == CONFIRMS and site and why and (file := seen_in(site[1], root)):
            line = int(site[2]) if site[2] else None
            return {"file": percent(repository_file(prefix, file=file)), "line": line, "why": why}
    return None


def jsonl_row(
    finding: Listed, judgement: Judged, step: JsonMap, place: int, run: Run, root: str
) -> Row:
    """One line of the JSONL for `finding`: its fields, its verdict, its `place` if it is valid, and
    the workflow's `step` for it. `root` is the triage's folder."""
    title, file = finding["title"], finding["file"]
    recorded = at(finding, "reported", "result", "properties", PROPERTY_BAG, "line")
    cwe_id = clean(step.get("cwe_id"))
    if file and "://" not in file:
        if anchored(file):
            file = (run["top"] and absolute.relative(os.path.normpath(file), run["top"])) or file
        else:
            file = repository_file(run["prefix"], file=file)
    if is_str(title):
        title = strictjson.well_formed((title.lstrip().splitlines() or [""])[0])
    return {
        "id": finding["id"],
        "tool": finding["tool"],
        "rule": finding["rule"],
        "title": title if is_str(title) else None,
        "file": percent(file) if file else None,
        "line": None if is_int(recorded) and recorded < 1 else finding["line"],
        "rating": finding["rating"],
        "cwe_id": cwe_id if CWE_ID_RE.fullmatch(cwe_id) else None,
        "order": place if judgement["verdict"] == VALID else None,
        "why": clean(step.get("why")),
        "found_at": found_at(finding, judgement, root, run["prefix"]),
        "overruled": overruled_at(judgement, root, run["prefix"]),
        **judgement,
    }


def ranked_rows(
    found: dict[str, Listed],
    votes: dict[str, list[JsonMap]],
    order: list[JsonMap],
    run: Run,
    root: str,
) -> list[Row]:
    """The findings as the page and the JSONL list them: by verdict, then as the workflow ordered
    them, then by severity, then by the number of verifiers that confirmed them, then as the list
    does. A valid finding is placed by the first step that names its id and gives a reason."""
    judgements = {name: judge(votes[name]) for name in found}
    steps: dict[str, JsonMap] = {}
    for step in order:
        name = clean(step.get("id"))
        if name in found and judgements[name]["verdict"] == VALID and one_line(step.get("why")):
            steps.setdefault(name, step)

    def weight(name: str) -> tuple[int, int]:
        confirming = sum(vote.get("verdict") == CONFIRMS for vote in votes[name])
        return Severity.named(judgements[name]["severity"]) or 0, confirming

    names = sorted(
        dict.fromkeys((*steps, *sorted(found, key=weight, reverse=True))),
        key=lambda name: [*HEADINGS].index(judgements[name]["verdict"]),
    )
    return [
        jsonl_row(found[n], judgements[n], steps.get(n, {}), place, run, root)
        for place, n in enumerate(names, 1)
    ]


def at_found_place(row: Row) -> Row:
    """`row` with the file and line of its `found_at`, where it has one."""
    spot = row["found_at"]
    return {**row, **spot} if spot else row


def patchable(row: Row, top: str) -> bool:
    """Whether a valid finding's row, as report hands it to Suggest patches, has all that Suggest
    patches needs in each line of a report: a path below the repository's top level, with no half
    of a surrogate pair, a severity and a CWE id. A path that starts with a folder named like a
    drive, such as C:/x.py, reads as a machine's and fails too. A regular file must also exist at
    the row's path below top."""
    file = unpercent(row["file"] or "")
    below = not anchored(file) and absolute.below_top(file)
    whole = not strictjson.has_lone_surrogate(row["file"] or "")
    complete = below and whole and row["severity"] and row["cwe_id"]
    return bool(complete and os.path.isfile(git.for_disk(f"{top}/{file}")))


def ids_of(rows: list[Row]) -> str:
    """The ids of the first MOST_NAMED of these findings, and how many more there are."""
    return at_most(MOST_NAMED, [row["id"] for row in rows])


def verdict_counts(rows: list[Row]) -> str:
    """How many findings have each verdict, and which."""
    groups = {v: [row for row in rows if row["verdict"] == v] for v in HEADINGS}
    return ", ".join(
        f"{len(held)} {verdict}" + (f" ({ids_of(held)})" if held else "")
        for verdict, held in groups.items()
    )


def summary_lines(
    rows: list[Row], base: PatchBase, fixes: list[Row], failure: dict[str, str]
) -> list[str]:
    """The paragraphs after the count, in the closing message and on the page: on missing answers,
    refused files, the order, what a verdict proves, and patches, which the triage offers for
    `fixes`. `failure` is Claude Code's word, by phase, on why an agent gave no usable answer."""
    reported = {
        phase: f" Claude Code reported {words}." if (words := quoted(said)) else ""
        for phase, said in failure.items()
    }
    valid = [row for row in rows if row["verdict"] == VALID]
    paragraphs: list[str] = []
    if short := [row for row in rows if len(row["votes"]) < PANEL_VOTER_COUNT]:
        paragraphs.append(
            f"For {ids_of(short)}, at least one verifier gave no usable answer."
            f"{reported['Validate']} A new triage may get the missing answers."
        )
    if refused := [row for row in rows if UNREAD in (v.get("verdict") for v in row["votes"])]:
        paragraphs.append(
            f"For {ids_of(refused)}, at least one verifier was refused a file that its answer "
            "turns on. The report names each such file that a verifier named. A new triage is "
            "likely to meet the same refusal, unless you first let Claude Code read each such file."
        )
    if unranked := [row for row in valid if not row["why"]]:
        paragraphs.append(
            f"The prioritize step did not rank {ids_of(unranked)}.{reported['Prioritize']} Each "
            "finding that it did not rank follows the ranked ones, by severity, then by the number "
            "of verifiers that confirmed it. A new triage may rank it."
        )
    if any(row["verdict"] != NOT_CHECKED for row in rows):
        paragraphs.append(CAVEATS)
    if not valid:
        paragraphs.append("This triage offers no patches, because it found no valid finding.")
    elif why_not := WHY_NOT.get(base["dirty"]):
        paragraphs.append(f"Patches are not available, because {why_not}.")
    elif without := [row for row in valid if row not in fixes]:
        paragraphs.append(
            f"Patches are not available for {ids_of(without)}: a patch needs a file at a relative "
            "path in this repository, a severity and a CWE id. A new triage may give a severity or "
            "a CWE id that is missing."
        )
    return paragraphs


def offer(fixes: list[Row]) -> str:
    """The offer of patches that ends the closing message."""
    several = len(fixes) > 1
    return (
        "Several agents write and analyze each patch. This may take a while and may use a "
        "significant number of tokens.\n\n"
        f"Do you want me to suggest {'patches' if several else 'a patch'} for {ids_of(fixes)}?"
        f"{' Reply yes for all of them, or name the ones you want.' if several else ''}"
    )


def agent_line(label: str, words: object) -> list[str]:
    """An agent's own words as a labelled line of the page, with no HTML; no line for no words."""
    text = inline(clean(words))
    return [f"{SUB_ITEM}{label}: {text}"] if text else []


def voted(vote: JsonMap) -> str:
    """A vote's lens and word for the page. A TRUE_POSITIVE without four YES comes from the
    workflow as a FALSE_POSITIVE that keeps its word in `said`. The page says so,
    and names each question answered NO, since the reasoning argues for the word that was given."""
    said = ""
    if vote.get("said") == CONFIRMS:
        no = [key for key in QUESTIONS if at(vote, key, "answer") != "YES"] or ["a question"]
        said = f": it said {CONFIRMS}, but answered NO to {', '.join(no)}"
    return f"{vote['lens']}, {vote['verdict']}{said}"


def uncalled(row: Row) -> bool:
    """Whether at least PANEL_KEEP_QUORUM verifiers rejected a finding only because nothing calls or
    runs the flawed code yet."""
    return sum(vote.get("uncalled") is True for vote in row["votes"]) >= PANEL_KEEP_QUORUM


def spelled(file: str | None, line: int | None) -> str:
    """The `file` and `line` of a line of the JSONL, for the page."""
    name = percent(unpercent(clean(file)), percent_sign=False)
    return f"{name}:{line}" if name and line is not None else name


def page_entry(row: Row) -> list[str]:
    """One finding on the page: its tool's words, its `found_at` if it has one, the count of its
    votes, NO_CALLER if uncalled() holds, the agents' words, then each file that a verifier was
    refused. Only a finding that the ordering agent ranked has a number."""
    location = spelled(row["file"], row["line"])
    elsewhere: list[str] = []
    if spot := row["found_at"]:
        elsewhere.append(
            f"{SUB_ITEM}That file was not found in the triage's folder. A verifier found the flaw "
            f"at {quoted(spelled(spot['file'], spot['line']))}."
        )
    bullet = f"{row['order']}." if row["why"] else "-"
    grade = f"{row['severity']}: " if row["severity"] else ""
    reasons = [
        line
        for vote in row["votes"]
        for line in agent_line(f"A verifier's reasoning ({voted(vote)})", vote.get("reasoning"))
    ]
    refused = [
        f"{SUB_ITEM}A verifier was refused a file ({vote['lens']}): "
        f"{quoted(vote.get('unopened_file'), 'it named none')}"
        for vote in row["votes"]
        if vote.get("verdict") == UNREAD
    ]
    return [
        (
            f"{bullet} **{row['id']}** {grade}{quoted(row['rule'], 'no rule')} at "
            f"{quoted(location, 'no file')}: {quoted(row['title'], 'no title')} (SARIF level "
            f"{quoted(row['rating'], 'none')}, from "
            f"{quoted(row['tool'], 'an unnamed tool')})"
        ),
        *elsewhere,
        f"{SUB_ITEM}{row['checks']}",
        *(
            agent_line(
                f"{quoted(spelled(note['file'], note['line']))} could excuse this flaw. The triage "
                "took that into account and reports it anyway",
                note["why"],
            )
            if (note := row["overruled"])
            else []
        ),
        *([f"{SUB_ITEM}{NO_CALLER}"] if uncalled(row) else []),
        *agent_line("CWE id", row["cwe_id"]),
        *agent_line("Why this priority", row["why"]),
        *reasons,
        *refused,
    ]


def page_text(opening: list[str], rows: list[Row]) -> str:
    """The page: the `opening` paragraphs of the closing message, each finding under its verdict,
    and a last section on how a finding is judged."""
    blocks = ["# Findings triage", *opening]
    for verdict, heading in HEADINGS.items():
        if held := [row for row in rows if row["verdict"] == verdict]:
            blocks += [f"## {heading} ({len(held)})"]
            blocks += [REJECTED_REAL] if verdict == NOT_VALIDATED else []
            blocks += ["\n".join(line for row in held for line in page_entry(row))]
    return "\n\n".join([*blocks, "## About this report", HOW])


def cleared(result: JsonMap) -> JsonMap:
    """A SARIF result without a triage's verdict and suppression."""
    properties, suppressions = result.get("properties"), result.get("suppressions")
    if is_map(properties):
        result = {**result, "properties": {k: v for k, v in properties.items() if k != TRIAGE_KEY}}
    if is_list(suppressions):
        kept = [s for s in suppressions if not is_map(at(s, "properties", TRIAGE_KEY))]
        result = {**result, "suppressions": kept}
    return result


def triaged(result: JsonMap, row: Row, folder: str) -> JsonMap:
    """A SARIF result with the verdict of `row` from the triage whose results are in `folder`, in
    place of an earlier triage's, and suppressed if it was not validated, uncalled() does not hold
    and it has no other suppression."""
    result = cleared(result)
    verdict = {key: value for key, value in row.items() if key not in LISTS_OWN}
    suppression = {
        "kind": "external",
        "status": "accepted",
        "justification": (
            f"The Claude Security plugin's triage did not validate {row['id']}: {row['checks']}"
        ),
        "properties": {TRIAGE_KEY: {"report": folder}},
    }
    suppressed = (
        row["verdict"] == NOT_VALIDATED
        and not uncalled(row)
        and not maps(result.get("suppressions"))
    )
    return {
        **result,
        "properties": {
            **as_map(result.get("properties")),
            TRIAGE_KEY: {**verdict, "report": folder},
        },
        **({"suppressions": [suppression]} if suppressed else {}),
    }


def run_with_verdicts(
    run: object, number: int, verdicts: dict[tuple[int, int], Row], folder: str
) -> object:
    """Run `number` of a list, with each result that `verdicts` places in it triaged. Where one of
    its results has an array of suppressions, each gets one, as SARIF asks. A null is none."""
    results = at(run, "results")
    if not (is_map(run) and is_list(results)):
        return run
    done: list[object] = [
        triaged(result, verdicts[number, index], folder)
        if is_map(result) and (number, index) in verdicts
        else result
        for index, result in enumerate(results)
    ]
    if any(is_map(result) and is_list(result.get("suppressions")) for result in done):
        done = [
            {**r, "suppressions": r.get("suppressions") or []} if is_map(r) else r for r in done
        ]
    return {**run, "results": done}


def log_with_verdicts(
    log: JsonMap, rows: list[Row], places: dict[str, list[int]], folder: str
) -> JsonMap:
    """The list's `log` with each row's verdict on the result at its place."""
    verdicts: dict[tuple[int, int], Row] = {}
    for row in rows:
        run, index = places[row["id"]]
        verdicts[run, index] = row
    runs = cast("list[object]", log["runs"])
    return {**log, "runs": [run_with_verdicts(r, n, verdicts, folder) for n, r in enumerate(runs)]}


def stamp(results: Path, base: PatchBase) -> None:
    """Write the revision stamp, which says that the directory holds a triage's results. Its `dirty`
    is patch_base()'s, which leaves SARIF files and the list's own file out."""
    revision: Revision = {
        "versioned": bool(base["top"]),
        "commit": base["commit"],
        "dirty": base["dirty"],
    }
    content = {
        "mode": plugin.TRIAGE_STAMP_MODE,
        "plugin_version": plugin.version(),
        "scan_prefix": "",
        "revision": revision,
    }
    path = results / plugin.revision_stamp_name(revision_tag(revision))
    path.write_bytes(encoded(content, indent=1))


def report(args: Args) -> None:
    """Join the votes to the findings as load laid them out. Write the page, the JSONL, the SARIF
    file, the findings for Suggest patches if patches can be offered, and the stamp. Remove the run
    directory, and print the closing message, which ends on the offer if there is one."""
    output, run_dir, votes = workflow_result(args.output_file)
    results = run_dir.parent
    run = cast("Run", strictjson.load(run_dir / RUN_JSON))
    found = {
        name: cast("Listed", strictjson.load(run_dir / FINDINGS_DIR / f"{name}.json"))
        for name in votes
    }
    root = os.path.abspath(results.parent)
    rows = ranked_rows(found, votes, maps(at(output, "result", "order")), run, root)
    valid = [row for row in rows if row["verdict"] == VALID]
    fixes = [
        row for row in valid if run["dirty"] is False and patchable(at_found_place(row), run["top"])
    ]
    opening = [
        f"Results for {run['which']}: {verdict_counts(rows)}.{run['more']}",
        *summary_lines(rows, run, fixes, failures(output)),
    ]
    (results / plugin.TRIAGE_MD_NAME).write_bytes(encoded(page_text(opening, rows)))
    (results / TRIAGE_JSONL_NAME).write_bytes(encoded(*rows))
    log = cast("JsonMap", strictjson.load(run_dir / LIST_JSON))
    copy = log_with_verdicts(log, rows, run["places"], results.name)
    (results / TRIAGE_SARIF_NAME).write_bytes(encoded(copy, indent=COPY_INDENT))
    if fixes:
        handed = (
            {key: value for key, value in at_found_place(row).items() if key not in NOT_HANDED}
            for row in fixes
        )
        (results / plugin.JSONL_NAME).write_bytes(encoded(*handed))
    stamp(results, run)
    stays = ""
    try:
        remove_tree(run_dir)
    except OSError as error:
        detail = console.removal_failure_detail(error)
        stays = (
            f"The folder {results.name}/{run_dir.name} could not be removed ({detail}). "
            "You can delete it."
        )
    where = (
        f"The report is `{results.name}/{plugin.TRIAGE_MD_NAME}`. It lists each finding under its "
        f"verdict, with the valid ones in the order to fix them. {TRIAGE_JSONL_NAME}, in the same "
        f"folder, has one finding per line. {TRIAGE_SARIF_NAME} is the list with the verdicts "
        "added. It marks each finding that was not validated as suppressed, unless another tool or "
        "person's suppression of it is under review or rejected, or the report says under it that "
        "it is not marked."
    )
    warning = plugin.worktree_warning(results)
    closing = (*opening, where, warning, stays, offer(fixes) if fixes else "")
    if fixes:
        print(f"report_dir: {results.name}")
    print(
        "relay: say this to the user exactly as printed, adding and leaving out nothing; then end "
        "your turn, whatever they asked for before"
    )
    print("\n\n".join(filter(None, closing)))


class Args(argparse.Namespace):
    """The parsed command line, whichever form it takes."""

    form: str = ""
    source: str = ""
    first: int = 1
    output_file: str = ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="triage.py", allow_abbrev=False)
    forms = parser.add_subparsers(dest="form", required=True)
    forms.add_parser("lists", allow_abbrev=False)
    for form in ("count", "load"):
        one = forms.add_parser(form, allow_abbrev=False)
        one.add_argument("source")
        one.add_argument("--from", dest="first", type=int, default=1, metavar="<place>")
    forms.add_parser("report", allow_abbrev=False).add_argument("output_file")
    args = parser.parse_args(argv, namespace=Args())
    if args.form == "report" and not os.path.isfile(args.output_file):
        parser.error("give the output file that the completion notice names")
    try:
        {"lists": lists, "count": count, "load": load, "report": report}[args.form](args)
    except TriageError as error:
        sys.stderr.write(f"triage.py: {error}\n")
        return 1
    except (OSError, ValueError, RecursionError) as error:
        sys.stderr.write(
            f"triage.py: The triage stopped on an error: {error}. Fix the cause and ask me to try "
            "again, or start a new triage.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:]))
