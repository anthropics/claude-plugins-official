"""One pull request review from a Report: where each finding and its fix can go under GitHub's
placement rules, and the body and inline comments that say so."""

from __future__ import annotations

import enum
from collections import Counter
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, TypedDict

from . import cwe, gfm, sarif, strictjson, unidiff
from .effort import ChangeScanEffort
from .finding import Severity
from .markdown import at_most
from .marker import (
    REF_LIMIT,
    Comment,
    Earlier,
    FindingLine,
    Marker,
    Tag,
    encoded,
    fullest_by_key,
    newest_by_place,
    newest_graded,
    part_line,
    shared_keys,
    still_answers,
)
from .plugin import AI_CAUTION_LINK, CONFIDENT
from .products import Withheld
from .verdict import IN_THIS_CHANGE, FailOn, reading_missing

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping, Sequence

    from .actions import BaseChange
    from .marker import Prior
    from .products import Item, Patch, Recheck, Report, Stamp, Words
    from .verdict import Graded, Verdict

REVIEW_NAME = "REVIEW.md"
REVIEW_HEADING = "## Claude Security plugin review"
# GitHub refuses a review or comment body past 65,536 characters.
BODY_LIMIT = 65000
# An attached patch is cut to this length, to leave room under BODY_LIMIT for its write-up.
ATTACHED_DIFF_LIMIT = 30000
ATTACK_TITLE = "How the attack works"
_ATTACHED_TITLE = "Suggested fix"
ANALYSIS_TITLE = "How the suggested fix was analyzed"
DECLINED_TITLE = "Why no fix is suggested"
ALSO_FOUND_TITLE = "Other problems found while a fix was considered"
_ALSO_FOUND = (
    "The agents that analyzed this finding for a suggested fix also found the problems below. A "
    "fix for this finding does not address them."
)
_FULL_REPORT_TITLE = "Full report"
RECOMMENDATION_TITLE = "The scan's full recommendation (not verified)"
# How many of a finding's other places its write-up gives by name.
_ALSO_SHOWN = 10
# How many of them its table row and the line on the check name.
_ALSO_IN_BRIEF = 3
# How many failing findings the line on the check names.
_FAILING_NAMED = 20
LISTED_POINTER = (
    "This write-up covers two or more findings of one flaw. Each can have its own fix and "
    "preconditions: see this finding's entry in the full report."
)
SPARSE = (
    "The job's checkout was sparse, so files that it left out may not have been scanned. To avoid "
    "this, check out the whole repository."
)
NO_ASSURANCE = "A scan can miss vulnerabilities, so this is no assurance that the code has none."
_NONE_OFFERED = "none offered"
_ADDS_FIXES = (
    "Suggested fixes for the findings that an earlier review of this commit describes. Nothing has "
    "been applied."
)
_ADDS_NO_FIX = (
    "This review adds no suggested fix for the findings that an earlier review of this commit "
    "describes."
)
_NOT_INLINE = "These findings have no suggested fix, or GitHub cannot show it on its lines."
DOTS = {Severity.CRITICAL: "🔴", Severity.HIGH: "🟠", Severity.MEDIUM: "🟡", Severity.LOW: "🔵"}
_GITHUB_SHORT_ID_CHARS = 7
FIX_CAUTION = "Each fix suggestion should be reviewed to ensure it does not break functionality."
# Per repository path, the new-side line ranges of the pull request's diff hunks.
Spans = dict[str, list[tuple[int, int]]]


_OLDER_TITLE: Final = "Older than the change"
_OLDER_WORDS: Final = (
    "The scan found each flaw in this list while it scanned this pull request, and judged it real, "
    "but did not tie it to the pull request's changes. So this list does not count in this check. "
    "A fix can go into this pull request or another one."
)
_EARLIER_COMMENT: Final = "An earlier review's comment on one of them can still count."


class Inputs(NamedTuple):
    """What a review is built from besides the report."""

    spans: Spans
    # The repository's URL, the root of the links the review builds; None outside a pull request.
    home: str | None
    previous: Sequence[str]
    # By finding id, git's diff of each patch a suggestion may be offered from, on this head.
    applied: Mapping[str, str]
    # The plugin's version for the footer; None when its manifest cannot be read.
    version: str | None
    # Set when this run's event changed the base branch and the scan covers the new range.
    base_change: BaseChange | None
    # The body's last line, for the job's repeat step; None where the body ends with no such line.
    verdict_line: str | None
    # By place, the earlier comment that can answer for a finding there (Earlier.answering).
    newest: Mapping[FindingLine, Prior]
    # The model the job asked for, as the job spells it; None when that is not known.
    model: str | None = None
    # The line under the heading on whether the check passes; None where the review is not posted,
    # or an earlier review of the scan has it.
    check_line: str | None = None
    # Whether a later job of the run may draft fixes for this review's findings.
    fixes_later: bool = False
    # Whether this review adds fixes to an earlier review of the same scan, which describes the
    # findings.
    fixes_only: bool = False


def spans_of(diff: str) -> Spans:
    """The Spans of a unified diff, leaving out a file whose name is not UTF-8."""
    spans: Spans = {}
    for section in unidiff.parse(diff):
        if section.new_path and not strictjson.has_lone_surrogate(section.new_path):
            spans.setdefault(section.new_path, []).extend(section.new_side_spans())
    return spans


