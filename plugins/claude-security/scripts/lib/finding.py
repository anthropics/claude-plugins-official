"""The Finding every product is built from, and build_finding, which validates a raw one."""

from __future__ import annotations

import ntpath
import os
import re
from typing import TypedDict

from . import absolute, cwe
from .strictjson import JsonMap, has_lone_surrogate, is_int, is_list, is_map, is_str


class Panel(TypedDict):
    """A validated panel round: the vote counts and the fixed voter count."""

    true: int
    false: int
    voters: int


class Finding(TypedDict):
    """One validated finding, in the JSONL record's field order; the record adds the id (Record)."""

    id: str
    title: str
    impact: str
    file: str
    line: int
    description: str
    exploit_scenario: str
    preconditions: list[str]
    category: str
    severity: str
    confidence: str
    recommendation: str
    cwe_id: str
    snippet: str
    symbol: str
    declared_line: int


class Record(Finding):
    """A finding as every product carries it: placed on its line (sarif.placed), its id last."""

    claudeSecurityPluginFindingId: str


SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
CONFIDENCES = ("low", "medium", "high")
CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}

PANEL_VOTER_COUNT = 3
PANEL_KEEP_QUORUM = 2

# \Z, not $: `$` also matches before a trailing newline, and this names a file.
FINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")


class FindingError(Exception):
    """A refusal; the message names what a findings.json record got wrong."""


class FindingPathError(FindingError):
    """A refusal of one finding's model-written path; the rest of a report can still carry.

    The message names the finding and quotes the declared path; `finding_id`
    and `wrong` (what is wrong with the path, without the path) are what a
    caller surviving the refusal may record in a product.
    """

    finding_id: str
    wrong: str
    cwe: int = 0
    snippet: str = ""

    def __init__(self, finding_id: str, *, declared: str, wrong: str) -> None:
        super().__init__(f"finding {finding_id} file {declared!r} {wrong}")
        self.finding_id = finding_id
        self.wrong = wrong


def cwe_number(item: JsonMap, finding_id: str) -> int:
    """A finding's CWE number; a cwe_id missing, unreadable or malformed is refused.

    A well-formed id is accepted as declared, whether or not the pinned CWE
    release defines it; one the release does not define files the finding
    under Uncategorized, and the renderer discloses the substitution.
    """
    declared = text_field(item, "cwe_id", finding_id, required=True)
    matched = re.fullmatch(
        r"(?:CWE-)?0*([1-9][0-9]{0,4})", declared.strip().upper().replace("_", "-")
    )
    if not matched:
        msg = f"finding {finding_id} cwe_id {declared!r} is not a CWE id such as CWE-89"
        raise FindingError(msg)
    return int(matched[1])


def confidence_value(raw: object) -> str:
    """A finding's stated confidence, normalized to low|medium|high; refuses others."""
    if is_str(raw):
        word = raw.strip().lower()
        if word in CONFIDENCE_RANK:
            return word
    msg = f"confidence {raw!r} is not one of {'/'.join(CONFIDENCES)}"
    raise FindingError(msg)


def panel_complete(record: object) -> Panel | None:
    """One round record's panel when the full voter count returned an integer tally, else None."""
    if not is_map(record):
        return None
    panel = record.get("panel")
    if not is_map(panel):
        return None
    panel_true = panel.get("true")
    if not is_int(panel_true):
        return None
    if panel.get("voters") != PANEL_VOTER_COUNT:
        return None
    false_votes = panel.get("false")
    return {
        "true": panel_true,
        "false": false_votes if is_int(false_votes) else 0,
        "voters": PANEL_VOTER_COUNT,
    }


def vote_confidence_ceiling(record: object) -> str | None:
    """A finding's vote-backed confidence: `high` if unanimous, `medium` if complete, else None."""
    panel = panel_complete(record)
    if panel is None:
        return None
    return "high" if panel["true"] >= PANEL_VOTER_COUNT else "medium"


def line_number(raw: object) -> int | None:
    """A findings.json line value as an integer: an int, or digits in a string; None otherwise."""
    if is_str(raw) and re.fullmatch(r"\s*-?[0-9]{1,15}\s*", raw):
        return int(raw)
    return raw if is_int(raw) else None


def line_field(item: JsonMap, key: str, finding_id: str, default: int) -> int:
    """One of a finding's line fields as an integer (line_number); absent reads as `default`."""
    line = line_number(item.get(key, default))
    if line is None:
        msg = f"finding {finding_id} {key} {item.get(key)!r} is not an integer"
        raise FindingError(msg)
    return line


def scan_prefix_shaped(prefix: str) -> bool:
    """Whether `prefix` is what `git rev-parse --show-prefix` prints: empty, or `a/b/`."""
    if not prefix:
        return True
    return (
        prefix.endswith("/")
        and "\\" not in prefix
        and not ntpath.splitdrive(prefix)[0]
        and all(segment not in {"", ".", ".."} for segment in prefix.split("/")[:-1])
    )


def text_field(item: JsonMap, key: str, finding_id: str, required: bool = False) -> str:
    """One of a finding's text fields; absent or null reads as empty unless it is required."""
    value = item.get(key)
    if value is None:
        text = ""
    elif is_str(value):
        text = value
    else:
        msg = f"finding {finding_id} {key} is {type(value).__name__}, not a string"
        raise FindingError(msg)
    if has_lone_surrogate(text):
        msg = f"finding {finding_id} {key} contains an unpaired surrogate"
        raise FindingError(msg)
    if required and not text.strip():
        msg = f"finding {finding_id} is missing required field {key!r}"
        raise FindingError(msg)
    return text


