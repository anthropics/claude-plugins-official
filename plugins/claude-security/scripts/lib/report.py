"""The Markdown report of one scan."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Final

from . import plugin
from .finding import PANEL_KEEP_QUORUM, Severity, panel_complete, percent
from .markdown import code, inline, literal, location, span, under_a_heading
from .strictjson import is_int, is_list, is_map, is_str, maps

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .finding import AlsoAt, FiledAt, Finding, FindingPathError, Panel
    from .sarif import Scan
    from .strictjson import JsonMap

_FINDINGS: Final = "Findings"
_OLDER: Final = "Older than the change"
_REPORT_ONLY: Final = "Findings in this report only"
_SECTIONS: Final = {
    _FINDINGS: "",
    _OLDER: (
        f"Fewer than {PANEL_KEEP_QUORUM} verifiers found that the change takes part in these "
        "flaws, and at least one judged each real but older than the change."
    ),
    _REPORT_ONLY: (
        "The scan could not tie any finding below to a file in the scanned code, so the JSONL and "
        "SARIF files leave it out. Confirm where the flaw is before you act on it."
    ),
}
_HOW_A_SCAN_WORKS: Final = (
    "Researchers read the code and raise candidate findings. Independent verifiers then try to "
    "disprove each one from the code, one each on reachability, impact and defenses. Where two of "
    "them settle the result, a third vote is not needed, so 2 of 2 is a complete panel. The "
    "scan's agents are told to read the repository's code, and never to build, test or execute "
    "it. Take each finding as derived from reading, not as demonstrated."
)
_NOT_CONFIRMED: Final = (
    "The lens verifiers' votes do not confirm the text under Impact, Exploit scenario, "
    "Preconditions or Fix."
)
_FIX_LABEL: Final = "Fix (not verified)"
_OWN_HEADING: Final = re.compile(r"\A\s*#+[ \t]*Coverage[ \t:#\r]*(?:\n|\Z)", re.IGNORECASE)
_REPORTED_BUT: Final = ": reported, but "
_RAISE: Final = re.compile(r"(\S+): (\w+) raised from (\w+) to (\w+),")


def session_text(written: str) -> str:
    """The session's Coverage text `written`, as the report prints it."""
    return under_a_heading(_OWN_HEADING.sub("", written))


def scan_report(
    scan: Scan,
    target: str,
    stamp: JsonMap,
    findings: Sequence[Finding],
    refused: Sequence[FindingPathError],
    *,
    rounds: JsonMap,
    digest_differs: bool,
    disclosed: Sequence[str],
    listed: Mapping[str, Finding],
    session_coverage: str,
    coverage: JsonMap | None,
    account: str,
) -> str:
    """The Markdown report of `scan`. `target` names the scanned code. `stamp` is the revision
    stamp, `findings` are the JSONL's, and `refused` are the findings refused for their paths.
    `rounds` are the vote record's, and `digest_differs` says that they are for another list, so no
    entry states them and no line of severityLowered prints. `disclosed` has one sentence for each
    finding merged into another and each replaced report left out, and `listed` holds each listed
    finding in full, by its id. `session_coverage` is what session_text() returns, `coverage` is
    coverage.json, and `account` opens "What was verified"."""
    wrong = {error.finding_id: error.wrong for error in refused}
    shown = [*findings, *(error.finding for error in refused)]
    grades = {(f["id"], grade): f[grade] for f in shown for grade in ("severity", "confidence")}
    scan_lines = _scan_lines(coverage or {}, digest_differs)
    lines = [told for line in scan_lines if (told := _raise_told(line, grades))]
    entry_of = {named["id"]: f["id"] for f in shown for named in (f, *f["also_at"])}

    def lines_at(name: str | None) -> list[str]:
        """The scan's lines for the entry of `name`. For None, its lines for no entry."""
        return [line for line in lines if entry_of.get(line.partition(":")[0]) == name]

    def section_of(finding: Finding) -> str:
        if finding["id"] in wrong:
            return _REPORT_ONLY
        return _OLDER if "older_than_the_change" in finding else _FINDINGS

    def entry(finding: Finding) -> str:
        name = finding["id"]
        panel = panel_complete(rounds.get(name))
        tally = _VOTES_ON_ANOTHER_LIST if digest_differs else _tally(panel)
        return _entry(finding, tally, listed, wrong.get(name, ""), lines_at(name))

    sections = {
        heading: found
        for heading in _SECTIONS
        if (found := [f for f in shown if section_of(f) == heading]) or heading == _FINDINGS
    }
    parts = [
        "# Claude Security results",
        _opening(
            scan,
            target,
            stamp,
            sections,
            "returned with their reading" if without_diff(coverage) else "returned",
        ),
        "## Coverage",
        session_coverage,
        _recorded(coverage, [*lines_at(None), *disclosed], several=len(shown) > 1),
        *(
            part
            for heading, found in sections.items()
            for part in (
                f"## {heading}",
                _SECTIONS[heading],
                *(map(entry, found) if found else ["None."]),
            )
        ),
        "## What was verified",
        account,
        _HOW_A_SCAN_WORKS,
        _NOT_CONFIRMED if shown else "",
        _context(coverage or {}),
    ]
    return percent("\n\n".join(filter(None, parts)) + "\n", percent_sign=False)