class Attached(enum.Enum):
    """Why a fix is attached as a patch rather than offered as a suggestion; the value is the
    sentence the review gives as the reason."""

    OUTSIDE_DIFF = (
        "GitHub can offer a one-click change only for lines that this pull request's diff shows, "
        "and this fix changes more."
    )
    UNCARRIABLE = "A one-click change cannot carry it."
    INVISIBLE = (
        "It is not offered as a one-click change: it adds an invisible character to the code."
    )
    STALE_PATCH = (
        "It cannot be offered as a one-click change: it was made for another commit, or it may not "
        "apply cleanly to this one."
    )
    TOO_LONG = "It is too long for a one-click change in a review comment."
    REFUSED = (
        "GitHub did not accept this review's inline comments, so it cannot be offered as a "
        "one-click change."
    )

    @classmethod
    def of(cls, patch: Patch, commit: str) -> Attached | None:
        """Why Patch.offerable refuses the patch at `commit`; None when it accepts the patch, and
        when no patch was written or read back."""
        if patch.diff is None or patch.offerable(commit) is not None:
            return None
        return cls.STALE_PATCH if patch.stale_for(commit) else cls.UNCARRIABLE


class Placed(NamedTuple):
    """Where one finding went: inline comments, a body section, or neither where an earlier comment
    still answers for it; how its fix is labelled; and whether the review offers that fix, as a
    suggestion or an attached patch."""

    comments: list[Comment]
    body_section: str | None
    fix_label: str
    placement: str
    offers_fix: bool


class Review(NamedTuple):
    """The assembled review: its body up to the full report, its body as fitted to GitHub's limit,
    its inline comments, one placement line per finding, its body from the full report to the end,
    and whether it offers a fix."""

    before_report: str
    posted: str
    comments: list[Comment]
    placements: list[str]
    from_report: str
    offers_fix: bool


def _fits(spans: Spans, path: str, start: int, end: int) -> bool:
    """Whether lines start..end of `path` all sit inside one hunk of the pull request's diff."""
    return any(low <= start and end <= high for low, high in spans.get(path, ()))


class Edit(NamedTuple):
    """One line replacement that a patch makes, and the repository path it makes it in."""

    path: str
    lines: unidiff.Replacement


def to_read(earlier: Earlier, spans: Spans) -> dict[str, list[FindingLine]]:
    """By believed id, the places that a re-check has to read. First those of its believed comments
    that are live or have an anchor, the newest first, or else the line in its fullest comment's
    marker. Then those of such doubted comments that name a grade. Then the lines with the id's
    code in the diff, `spans`. Last those outside it, unless each comment's line is in the diff and
    a believed comment makes its place sure."""
    believed = [one for one in reversed(earlier.believed) if one.live or one.anchor]
    doubted = [one for one in reversed(earlier.doubted) if one.graded and (one.live or one.anchor)]
    found: dict[str, list[FindingLine]] = {}
    for key, fullest in fullest_by_key(earlier.believed).items():
        lines = [one.place.line for one in believed if one.key == key] or [fullest.line]
        lines += [one.place.line for one in doubted if one.key == key]
        inside = all(_fits(spans, fullest.path, line, line) for line in lines)
        sure = any(earlier.is_sure(one) for one in earlier.believed if one.key == key)
        held = earlier.holding.get(key, ())
        lines += [line for line in held if _fits(spans, fullest.path, line, line)]
        if not (inside and sure):
            lines += held
        found[key] = [FindingLine(key, line) for line in dict.fromkeys(lines)]
    return found


def suggestions(diff: str, spans: Spans) -> list[Edit] | Attached:
    """git's own diff of the patch applied to this head as the edits a suggestion would make,
    when every hunk of it is a line replacement that fits the pull request's diff, a suggestion
    can carry its text, and it adds no invisible character; otherwise the reason it is attached
    instead."""
    if not gfm.carriable(diff):
        return Attached.UNCARRIABLE
    if gfm.adds_invisible(diff):
        return Attached.INVISIBLE
    edits: list[Edit] = []
    for section in unidiff.parse(diff):
        found = section.replacements()
        if found is None or section.new_path is None:
            return Attached.OUTSIDE_DIFF
        edits.extend(Edit(section.new_path, lines) for lines in found)
    if edits and all(_fits(spans, edit.path, edit.lines.start, edit.lines.end) for edit in edits):
        return edits
    return Attached.OUTSIDE_DIFF


_UNTESTED = " No test in the project ran the code that this fix changes."


def _analysis_line(patch: Patch) -> str:
    """The one line under a suggestion: what its panel believes of the fix, that no test in the
    project ran the code that it changes, when the record says so, and a request to review it."""
    untested = _UNTESTED if patch.untested else ""
    return (
        "_A panel of agents analyzed this suggestion and believes it introduces no new "
        "vulnerability and does not meaningfully change how the application behaves."
        f"{untested} Please review it carefully: {AI_CAUTION_LINK}._"
    )


def _labelled(label: str, text: str) -> str:
    """`text` as a paragraph that opens with its bold label; empty for an empty text."""
    return f"**{label}.** {text}" if text else ""


def _folded(paragraphs: Sequence[str], title: str) -> str:
    """The paragraphs that are not empty as one collapsed section; empty when all are."""
    body = "\n\n".join(filter(None, paragraphs))
    return gfm.details(body, title) if body else ""


def _set_aside(patch: Patch) -> list[str]:
    """The paragraphs on the problems that the fix's agents judged outside the finding: a lead, then
    the list. An empty list where they found none."""
    if not patch.set_aside:
        return []
    return [_ALSO_FOUND, "\n".join(f"- {problem}" for problem in patch.set_aside)]


def analysis(patch: Patch) -> str:
    """The collapsed section on how a written fix was analyzed: each claim with its evidence, the
    test commands that ran, and what the fix leaves open."""
    claims = (
        f"- **{claim.label.capitalize()}.** "
        + ": ".join(filter(None, ("" if said.state == CONFIDENT else said.state, said.evidence)))
        for claim, said in patch.claims.items()
    )
    paragraphs = [
        "\n".join(claims),
        f"Tests run: {patch.tests_run or 'none recorded'}",
        *_set_aside(patch),
    ]
    return _folded(paragraphs, ANALYSIS_TITLE)