def leaked_spelling(path: str, *, first: str, scan_root: str) -> bool:
    """Whether a path's cross-platform absolute spelling names the machine, not the repository."""
    if not absolute.spelled(path):
        return False
    if os.name == "nt":
        return True
    return not os.path.lexists(os.path.join(scan_root, first))


def file_field(
    item: JsonMap, finding_id: str, scan_root: str, scan_prefix: str, must_exist: bool
) -> str:
    """A finding's file relative to the scan root; a path that leaves the repository is refused.

    `scan_prefix` is the scan root's path below the repository top level (`a/b/`,
    or empty): a file may climb one directory per prefix component and no further.
    A file spelled relative to the top level, absent under the scan root but
    present under the top level, is respelled relative to the scan root.
    With `must_exist` (a codebase scan, whose whole tree is still present when
    the report renders), a path that exists neither under the scan root nor at
    the repository top level is refused.
    A name that merely spells like another platform's absolute path is treated
    as repository content when the scan root holds its first segment.
    """
    declared = text_field(item, "file", finding_id, required=True).strip()
    depth = scan_prefix.count("/")
    escapes = f"escapes the {'repository' if depth else 'scan root'}"
    path = declared.replace("\\", "/")
    prefix = scan_root.replace("\\", "/").rstrip("/") + "/"
    if scan_root and path.startswith(prefix):
        path = path[len(prefix) :].lstrip("/")
    if os.path.isabs(path):
        try:
            path = os.path.relpath(os.path.realpath(path), scan_root).replace("\\", "/")
        except (ValueError, OSError) as error:
            raise FindingPathError(finding_id, declared=declared, wrong=escapes) from error
    parts = [part for part in path.split("/") if part and part != "."]
    climb = next((i for i, part in enumerate(parts) if part != ".."), len(parts))
    inside = parts[climb:]
    if (
        not inside
        or ".." in inside
        or climb > depth
        or leaked_spelling(path, first=parts[0], scan_root=scan_root)
    ):
        raise FindingPathError(finding_id, declared=declared, wrong=escapes)
    if not os.path.lexists(os.path.join(scan_root, *parts)):
        # A file only the repository top level holds was spelled relative to it, not the scan root.
        if depth and not climb:
            at_top = os.path.join(os.path.normpath(os.path.join(scan_root, "../" * depth)), *parts)
            if os.path.lexists(at_top):
                return os.path.relpath(at_top, scan_root).replace("\\", "/")
        if must_exist:
            raise FindingPathError(
                finding_id, declared=declared, wrong="does not exist in the scanned tree"
            )
    return "/".join(parts)


def build_finding(
    raw: object,
    index: int,
    rounds_by_id: JsonMap,
    scan_root: str,
    scan_prefix: str,
    must_exist: bool,
) -> Finding:
    """Validate one raw findings.json record into a Finding."""
    if not is_map(raw):
        msg = f"findings.json item {index} is not an object"
        raise FindingError(msg)
    numbered = f"F{index + 1}"
    finding_id = text_field(raw, "id", numbered) or numbered
    if not FINDING_ID_RE.match(finding_id):
        msg = f"finding id {finding_id!r} is not a valid id"
        raise FindingError(msg)

    severity = str(raw.get("severity", "")).strip().upper()
    if severity not in SEVERITIES:
        msg = (
            f"finding {finding_id} severity {raw.get('severity')!r} is not one of "
            f"{'/'.join(SEVERITIES)}"
        )
        raise FindingError(msg)

    confidence = confidence_value(raw.get("confidence"))
    ceiling = vote_confidence_ceiling(rounds_by_id.get(finding_id))
    if ceiling is not None and CONFIDENCE_RANK[confidence] > CONFIDENCE_RANK[ceiling]:
        confidence = ceiling

    line = line_field(raw, "line", finding_id, 0)
    declared_line = line_field(raw, "declared_line", finding_id, line)

    preconditions: list[str] = []
    declared = raw.get("preconditions")
    if declared is not None:
        if not is_list(declared):
            msg = f"finding {finding_id} preconditions must be a list"
            raise FindingError(msg)
        preconditions = [item for item in declared if is_str(item)]
        if len(preconditions) != len(declared) or any(map(has_lone_surrogate, preconditions)):
            msg = f"finding {finding_id} preconditions must be a list of strings"
            raise FindingError(msg)

    number = cwe_number(raw, finding_id)
    category = cwe.catalog.category(number)
    title = text_field(raw, "title", finding_id, required=True)
    impact = text_field(raw, "impact", finding_id)
    description = text_field(raw, "description", finding_id, required=True)
    exploit_scenario = text_field(raw, "exploit_scenario", finding_id, required=True)
    recommendation = text_field(raw, "recommendation", finding_id)
    snippet = text_field(raw, "snippet", finding_id)
    symbol = text_field(raw, "symbol", finding_id)
    try:
        file = file_field(raw, finding_id, scan_root, scan_prefix, must_exist)
    except FindingPathError as error:
        error.cwe, error.snippet = number, snippet
        raise

    return {
        "id": finding_id,
        "title": title,
        "impact": impact,
        "file": file,
        "line": line,
        "description": description,
        "exploit_scenario": exploit_scenario,
        "preconditions": preconditions,
        "category": category.name if category is not None else cwe.UNCATEGORIZED,
        "severity": severity,
        "confidence": confidence,
        "recommendation": recommendation,
        "cwe_id": f"CWE-{number}",
        "snippet": snippet,
        "symbol": symbol,
        "declared_line": declared_line,
    }