def _map_at(record: JsonMap, key: str) -> JsonMap:
    """The object that `record` holds under `key`."""
    held = record.get(key)
    return held if is_map(held) else {}


def _fact(held: object) -> str:
    """A value of the stamp as the opening prints it: a string as code, and a number as it is.
    Empty for any other value."""
    return code(held) if is_str(held) else str(held) if is_int(held) else ""


MODES: Final = {
    "scan": "Scan codebase",
    "changes": "Scan changes",
    "commit": "Scan changes, one commit",
}
_NOT_COVERED: Final = (
    "; the reading of the others is missing from this scan, and the verification status does not "
    "cover it"
)


def without_diff(coverage: JsonMap | None) -> int:
    """How many researchers coverage.json lists as returned without the change's diff."""
    lost = maps((coverage or {}).get("lostResearchers"))
    return sum(one.get("diffRead") is False for one in lost)


def _opening(
    scan: Scan,
    target: str,
    stamp: JsonMap,
    sections: Mapping[str, Sequence[Finding]],
    returned: str,
) -> str:
    """The report's opening: one line for each label whose fact is not empty. `returned` is the
    word for the researchers that the stamp counts as returned."""
    revision, shape, verification = (
        _map_at(stamp, key) for key in ("revision", "run_shape", "verification")
    )
    commit, branch = revision.get("commit"), revision.get("branch")
    dirty = revision.get("dirty", None if commit else False)
    sent = verification.get("researchers_dispatched")
    back = verification.get("researchers_returned")
    facts = {
        "Scanned": code(target),
        "Mode": MODES[scan.mode],
        "Scope": ", ".join(code(scan.prefix + path) for path in scan.scope) or code(scan.prefix),
        "Commit": _fact(commit) or "the scan recorded none",
        "Branch": "none (a detached checkout)" if branch == "HEAD" else _fact(branch),
        "Base": _fact(revision.get("base")),
        "Working tree": (
            "held uncommitted changes or untracked files"
            if dirty is True
            else ""
            if dirty is False
            else "its state could not be determined"
        ),
        "Effort": _fact(stamp.get("effort")),
        "Change Scan Effort": _fact(stamp.get("change_scan_effort")),
        "Changed files": _fact(shape.get("diff_files")),
        "Changed lines": _fact(shape.get("diff_lines")),
        "Report written": _fact(stamp.get("generated_at")),
        "Researchers": (
            f"{back} of {sent} {returned}" + (_NOT_COVERED if 0 < back < sent else "")
            if is_int(sent) and is_int(back)
            else ""
        ),
        **{heading: _by_severity(found) for heading, found in sections.items()},
        "Verification status": f"**{verification['status']}**",
    }
    return "\n".join(f"- {label}: {fact}" for label, fact in facts.items() if fact)


def _by_severity(findings: Sequence[Finding]) -> str:
    """How many `findings` there are, and in brackets how many at each severity."""
    counts = Counter(finding["severity"] for finding in findings)
    return f"{len(findings)} ({', '.join(f'{counts[s.name]} {s.name}' for s in Severity)})"


def _texts(held: object) -> list[str]:
    """The strings in a list of coverage.json."""
    return [text for text in (held if is_list(held) else []) if is_str(text)]