class Fix(NamedTuple):
    """How a finding's fix is presented."""

    said: str
    label: str
    attached: str = ""
    record: str = ""
    offers_fix: bool = False


def describe_fix(
    patch: Patch | None,
    attached_because: Attached,
    no_fix: str,
    *,
    withheld: bool,
    fixes: bool,
) -> Fix:
    """The Fix of a finding whose fix is not offered inline: `attached_because` is the reason a
    written fix is attached instead; `no_fix` is the explanation's sentence on a declined fix, if
    it has one. With `fixes` False it says nothing of a fix. With `withheld` it gives only the fixed
    notice on fixes."""
    if not fixes:
        return Fix("", "")
    if withheld:
        return Fix(Withheld.FIX, "withheld")
    if patch is None:
        return Fix("This review offers no fix for this finding.", _NONE_OFFERED)
    if patch.file is not None and patch.diff is None:
        unreadable = "A fix was analyzed, but its patch file could not be read back as a patch."
        return Fix(unreadable, "could not be read")
    if patch.diff is not None:
        said = f"A suggested fix is attached below. {attached_because.value}"
        diff = patch.diff
        said += _UNTESTED if patch.untested else ""
        whole = patch.exact and len(diff) <= ATTACHED_DIFF_LIMIT
        if whole and attached_because is not Attached.STALE_PATCH:
            said += (
                " To apply it, save it to a file and run `git apply --3way <file>` from the top "
                "folder of the repository."
            )
        if len(diff) > ATTACHED_DIFF_LIMIT:
            diff = (
                diff[:ATTACHED_DIFF_LIMIT] + "\n[truncated: the whole fix is too long to show here]"
            )
        if not patch.exact:
            diff = (
                diff.rstrip("\n")
                + "\n[some bytes of this copy differ from the fix, so it may not apply as shown]"
            )
        block = gfm.details(gfm.fenced(diff, "diff"), _ATTACHED_TITLE)
        return Fix(said, "attached", block, analysis(patch), offers_fix=True)
    unable = "I was unable to confidently propose a fix:"
    also = _folded(_set_aside(patch), ALSO_FOUND_TITLE)
    if no_fix and patch.decline_reason:
        recorded = _folded([patch.decline_reason], DECLINED_TITLE)
        sections = "\n\n".join(filter(None, (recorded, also)))
        return Fix(f"{unable} {no_fix}", _NONE_OFFERED, record=sections)
    reason = patch.refusal or patch.decline_reason or "no reason was recorded."
    return Fix(f"{unable} {reason}", _NONE_OFFERED, record=also)


def also_reached(item: Item, shown: int = _ALSO_SHOWN) -> str:
    """The finding's other places: the first `shown` by name, the rest as a number; "" for none."""
    more = len(item.also) - shown
    named = [place.location for place in item.also[:shown]]
    rest = [f"and {more} more place{'' if more == 1 else 's'}"] if more > 0 else []
    return ", ".join([*named, *rest])


def places_of(item: Item) -> str:
    """The finding's location, then its other places: _ALSO_IN_BRIEF by name, then how many more."""
    also = also_reached(item, _ALSO_IN_BRIEF)
    return f"{item.location} (also {also})" if also else item.location


def finding_markdown(
    item: Item, text: Words, about_fix: str, record: str, *, where_in_head: bool, link: str = ""
) -> str:
    """One finding for the developer, in the words of `text`: its write-up, then `about_fix`, then,
    collapsed, how the attack works and `record` on the fix. With `where_in_head` the facts name the
    finding's place, which leads to `link` if there is one."""
    where = f"[{item.location}]({link})" if link else item.location
    where += f" in {gfm.code_span(item.symbol)}" if item.symbol else ""
    category = item.category if item.category != text.headline else ""
    entry = f"[CWE-{item.cwe}]({cwe.page(item.cwe)})"
    facts = [f"{item.severity.name.capitalize()} severity", category, entry]
    attack = [
        "\n".join(["**What the attack needs.**", *(f"- {need}" for need in item.preconditions)])
        if item.preconditions
        else "",
        "\n".join(f"{number}. {step}" for number, step in enumerate(text.steps, start=1)),
        _labelled("Link to the change", text.via),
        _labelled("Scenario", text.scenario),
    ]
    parts = [
        f"**{DOTS[item.severity]} {text.headline}**",
        " · ".join(filter(None, [*facts, f"at {where}" if where_in_head else ""])),
        _labelled("Also reached at", also_reached(item)),
        text.notice,
        _labelled("What it is", text.what),
        _labelled("Why it matters", text.why),
        text.diagram.drawn() if text.diagram else "",
        _labelled(
            "How to fix it (not verified)" if text.fix_unverified else "How to fix it", text.fix
        ),
        about_fix,
        _folded(attack, ATTACK_TITLE),
        record,
    ]
    return "\n\n".join(filter(None, parts))


def _trailer_of(item: Item, tag: Tag) -> str:
    """The marker a finding's lead comment ends with, empty for a finding with no key."""
    if not item.key:
        return ""
    graded = item.shared_grade or item.graded
    return Marker(item.key, item.path, item.line, tag, graded, bool(item.shared_grade)).text()


