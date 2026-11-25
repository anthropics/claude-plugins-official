"""The last report on the same scan target: its findings whose code has not changed."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, TypedDict

from . import git, history, plugin, sarif, source, strictjson
from .candidates import CHUNK, LastReport, candidate_files
from .cwe import catalog
from .finding import (
    FINDING_ID,
    OVERRULED_NOTE,
    FindingError,
    Severity,
    confidence_value,
    cwe_number,
    other_cwe_numbers,
    repository_file,
    unpercent,
)
from .link import is_link
from .products import ProductError, Stamp, records
from .strictjson import clean, is_list, is_str

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from .strictjson import JsonMap

RESEARCH_RUN = 1
SCAN_MODES = ("scan", plugin.STAMP_MODES["scan"])
ROW_TEXTS = {
    "symbol": "symbol",
    "impact": "impact",
    "exploit_scenario": "exploitScenario",
    "recommendation": "recommendation",
}


class Rows(TypedDict):
    """What the scan job hands to workflows/scan.js as `lastReport`: how many candidate rows were
    written, and how many rows a file holds."""

    held: int
    rowsPerFile: int


def _extent(scope: Collection[str]) -> frozenset[str]:
    return frozenset(entry.strip("/") for entry in scope)


def _can_be_of_repository(scan_root: str, commit: str | None) -> bool:
    """Whether a report stamped with `commit` can be of the repository at `scan_root`: the
    repository holds that commit or, where the stamp has none, its HEAD names no commit yet. A
    partial clone takes no report that stamps a commit, since asking for that commit can fetch."""
    if commit and history.partial_clone(scan_root):
        return False
    no_fetch = {"GIT_NO_LAZY_FETCH": "1"}
    found = git.run(scan_root, "cat-file", "-e", commit or "HEAD", env=no_fetch) is not None
    return found == bool(commit)


def target_of(report: Path) -> tuple[str, frozenset[str]] | None:
    """The scan_prefix and the scope of `report`, if it is a verified report of a codebase scan
    whose stamp can be read; else None. A symbolic link or a directory junction is not followed."""
    try:
        if is_link(report) or any(is_link(each) for each in report.iterdir()):
            return None
        stamp = Stamp.read(report)
    except (OSError, ProductError):
        return None
    if not (stamp.verified and stamp.mode in SCAN_MODES):
        return None
    return stamp.prefix, _extent(stamp.scope)


def _findings(
    report: Path, scan_root: str, prefix: str, scope: Collection[str]
) -> list[JsonMap] | None:
    """The records of `report`, if its target is this scan_prefix and scope, it can be of the
    repository at `scan_root`, and they can be read; else None."""
    if target_of(report) != (prefix, _extent(scope)):
        return None
    try:
        if not _can_be_of_repository(scan_root, Stamp.read(report).commit):
            return None
        return records(report / plugin.JSONL_NAME, required=True)
    except (OSError, ProductError):
        return None


def _candidate(
    record: JsonMap, scan_root: str, prefix: str, files: Collection[str]
) -> dict[str, object] | None:
    """`record` as a candidate row without its id, on the line where its file now holds the quote
    with the same lines around it. None if the record is not whole, its file is not among `files`
    or cannot be read, or the file does not hold the quote with those lines around it in exactly
    one place."""
    file, severity = record.get("file"), Severity.of(record)
    title, rationale = clean(record.get("title")), clean(record.get("description"))
    head, _, last = rationale.rpartition("\n\n")
    if head and OVERRULED_NOTE in last:
        rationale = head.strip()
    if not (is_str(file) and severity and title and rationale):
        return None
    try:
        confidence = confidence_value(record.get("confidence"))
        cwe = cwe_number(record, "")
        others = other_cwe_numbers(record, "", cwe)
    except FindingError:
        return None
    name = unpercent(file)
    text = source.read(scan_root, name) if name in files else None
    if text is None:
        return None
    lines = source.normalized_lines(text)
    quote = clean(record.get("snippet"))
    rule, path = sarif.rule_id(catalog.category(cwe)), repository_file(prefix, file=name)
    own = {
        row
        for first, last in source.occurrences(lines, " ".join(quote.split()))
        for row in range(first, last + 1)
        if sarif.keyed(rule, path, sarif.code_at(lines, row)) == record.get(FINDING_ID)
    }
    if len(own) != 1:
        return None
    preconditions = record.get("preconditions")
    return {
        "file": name,
        "line": own.pop() + 1,
        "cweId": f"CWE-{cwe}",
        "severity": severity.name,
        "confidence": confidence.name.upper(),
        "title": title,
        "rationale": rationale,
        "snippet": quote,
        **{key: held for field, key in ROW_TEXTS.items() if (held := clean(record.get(field)))},
        "preconditions": [each for each in preconditions if is_str(each)]
        if is_list(preconditions)
        else [],
        "otherCweIds": [f"CWE-{number}" for number in others],
    }


def write_last_findings(
    run_dir: Path,
    scan_root: str,
    prefix: str | None,
    scope: Collection[str],
    files: Collection[str] | None,
) -> Rows | None:
    """Write the findings of the last report whose code has not changed, in a file among `files`,
    into the run directory, as the research run's candidate files, and plugin.LAST_REPORT_NAME
    beside them. A finding whose id another finding of that report has is left out. The last report
    is the newest of the report directories beside this scan's own that _findings takes. None where
    no row is written; with no last report, or one with no finding, no prefix or no `files`, nothing
    is written at all."""
    if not files or prefix is None:
        return None
    beside = sorted(
        (each for each in run_dir.parent.parent.iterdir() if plugin.REPORT_DIR_RE.match(each.name)),
        reverse=True,
    )
    last = next(
        (
            (each, found)
            for each in beside
            if (found := _findings(each, scan_root, prefix, scope)) is not None
        ),
        None,
    )
    if last is None or not last[1]:
        return None
    report, found = last
    tracked = frozenset(files)
    ids = Counter(clean(each.get(FINDING_ID)) for each in found)
    held = [
        row
        for each in found
        if ids[clean(each.get(FINDING_ID))] == 1
        and (row := _candidate(each, scan_root, prefix, tracked))
    ]
    rows = [{"cid": f"C{number}", **row} for number, row in enumerate(held, start=1)]
    taken = LastReport(report=report.name, findings=len(found), held=len(rows))
    files_to_write = [
        (plugin.LAST_REPORT_NAME, taken),
        *candidate_files(run_dir, RESEARCH_RUN, rows),
    ]
    for name, content in files_to_write:
        (run_dir / name).write_bytes((strictjson.text(content, indent=1) + "\n").encode())
    return Rows(held=len(rows), rowsPerFile=CHUNK) if rows else None