def _scan_lines(coverage: JsonMap, digest_differs: bool) -> list[str]:
    """The lines that workflows/scan.js and save_result.py wrote into coverage.json for the
    report, less those of severityLowered where `digest_differs` says that the votes that they
    state are for another list."""
    lowered = () if digest_differs else ("severityLowered",)
    lists = (
        *lowered,
        "raised",
        "replacedNotKept",
        "preconditionsNotKept",
        "pathsMended",
        "droppedOnDocuments",
    )
    casualties = _texts(coverage.get("adversarialCasualties"))
    return [
        *(line for key in lists for line in _texts(coverage.get(key))),
        *(line for line in casualties if _REPORTED_BUT in line),
        *_texts([_map_at(coverage, "lastReport").get("text")]),
        *_texts(_map_at(_map_at(coverage, "laterResearch"), "leftOut").get("lines")),
    ]


def _raise_told(line: str, grades: Mapping[tuple[str, str], str]) -> str | None:
    """`line` as a report prints it, or None if it prints no such line. `grades` holds each grade
    that the report shows, by the finding's id and the grade's name."""
    raised = _RAISE.match(line)
    if raised is None:
        return line
    finding, grade, old, new = raised.groups()
    shown = grades.get((finding, grade), new)
    if shown == new:
        return line
    return None if shown == old else f"{line}; the entry shows {shown}"


def _lost(researcher: JsonMap) -> str:
    """Whether a researcher whose reading is missing returned, what it was sent to read, and the
    recorded reason."""
    reading, why = researcher.get("reading"), researcher.get("reason")
    sent = f"sent to read {reading}" if is_str(reading) and reading else "with no recorded reading"
    reason = f'recorded reason: "{why}"' if is_str(why) and why else "no reason recorded"
    what = "Returned without the diff" if researcher.get("diffRead") is False else "Did not return"
    return f"{what}: the researcher {sent} ({reason})"


_NO_COVERAGE_RECORD: Final = (
    "The scan's record of its coverage is missing or could not be read, so this section may be "
    "incomplete."
)
_OLDER_CHECKS: Final = (
    "At Change Scan Effort high, a flaw in a check that the change adds or tightens, or in another "
    "path to the same operation that lacks the check, can be reported even where it is older than "
    "the change."
)
_SAME_FLAW: Final = (
    "Some findings in this report may describe the same flaw: the scan could not rule that out "
    "for all of them."
)


def _recorded(coverage: JsonMap | None, lines: Sequence[str], *, several: bool) -> str:
    """What the report adds to the session's Coverage text, as a list: `lines`, and what
    coverage.json calls for. `several` says that the report has more than one finding."""
    held = coverage or {}
    lost = held.get("lostResearchers")
    said = [
        *([_NO_COVERAGE_RECORD] if coverage is None else []),
        *([_OLDER_CHECKS] if plugin.at_change_scan_effort_high(held) else []),
        *([_SAME_FLAW] if several and _texts(held.get("findingsNotJoined")) else []),
        *lines,
        *map(_lost, filter(is_map, lost if is_list(lost) else [])),
    ]
    bullets = [f"- {line}" for line in map(inline, said) if line]
    return "\n".join(["From the scan's records:", "", *bullets]) if bullets else ""


CONTEXT_WARNING: Final = (
    "A wrong or outdated statement in what this scan was given can lower a flaw's severity, or "
    "keep the flaw out of the report."
)
CONTEXT_LOST: Final = (
    "No summary of it came back, so the scan's researchers did not get it. A new scan may do "
    "better."
)


def _context(coverage: JsonMap) -> str:
    """The section on coverage.json's `context`: what the scan was given, a warning or that no
    summary of it came back, and what of it is not confirmed as read. Empty where it names
    nothing."""
    context = plugin.context_of(coverage)
    if context is None:
        return ""
    given, unread = ("; ".join(map(span, _texts(context.get(key)))) for key in ("given", "unread"))
    lost = context.get("summaryLost") is True
    bullets = [f"- This scan was given: {given}.", f"- {CONTEXT_LOST if lost else CONTEXT_WARNING}"]
    if unread:
        bullets.append(
            f"- These are not confirmed as read in full: {unread}. A wrong path, a path outside "
            "the scanned folder, a permission rule, a file's length, a control character in a "
            "name, or more than 10 files can be the reason."
        )
    return "\n".join(["## Context for this scan", "", *bullets])


_NONE_STATED: Final = "none stated"