def _offer_inline(
    item: Item, text: Words, patch: Patch, edits: list[Edit], pointer: str
) -> Placed | None:
    """The finding, in the words of `text`, placed as inline comments carrying its fix as suggestion
    blocks, one per hunk. `pointer` follows the first block. None when a comment would pass
    BODY_LIMIT."""
    analyzed = _analysis_line(patch)
    edits = sorted(edits, key=lambda e: (e.path != item.name, not e.lines.covers(item.line)))
    comments: list[Comment] = []
    for index, (path, lines) in enumerate(edits, start=1):
        block = gfm.fenced(lines.text, "suggestion") + "\n" + analyzed
        if len(edits) > 1:
            block = (
                f"**Suggested fix, part {index} of {len(edits)}.** Commit all parts in one batch: "
                f"they are one fix.\n\n{block}"
            )
        if index == 1:
            on_sink = path == item.name and lines.covers(item.line)
            about_fix = "\n\n".join(filter(None, (block, pointer)))
            body = finding_markdown(
                item, text, about_fix, analysis(patch), where_in_head=not on_sink
            )
            body += _trailer_of(item, Tag.FIX)
        else:
            body = f"**{text.headline}**\n\n{block}" + part_line(item.key)
        if len(body) > BODY_LIMIT:
            return None
        comments.append(Comment(path, lines.start, lines.end, body))
    first = edits[0]
    at = f"{first.path}:{first.lines.start}"
    placement = f"{item.id}: inline at {at} with a suggested fix"
    parts = len(edits)
    label = "one-click, on the line" if parts == 1 else f"in {parts} parts, on the lines"
    return Placed(comments, None, label, placement, offers_fix=True)


def _answered(item: Item, tag: Tag, inputs: Inputs) -> Prior | None:
    """The comment that `inputs.newest` holds for the finding's place, where it carried at least
    what `tag` names and names the grade that this run gives the finding (marker.still_answers).
    None where another finding of the change has the same key."""
    if not item.key or item.shared_grade:
        return None
    newest = inputs.newest.get(FindingLine(item.key, item.line))
    carried, named = (newest.tag, newest.graded) if newest else (None, None)
    return newest if still_answers(carried, named, tag, item.graded) else None


def all_fixes_offered(report: Report, inputs: Inputs) -> bool:
    """Whether _answered() gives a comment that offers the fix, for every finding of the change.
    True of a report with no such finding."""
    return all(_answered(item, Tag.FIX, inputs) for item in report.findings)


def lowers_a_grade(report: Report, priors: Iterable[Prior]) -> bool:
    """Whether the newest live graded comment at a place among `priors` names a higher severity or
    confidence than the highest that the report gives under its key."""
    return any(
        named.severity > max(item.severity for item in held)
        or named.confidence > max(item.confidence for item in held)
        for prior in newest_by_place(priors).values()
        if (named := prior.graded)
        and (held := [one for one in report.findings if one.key == prior.key])
    )


def describes_fixes(report: Report, inputs: Inputs) -> bool:
    """Whether the review's opening, table and comments describe fixes: the job drafts fixes, and
    the report withholds its write-ups, has a patch record, or needs none (all_fixes_offered)."""
    recorded = report.withheld or bool(report.patches)
    return report.fixes and (recorded or all_fixes_offered(report, inputs))


def place(report: Report, item: Item, inputs: Inputs, *, to_body: bool) -> Placed:
    """Where one finding and its fix go. A fix that is offered as a suggestion carries the write-up
    on the fix's lines. Any other write-up goes on the first of the finding's places that the diff
    shows. Where the diff shows none, or the write-up is too long for one comment, it goes into the
    review's body, as every write-up does with `to_body`. A finding that an earlier comment still
    answers for, by its Tag and its grade, is not commented again. In a review that adds fixes, a
    finding with no fix gets no comment, and the body gives the reason where one was recorded."""
    patch = report.patches.get(item.id)
    attached = Attached.of(patch, report.commit) if patch else None
    diff = inputs.applied.get(item.id)
    offered = suggestions(diff, inputs.spans) if diff is not None else None
    edits = offered if isinstance(offered, list) else None
    why = offered if isinstance(offered, Attached) else attached or Attached.STALE_PATCH
    pointer = LISTED_POINTER if item.joined and report.shows_report else ""
    text = item.words(patch)
    inline = None
    if edits is not None and patch is not None:
        inline = _offer_inline(item, text, patch, edits, pointer)
        why = Attached.TOO_LONG if inline is None else Attached.REFUSED
    fix = describe_fix(
        patch, why, text.no_fix, withheld=report.withheld, fixes=describes_fixes(report, inputs)
    )
    kept = item.recommendation if item.explanation and not fix.offers_fix else ""
    recommendation = _folded([kept], RECOMMENDATION_TITLE)
    about_fix = "\n\n".join(filter(None, (fix.said, fix.attached, recommendation, pointer)))
    wants_fix_comment = fix.offers_fix or inputs.fixes_only
    tag = Tag.WITHHELD if report.withheld else Tag.FIX if wants_fix_comment else Tag.WRITE_UP
    if prior := _answered(item, tag, inputs):
        shown = f"see the [earlier comment]({prior.url}), which still applies"
        spoken = f"{item.id}: already in an earlier comment that still applies ({prior.url})"
        return Placed([], None, shown, spoken, offers_fix=False)
    if inputs.fixes_only and not fix.offers_fix:
        head = f"**{DOTS[item.severity]} {text.headline}**"
        section = "\n\n".join(filter(None, (head, item.location, fix.said, fix.record)))
        placement = f"{item.id}: no fix, in the review body"
        return Placed([], section, fix.label, placement, offers_fix=False)
    if inline and not to_body:
        return inline
    attached_too = " with the suggested fix attached" if fix.offers_fix else ""
    at = f"{item.path}:{item.line}"
    odd = strictjson.has_lone_surrogate(item.name)
    where = f"{at} is in a file whose name is not UTF-8" if odd else f"{at} is outside the diff"
    file = f"{inputs.home}/blob/{report.commit}/{encoded(item.name)}"
    link = f"{file}#L{item.line}" if inputs.home else ""
    own = item.place
    in_diff = (
        one for one in (own, *item.also) if _fits(inputs.spans, one.name, one.line, one.line)
    )
    if not to_body and (spot := next(in_diff, None)):
        away = spot.identity != own.identity
        body = finding_markdown(item, text, about_fix, fix.record, where_in_head=away, link=link)
        body += _trailer_of(item, tag)
        if len(body) <= BODY_LIMIT:
            comment = Comment(spot.path, spot.line, spot.line, body)
            placement = f"{item.id}: inline at {spot.path}:{spot.line}{attached_too}"
            return Placed([comment], None, fix.label, placement, offers_fix=fix.offers_fix)
        where = "too long for one comment"
    in_body = finding_markdown(item, text, about_fix, fix.record, where_in_head=True, link=link)
    placement = f"{item.id}: in the review body ({where}){attached_too}"
    return Placed([], in_body, fix.label, placement, offers_fix=fix.offers_fix)


def _range_lines(report: Report, inputs: Inputs) -> list[str]:
    """The line naming the range under review, linked to GitHub's comparison of it. After it, the
    sentence of a run whose event changed the base branch. Nothing outside a pull request."""
    if not inputs.home:
        return []
    base, head = report.merge_base, report.commit
    span = gfm.code_span(f"{base[:_GITHUB_SHORT_ID_CHARS]}...{head[:_GITHUB_SHORT_ID_CHARS]}")
    line = f"Reviewed [{span}]({inputs.home}/compare/{base}...{head})."
    if change := inputs.base_change:
        was, now = (gfm.code_span(name[:REF_LIMIT]) for name in (change.was, change.now))
        line += f" The base branch changed from {was} to {now}; this review covers the new range."
    return [line, ""]


def scanned(stamp: Stamp, model: str | None) -> str:
    """The footer's sentence on how many changed files the scan was handed, at what scan effort and
    with which `model` setting; empty where none of these is known and the stamp does not record
    Change Scan Effort high. Where it does, the sentence names the input `change_scan_effort: high`
    instead of the scan effort. It gives no count of files for a sparse checkout."""
    files = None if stamp.sparse else stamp.diff_files
    at = f" at {stamp.effort.value} scan effort" if stamp.effort else ""
    if stamp.change_scan_effort is ChangeScanEffort.HIGH:
        at = f" with `change_scan_effort: {ChangeScanEffort.HIGH.value}`"
    if files is None and not at and not model:
        return ""
    read = (
        "Scanned" if files is None else f"{files} changed file{'' if files == 1 else 's'} scanned"
    )
    using = f" using {gfm.code_span(model)}" if model else ""
    return f"{read}{at}{using}."


# Per policy: the findings that fail the run, in words that follow "finding of"; None if none do.
_BAR: Final = {
    FailOn.NEVER: None,
    FailOn.ANY: "any severity",
    FailOn.MEDIUM: "medium severity or above",
    FailOn.HIGH: "high or critical severity",
    FailOn.CONFIDENT_HIGH: "high or critical severity and high confidence",
}


_AGAIN: Final = "Run the job again, or push a new commit."
_LOOK_FIRST: Final = (
    'See "Coverage" in the full report for what the scan could not check. If it names a file that '
    "the scan could not open, a new run can fail the same way: decide whether the scan should read "
    "that file. If it names a researcher that returned without the diff, a new run can fail the "
    "same way too: see whether a permission rule refuses the scan's git commands. If it names "
    f"neither, {_AGAIN[:1].lower()}{_AGAIN[1:]}"
)
_CONFIRMED: Final = " confirmed"


def check_line(outcome: Verdict, report: Report, policy: FailOn, previous: PreviousFindings) -> str:
    """The line under the review's heading: whether the check passes and why, and what to do about a
    check that fails, except where the report lost the change's findings: then opening() says it.
    `outcome` is the verdict under `policy` over the findings of the change and what counts of
    `previous`."""
    words = _BAR[policy]
    if words is None:
        return f"**This check passes:** this job lets no finding fail it (`{policy.value}`)."
    bar = f"{words} (`{policy.value}`)"
    if outcome.passed:
        sure, where = (_CONFIRMED, IN_THIS_CHANGE) if report.older_listed else ("", "")
        return f"**This check passes:** no{sure} finding of {bar}{where}."
    if not outcome.by_findings:
        fails = f"**This check fails:** {outcome.reason}."
        if report.lost_the_changes_findings:
            return fails
        return f"{fails} {_LOOK_FIRST if report.shows_report else _AGAIN}"
    spots = [places_of(item) for item in report.findings if policy.fails(item.graded)]
    spots += [
        f"{gfm.code_span(gfm.plain_line(prior.path))} ([{label}]({prior.url}))"
        for label, earlier in (
            ("reported earlier", previous.standing),
            ("a comment with no receipt", previous.doubted),
        )
        for prior, graded in earlier
        if policy.fails(graded)
    ]
    places = ", ".join(spots[:_FAILING_NAMED])
    more = len(spots) - _FAILING_NAMED
    count = f"{len(spots)} finding{'' if len(spots) == 1 else 's'}"
    if more > 0:
        rest = f"and {more} more finding{'' if more == 1 else 's'}"
        return f"**This check fails:** {count} of {bar}: {places}, {rest}. Fix each one."
    return f"**This check fails:** {count} of {bar}: {places}. Fix each named finding."