def _entry(
    finding: Finding,
    tally: str,
    listed: Mapping[str, Finding],
    wrong: str,
    notes: Sequence[str],
) -> str:
    """One finding's entry: its heading, then each labeled part that its record states. `tally`
    tells of the panel's votes. `wrong` says what is wrong with the path of a refused finding.
    `notes` are the scan's lines on the finding and on those that it lists."""
    preconditions = "\n".join(f"- {item}" for item in map(inline, finding["preconditions"]) if item)
    rated = f"({finding['severity']}, confidence {finding['confidence']})"
    parts = [
        f"### {finding['id']} — {inline(finding['title'])} {rated}",
        _labeled("Impact", finding["impact"]),
        f"**Where.** {_where(finding, wrong)}",
        _also_at(finding, listed),
        _also_filed_at(finding),
        _labeled("Link to the change", finding["via_change"] or ""),
        _labeled("What", finding["description"]),
        _labeled("Exploit scenario", finding["exploit_scenario"]),
        f"**Preconditions.**\n\n{preconditions}"
        if preconditions
        else f"**Preconditions.** {_NONE_STATED.capitalize()}.",
        _labeled(_FIX_LABEL, finding["recommendation"]),
        f"**Verification.** {'. '.join([tally, *map(inline, notes)])}.",
    ]
    return "\n\n".join(filter(None, parts))


def _labeled(label: str, text: str) -> str:
    """One labeled part of a finding. Empty if the record states nothing for it."""
    shown = literal(text)
    return f"**{label}.** {shown}" if shown else ""


def _cwes(held: Finding | FiledAt) -> str:
    """The CWE id of a finding or of a report, then its other CWE ids."""
    others = ", ".join(held["other_cwe_ids"])
    return f"{held['cwe_id']} (also {others})" if others else held["cwe_id"]


def _where(finding: Finding, wrong: str) -> str:
    """A finding's file, line, symbol and CWE ids. A refused finding shows no file, and says
    `wrong`."""
    file = "" if wrong else location(finding["file"], finding["line"])
    place = " in ".join(filter(None, [file, code(finding["symbol"])]))
    where = " — ".join(filter(None, [place, _cwes(finding)]))
    if not wrong:
        return where
    return f"{where}. No file is listed: the path that the scan recorded {wrong}."


_ALSO_AT: Final = (
    "**Also reached at.** Each finding below can have a fix and preconditions of its own, and "
    "nothing has checked them against this finding's. The flaw can affect you if the preconditions "
    "of any one of them fit you."
)


def _also_at(finding: Finding, listed: Mapping[str, Finding]) -> str:
    """One bullet for each finding that `finding` lists. Under it stand its fix, unless that prints
    the same as the fix of `finding`, and its preconditions. Empty if it lists none."""
    own_fix = inline(finding["recommendation"])

    def bullet(other: AlsoAt) -> str:
        fix = inline(other["recommendation"])
        needs = "; ".join(filter(None, map(inline, listed[other["id"]]["preconditions"])))
        place = location(other["file"], other["line"])
        rated = f"{other['cwe_id']}, {other['severity']}"
        return "\n".join([
            f"- {other['id']} — {place} — {rated}: {inline(other['title'])}",
            *([f"    - {_FIX_LABEL}: {fix}"] if fix and fix != own_fix else []),
            f"    - Preconditions: {needs or _NONE_STATED}",
        ])

    bullets = map(bullet, finding["also_at"])
    return "\n".join([_ALSO_AT, "", *bullets]) if finding["also_at"] else ""


_FILED_AT: Final = (
    "**Also filed at.** This finding replaces one or more researchers' reports at each of these "
    "places. None of those reports had a panel of its own."
)


def _also_filed_at(finding: Finding) -> str:
    """One bullet for each place where the finding replaces reports. Empty if there is none."""
    bullets = [
        f"- {location(at['file'], at['line'])} — {_cwes(at)}: {inline(at['title'])}"
        for at in finding.get("also_filed_at", [])
    ]
    return "\n".join([_FILED_AT, "", *bullets]) if bullets else ""


_VOTES_ON_ANOTHER_LIST: Final = "The panel's votes do not cover this list"


def _tally(panel: Panel | None) -> str:
    """How many verifiers of a finding's complete panel confirmed it, or that it has none."""
    if panel is None:
        return "No complete panel is recorded"
    predates = panel.get("predates", 0)
    older = f", {predates} of them as a flaw older than the change" if predates else ""
    return f"{panel['true']} of {panel['voters']} verifiers confirmed the flaw{older}"