def opening(report: Report, *, fixes_described: bool, fixes_later: bool = False) -> str:
    """The review's paragraph on what the scan found. `fixes_described` is describes_fixes().
    `fixes_later` is that of Inputs."""
    stamp = report.stamp
    count, aside = len(report.findings), stamp.pre_existing
    if report.lost_the_changes_findings:
        text = (
            "The scan reported one or more findings that it could not carry into the report, so "
            f"this review does not list them. This is not a clean result. {_AGAIN}"
        )
    elif count == 0:
        sure = _CONFIRMED if report.older_listed else ""
        where = IN_THIS_CHANGE if aside or report.older else ""
        text = f"The scan reported no{sure} security vulnerabilities{where}. {NO_ASSURANCE}"
    else:
        counts = Counter(item.severity for item in report.findings)
        tally = ", ".join(
            f"{counts[level]} {level.name.lower()}" for level in Severity if counts[level]
        )
        each, listed = ("It", "the finding") if count == 1 else ("Each", "each one")
        if report.withheld:
            left_out = "write-up or any fix" if report.fixes else "write-up"
            described = (
                "The scan reports a hard-coded credential, or could not carry every finding into "
                f"the report, so {listed} is listed where it occurs without its {left_out}."
            )
        elif fixes_described:
            described = (
                f"{each} is described on its line or below, with a suggested fix if I could "
                "propose one with confidence. Nothing has been applied."
            )
        elif report.fixes:
            described = (
                f"{each} is described on its line or below. This review includes no suggested "
                "fixes."
            )
        else:
            then = (
                "Suggested fixes may follow in a second review."
                if fixes_later
                else "This job does not draft fixes."
            )
            described = f"{each} is described on its line or below, with how to fix it. {then}"
        found = "vulnerability was" if count == 1 else "vulnerabilities were"
        text = f"{count} security {found} found ({tally}). {described}"
    if older := report.older_listed:
        text += (
            " This review also lists findings that do not count in this check: "
            f'{older} under "{_OLDER_TITLE}".'
        )
    if (rest := aside - len(stamp.set_aside)) > 0:
        possible, them = ("vulnerability", "it") if rest == 1 else ("vulnerabilities", "them")
        text += (
            f" The scan also judged {rest} possible {possible} real but older than this change, "
            f"and set {them} aside; a scan of the whole branch can report {them}."
        )
    if stamp.lost:
        missing = reading_missing(stamp.lost)
        text += (
            f" {missing[:1].upper()}{missing[1:]}, so part of the scan is missing from this review."
        )
    if stamp.sparse:
        text += f" {SPARSE}"
    if not stamp.verified:
        why = f": {shown}" if (shown := stamp.reason_shown(withheld=report.withheld)) else ""
        text += (
            " The scan could not fully verify its own results (status "
            f"{gfm.code_span(stamp.status.value)}{why}), so treat this review as provisional."
        )
    return text


def findings_table(rows: Sequence[tuple[Item, str]], *, fix_column: bool) -> list[str]:
    """Each finding, with its label, as the lines of a Markdown table and a closing blank line; no
    lines for none. The label fills the second column or, with no such column, follows the
    places."""
    if not rows:
        return []
    columns = ["Finding", *(["Suggested fix"] if fix_column else [])]
    lines = [f"| {' | '.join(columns)} |", "|" + " --- |" * len(columns)]
    for item, label in rows:
        grade = f"{DOTS[item.severity]} {item.severity.name.capitalize()}"
        spots = places_of(item)
        where = spots if fix_column else ", ".join(filter(None, [spots, label]))
        finding = f"{grade} · {where}<br>{item.words().headline}"
        cells = [finding, label] if fix_column else [finding]
        escaped = (cell.replace("|", "\\|") for cell in cells)
        lines.append(f"| {' | '.join(escaped)} |")
    return [*lines, ""]


def _older_section(report: Report) -> str:
    """The section on the findings older than the change: its heading, its words, and a table of
    those findings, or a list of those that the scan set aside. Empty where there is neither."""
    if not report.older_listed:
        return ""
    notice = f" {Withheld.NOTICE}" if report.withheld else ""
    does = "describes" if report.older else "names"
    pointer = f" The full report {does} each finding." if report.shows_report else ""
    labels = (
        "" if report.withheld else f"{item.confidence.name} confidence" for item in report.older
    )
    table = findings_table(list(zip(report.older, labels)), fix_column=False)
    aside = [f"- {place.location}: {category}" for place, category in report.stamp.set_aside]
    comments = "" if report.older else f" {_EARLIER_COMMENT}"
    listed = table or [*aside, ""]
    lines = [f"### {_OLDER_TITLE}", "", _OLDER_WORDS + comments + notice + pointer, "", *listed]
    return "".join(f"{line}\n" for line in lines)


def build_review(report: Report, inputs: Inputs, *, to_body: bool) -> Review:
    """Assemble the review; `to_body` marks the retry after GitHub refused the inline comments,
    when no finding is placed inline and the body says why."""
    if inputs.fixes_only:
        stamp = report.stamp._replace(set_aside=[])
        report = report._replace(markdown="", older=[], stamp=stamp)
    fixes_described = describes_fixes(report, inputs)
    placed = [place(report, item, inputs, to_body=to_body) for item in report.findings]
    offers_fix = any(outcome.offers_fix for outcome in placed)
    check = [inputs.check_line, ""] if inputs.check_line else []
    if inputs.fixes_only:
        opened = _ADDS_FIXES if offers_fix else _ADDS_NO_FIX
    else:
        opened = opening(report, fixes_described=fixes_described, fixes_later=inputs.fixes_later)
    lines = [REVIEW_HEADING, "", *check, *_range_lines(report, inputs), opened, ""]
    rows = [(item, outcome.fix_label) for item, outcome in zip(report.findings, placed)]
    lines += findings_table(rows, fix_column=fixes_described)
    if inputs.previous:
        lines += ["### Previously reported findings", "", *inputs.previous, ""]
    sections = [outcome.body_section for outcome in placed if outcome.body_section]
    why = (
        "GitHub did not accept this review's inline comments, so these findings are described "
        "here instead of on their lines."
        if to_body
        else "These sit on lines outside this pull request's diff, where GitHub accepts no "
        "review comment, or are too long for one."
    )
    heading = ["### Findings GitHub cannot show inline", "", why, ""]
    if inputs.fixes_only and not to_body:
        heading = ["### Not shown inline", "", _NOT_INLINE, ""]
    version = f" {inputs.version}" if inputs.version else ""
    said = [
        f"Reviewed by the {sarif.TOOL_NAME}{version}.",
        scanned(report.stamp, inputs.model),
        FIX_CAUTION if offers_fix else "",
    ]
    footer = f"<sub>{' '.join(filter(None, said))}</sub>\n" + (
        f"\n{inputs.verdict_line}\n" if inputs.verdict_line else ""
    )
    markdown = "" if report.lost_the_changes_findings else report.markdown
    full = _folded([markdown], _FULL_REPORT_TITLE) + "\n\n" if markdown.strip() else ""
    body = Body(
        lines=lines,
        heading=heading,
        sections=sections,
        full=full,
        footer=footer,
        older=_older_section(report),
    )
    return Review(
        before_report=gfm.postable(body.before_report()),
        posted=gfm.postable(body.fitted()),
        comments=[c._replace(body=gfm.postable(c.body)) for o in placed for c in o.comments],
        placements=[
            *(outcome.placement for outcome in placed),
            *(f'{item.id}: in the review body, under "{_OLDER_TITLE}"' for item in report.older),
        ],
        from_report=gfm.postable(body.full + body.footer),
        offers_fix=offers_fix,
    )


_CUT: Final = "_Part of this review did not fit here; see the job summary._\n\n"


class Body(NamedTuple):
    """The parts a review body is assembled from."""

    lines: list[str]
    heading: list[str]
    sections: list[str]
    full: str
    footer: str
    older: str = ""
    left_out: str = ""

    def before_report(self) -> str:
        """The review body up to the full report: the heading and the finding sections, set off by
        blank lines, follow the lines only when there are sections. Then comes the note that a part
        is left out, and last the section on older findings."""
        shown = [*self.lines, *self.heading, "\n\n".join(self.sections), ""]
        body = "\n".join(shown if self.sections else self.lines) + "\n"
        return body + self.left_out + self.older

    def text(self) -> str:
        """The whole review body, with nothing left out to fit."""
        return self.before_report() + self.full + self.footer

    def fitted(self) -> str:
        """The review body within BODY_LIMIT. It leaves out the full report first, then each finding
        section that no longer fits. The section on older findings stays whole meanwhile. Last, it
        cuts the end of a body that is still too long, and that cut reaches that section first.
        One note says that a part is missing."""
        body = self.text()
        if len(body) <= BODY_LIMIT:
            return body
        # With no sections, before_report() leaves out the heading; one empty section keeps it.
        bare = self._replace(sections=[""] if self.sections else [], full="", left_out=_CUT)
        room = BODY_LIMIT - len(bare.text()) + len("\n\n")
        kept: list[str] = []
        for section in self.sections:
            size = len(section) + len("\n\n")
            if size <= room:
                kept.append(section)
                room -= size
        body = bare._replace(sections=kept).text()
        if len(body) > BODY_LIMIT:
            body = bare._replace(sections=kept, left_out="").text()
            whole = body[: BODY_LIMIT - len("\n\n") - len(_CUT) - len(self.footer)]
            body = (whole.rpartition("\n")[0] or whole) + "\n\n" + _CUT + self.footer
        return body


def review_markdown(review: Review) -> str:
    """REVIEW.md: the review body up to the full report, then each inline comment under its
    location, then the full report and the footer."""
    parts = ["# Pull request review", "", review.before_report]
    if review.comments:
        parts += ["## Inline comments", ""]
        for c in review.comments:
            span = f"line {c.start}" if c.start == c.end else f"lines {c.start}-{c.end}"
            where = gfm.code_span(gfm.plain_line(c.path))
            parts += [f"### {where} {span}", "", c.body, ""]
    return "\n".join([*parts, review.from_report]).rstrip("\n") + "\n"


class _OneLineComment(TypedDict):
    path: str
    body: str
    line: int
    side: Literal["RIGHT"]


class _SeveralLinesComment(_OneLineComment):
    start_line: int
    start_side: Literal["RIGHT"]


class Request(TypedDict):
    """The request body for POST /repos/{owner}/{repo}/pulls/{number}/reviews."""

    commit_id: str
    event: Literal["COMMENT"]
    body: str
    comments: list[_OneLineComment]


def payload(review: Review, commit: str) -> Request:
    """The request that posts `review` on `commit`."""
    comments: list[_OneLineComment] = []
    for c in review.comments:
        item: _OneLineComment = {"path": c.path, "body": c.body, "line": c.end, "side": "RIGHT"}
        if c.start < c.end:
            item = _SeveralLinesComment(**item, start_line=c.start, start_side="RIGHT")
        comments.append(item)
    return {"commit_id": commit, "event": "COMMENT", "body": review.posted, "comments": comments}


_STANDS: Final = (
    "It counts in each run whose re-check does not find it fixed, until its comments are outdated "
    "and the diff no longer has its code"
)
_CODE_STANDS: Final = "The diff still has its code: {}"
_LINES_NAMED = 5
_ELSEWHERE: Final = (
    "An earlier comment puts it on another line too. That comment counts in each run that neither "
    "reports that line nor finds it fixed in this commit's file, until it is outdated"
)
_SHARED: Final = (
    "An earlier review reported more than one finding under this finding's id. It counts until "
    "the lines under each of its comments change and the diff no longer has its code"
)
_MISREAD: Final = (
    "the re-check found it fixed, but may have read another copy of the file than this commit's"
)
_MISREAD_STANDS: Final = (
    "While the file on disk cannot be shown to match this commit's, it counts until its comments "
    "are outdated and the diff no longer has its code"
)
_DOUBTED_LINKED = 20
_DOUBTED: Final = (
    "**not confirmed fixed** — each stands in a review that has no receipt, so this job may not "
    "have written it. It counts until the lines under it change, or a scan runs after it is "
    "deleted."
)


class PreviousFindings(NamedTuple):
    """The previously-reported section's bullets and stdout lines; the findings that still count in
    the verdict, one comment for each earlier grade that counts; and, for each other grade of a
    finding that counts, one comment with no receipt."""

    bullets: list[str]
    spoken: list[str]
    standing: list[tuple[Prior, Graded]]
    doubted: list[tuple[Prior, Graded]]

    @property
    def graded(self) -> list[Graded]:
        """The grades that count in the verdict."""
        return [graded for _prior, graded in self.standing + self.doubted]


def previous_findings_report(
    earlier: Earlier,
    report: Report,
    rechecks: Mapping[FindingLine, Recheck],
    *,
    spans: Spans,
    misread: Collection[str],
) -> PreviousFindings:
    """One bullet and one stdout line per distinct previously reported finding: still present, fixed
    or not confirmed fixed as the session's recorded re-check says, or not reassessed. A finding is
    fixed where the re-check says so of each line that to_read() gives, and doubts no line. A
    `fixed` does not count for a finding in `misread`.
    A finding neither reported again nor confirmed fixed stands at the grade of its newest live
    comment whose marker names one. It also counts at each other grade that a live doubted comment
    names: those share one bullet and one line. Reported again or not, a finding also stands at
    the grade of each comment that Earlier.at_sure_places() gives, unless the run reports or lists
    the id on that line, or finds that line fixed. With no live graded comment, a finding that is
    not reported stands at the grade of its newest graded comment, while a line of the diff has its
    id's code and is not found fixed. While a live believed comment says that its id is shared, a
    fixed of an id that the run does not report ends no place's count, and never reads as fixed."""
    bullets: list[str] = []
    spoken: list[str] = []
    standing: list[tuple[Prior, Graded]] = []
    priors = earlier.believed
    newest = newest_graded(priors)
    withheld_keys = {prior.key for prior in priors if prior.tag is Tag.WITHHELD}
    shared = shared_keys(priors)
    places = to_read(earlier, spans)
    asked = {at for held in places.values() for at in held}
    in_doubt = sorted((at for at, one in rechecks.items() if not one.fixed), key=asked.__contains__)
    doubts = {at.key: at for at in in_doubt}
    read = {key: held[0] for key, held in places.items() if all(at in rechecks for at in held)}
    reported_keys = report.keys
    no_fixed = {*misread, *(shared - reported_keys)}
    settled = reported_keys | read.keys() - {*doubts, *no_fixed}
    mended = {at for at, one in rechecks.items() if one.fixed and at.key not in no_fixed}
    gone = report.reported | mended
    elsewhere = [one for at, one in earlier.at_sure_places().items() if at not in gone]
    for prior in fullest_by_key(priors).values():
        keeping = [one for one in elsewhere if one.key == prior.key]
        if prior.key not in settled and prior.key in newest:
            keeping.append(newest[prior.key])
        closing, why = _STANDS, ""
        if prior.key in reported_keys:
            status, note = "still present", "reported again in this run's findings"
            closing = _ELSEWHERE
            if prior.key in report.older_keys:
                note = (
                    f'this run lists it under "{_OLDER_TITLE}", so it does not count in this check'
                )
        elif prior.key in misread and prior.key in read and prior.key not in doubts:
            status, note, closing = "not confirmed fixed", _MISREAD, _MISREAD_STANDS
            why = f" ({_MISREAD})"
        elif at := doubts.get(prior.key) or read.get(prior.key):
            status = "fixed" if prior.key in settled else "not confirmed fixed"
            note = rechecks[at].note or "the run recorded no reason"
            if prior.key in withheld_keys or report.withheld:
                note = Withheld.NOTE
            if prior.key in doubts and at in asked:
                note = f"line {at.line}: {note}"
        else:
            status, note = (
                "not reassessed",
                "this run left no usable re-check of each of its places",
            )
        still_on = [
            line
            for line in earlier.holding.get(prior.key, ())
            if FindingLine(prior.key, line) not in gone and _fits(spans, prior.path, line, line)
        ]
        last = [one for one in priors if one.key == prior.key and one.graded][-1:]
        if still_on and last and not keeping and prior.key not in reported_keys:
            keeping = last
            named = at_most(_LINES_NAMED, [f"line {line}" for line in still_on])
            note = f"{note.rstrip('.')}. {_CODE_STANDS.format(named)}"
        if keeping:
            standing += {one.graded: (one, one.graded) for one in keeping if one.graded}.values()
            note = f"{note.rstrip('.')}. {_SHARED if prior.key in shared - settled else closing}"
        linked = keeping[-1] if keeping else prior
        shown = (linked.headline or "an earlier finding").replace("[", "(").replace("]", ")")
        bullets.append(f"- [{shown}]({linked.url}): **{status}** — {note.rstrip('.')}.")
        counts = ", and it counts in this check" if keeping else ""
        spoken.append(f"previously reported {prior.key}: {status}{why}{counts}")
    stands = {(prior.key, graded) for prior, graded in standing}
    counting = [
        (prior, prior.graded)
        for prior in earlier.doubted
        if prior.live
        and prior.graded
        and prior.key not in settled
        and (prior.key, prior.graded) not in stands
    ]
    if counting:
        links = [f"[comment {n}]({prior.url})" for n, (prior, _) in enumerate(counting, 1)]
        bullets.append(f"- {at_most(_DOUBTED_LINKED, links)}: {_DOUBTED}")
        spoken.append(f"comments with no receipt that count in this check: {len(links)}")
    added = {(prior.key, graded): (prior, graded) for prior, graded in counting}
    return PreviousFindings(bullets, spoken, standing, list(added.values()))
