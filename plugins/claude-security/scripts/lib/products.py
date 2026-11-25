"""A report's products read back from its directory: the revision stamp, the findings and their
explanations, the report Markdown, the patch record and the recorded re-checks, each narrowed
once."""

from __future__ import annotations

import re
from collections import Counter
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, NamedTuple, final

from . import (
    absolute,
    console,
    cwe,
    explanation,
    gfm,
    link,
    plain,
    plugin,
    sarif,
    secret,
    strictjson,
    unidiff,
)
from .effort import ChangeScanEffort, Effort
from .explanation import Diagram, Explanation, Flaw
from .finding import (
    FINDING_ID,
    FINDING_ID_RE,
    OVERRULED_NOTE,
    Confidence,
    Severity,
    highest,
    listed_in,
    repository_file,
    scan_prefix_shaped,
    unpercent,
)
from .markdown import fenceable
from .marker import FindingLine
from .strictjson import clean, is_int, is_list, is_map, is_str, surrogates_are_bytes
from .verdict import Graded, Status

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from .strictjson import JsonMap

_OLDER: Final = "older_than_the_change"
PATCH_NAME_RE = re.compile(plugin.PATCH_UNIT_ID_PATTERN + r"\.patch")
CWE_ID_RE = re.compile(r"CWE-[0-9]{1,9}")
DIFF_START_RE = re.compile(rf"(?m)^(?:(?:# )?{re.escape(unidiff.DIFF_HEADER)}|--- .*\n\+\+\+ )")
UNRECORDED = (
    "the patch record does not carry the mark of the script that verifies and writes "
    "patches, so this review does not vouch for it."
)
_ID_RE = re.compile(
    r"`[^`]*`|(?i:\bthe )?(?i:\bfindings? )?"
    rf"(?<![\w%./=-])({plugin.PATCH_UNIT_ID_PATTERN})(?![\w%/=-]|\.\w)"
)


class ProductError(Exception):
    """A product is not as the renderer or the patch writer leaves it, or is not one that a review
    is built from; the message says what is wrong."""


@final
class Withheld:
    """The fixed text the review shows when the report holds a hard-coded credential finding
    or its render refused a finding: each finding in the report is then posted as its places,
    severity and CWE alone, and the report's Markdown, each finding's write-up and every fix are
    not posted. A comment's hidden marker still names the finding's id, place and grade, for a
    later run."""

    REPORT = (
        "The report discusses a hard-coded credential, or the scan could not carry one of its "
        "findings into the report, so the report's text is withheld.\n"
    )
    NOTICE = (
        "This scan reports a hard-coded credential, or could not carry one of its findings "
        "into the report, so the review gives each finding's places, severity and CWE only. "
        "Move any reported credential out of the source and rotate it."
    )
    FIX = "Any suggested fix is withheld too."
    NOTE = "the re-check's note is withheld"


class Change(NamedTuple):
    """The pair a changes scan's stamp records: the commit scanned and its declared merge base."""

    commit: str
    merge_base: str


class Stamp(NamedTuple):
    """The report's one revision stamp."""

    # The commit the stamp says was scanned; None unless it records a commit id.
    commit: str | None
    # The merge base as stamped, not checked to be a commit id; None unless it records a string.
    merge_base: str | None
    mode: str | None
    prefix: str
    scope: list[str]
    effort: Effort | None
    change_scan_effort: ChangeScanEffort
    status: Status
    reason: str
    # The render refused a finding: it is absent from the JSONL and the SARIF results.
    refused: bool
    diff_files: int | None
    # Candidates the panel judged real but predating the change: set aside, not reported.
    pre_existing: int
    set_aside: list[tuple[Place, str]]
    # Research agents whose reading is missing while another's is there; 0 otherwise.
    lost: int
    empty: bool
    scoped: bool
    sparse: bool
    total: int | None
    tally: Mapping[Graded, int] | None
    older: int

    @property
    def verified(self) -> bool:
        """Whether the scan verified its own results."""
        return self.status is Status.VERIFIED

    def reason_shown(self, *, withheld: bool) -> str:
        """The stamp's reason as Markdown, for a report whose checks did not all pass; empty where
        they passed, where the stamp gives none, and where the review withholds the report's
        prose."""
        return "" if self.verified or withheld else gfm.inert(self.reason)

    @classmethod
    def read(cls, report_dir: Path) -> Stamp:
        """The report's single revision stamp; refused when there is not exactly one, it is not a
        JSON object, its mode is a string that no scan or triage writes, its scan_prefix is not a
        path prefix, or it has counts of research agents that are not two whole numbers with no
        more returned than sent. OSError where plain.read_text refuses the stamp."""
        stamps = [path for path in report_dir.iterdir() if plugin.is_revision_stamp(path)]
        if len(stamps) != 1:
            msg = (
                f"{report_dir} must hold exactly one {plugin.revision_stamp_name('*')} revision "
                f"stamp and holds {len(stamps)}; render the report before running this script"
            )
            raise ProductError(msg)
        try:
            stamp = strictjson.loads(plain.read_text(stamps[0]))
        except ValueError as error:
            msg = f"{stamps[0].name} is not valid JSON: {error}"
            raise ProductError(msg) from error
        if not is_map(stamp):
            msg = f"{stamps[0].name} is not a JSON object"
            raise ProductError(msg)
        mode = stamp.get("mode")
        taken = {*plugin.MODES, *plugin.STAMP_MODES.values(), plugin.TRIAGE_STAMP_MODE}
        if is_str(mode) and mode not in taken:
            msg = (
                f"{stamps[0].name} has the mode {mode!r}, which no scan or triage of this plugin "
                "version writes: name a scan's report or a triage's"
            )
            raise ProductError(msg)

        def part(key: str) -> JsonMap:
            value = stamp.get(key)
            return value if is_map(value) else {}

        prefix = stamp.get("scan_prefix")
        if not is_str(prefix) or not scan_prefix_shaped(prefix) or not surrogates_are_bytes(prefix):
            msg = f"{stamps[0].name} scan_prefix {prefix!r} is not a path prefix"
            raise ProductError(msg)
        revision, check, shape = part("revision"), part("verification"), part("run_shape")
        commit, merge_base = revision.get("commit"), revision.get("merge_base")
        try:
            status = Status(clean(check.get("status")))
        except ValueError:
            status = Status.UNKNOWN
        sent, back = check.get("researchers_dispatched"), check.get("researchers_returned")
        if (sent, back) != (None, None) and not (
            is_int(sent) and is_int(back) and 0 <= back <= sent
        ):
            msg = (
                f"{stamps[0].name} researchers_dispatched {sent!r} and researchers_returned "
                f"{back!r} are not two whole numbers with no more returned than sent; "
                "run the scan again"
            )
            raise ProductError(msg)
        try:
            effort = Effort(clean(stamp.get("effort")))
        except ValueError:
            effort = None
        change_scan_effort = (
            ChangeScanEffort.HIGH
            if stamp.get("change_scan_effort") == ChangeScanEffort.HIGH.value
            else ChangeScanEffort.LOW
        )
        diff_files, pre_existing = shape.get("diff_files"), shape.get("pre_existing")
        scope = stamp.get("scope")
        counted = part("findings")
        total = counted.get("total")
        older = counted.get(_OLDER)
        grid = counted.get("by_confidence")
        tally = {
            Graded(severity, confidence): count
            for severity in Severity
            if is_map(grid) and is_map(row := grid.get(severity.name.lower()))
            for confidence in Confidence
            if is_int(count := row.get(confidence.name))
        }
        return cls(
            commit=commit if is_str(commit) and plugin.SHA_RE.match(commit) else None,
            merge_base=merge_base if is_str(merge_base) else None,
            mode=mode if is_str(mode) else None,
            prefix=prefix,
            scope=[entry for entry in scope if is_str(entry)] if is_list(scope) else [],
            effort=effort,
            change_scan_effort=change_scan_effort,
            status=status,
            reason=gfm.plain_line(clean(check.get("reason"))),
            refused=check.get("refused_findings") not in (None, []),
            diff_files=diff_files if is_int(diff_files) else None,
            pre_existing=pre_existing if is_int(pre_existing) else 0,
            set_aside=[
                (place, cwe.catalog.category_name(strictjson.as_int(entry.get("cwe"))))
                for entry in strictjson.maps(shape.get("pre_existing_at"))
                if (place := Place.of(entry, prefix))
            ],
            lost=sent - back if is_int(sent) and is_int(back) and 0 < back < sent else 0,
            empty=shape.get("empty_diff") is True or shape.get("empty_scope") is True,
            scoped=bool(prefix) or stamp.get("scope") not in (None, []),
            sparse=revision.get("sparse") is True,
            total=total if is_int(total) else None,
            tally=tally if len(tally) == len(Severity) * len(Confidence) else None,
            older=older if is_int(older) else 0,
        )

    def change(self) -> Change:
        """The commit and merge base of the changes scan this stamp records; refused when it
        records no pair, or a merge base that is no commit id."""
        if not (self.commit and self.merge_base is not None):
            msg = (
                "the revision stamp records no commit and merge base: a review is built from a "
                "scan of a branch's changes against a base, and this report is not one"
            )
            raise ProductError(msg)
        if not plugin.SHA_RE.match(self.merge_base):
            msg = f"the revision stamp's merge_base {self.merge_base!r} is not a commit id"
            raise ProductError(msg)
        return Change(commit=self.commit, merge_base=self.merge_base)


def records(path: Path, *, required: bool) -> list[JsonMap]:
    """The object records of a JSONL product. An optional one is empty where it is absent and, with
    a warning, where plain.read_text() refuses it. A required one raises that OSError, and
    ProductError where it is absent. Either raises ProductError where it is not UTF-8 JSONL of
    objects with an id."""
    try:
        lines = plain.read_text(path).split("\n")
        rows = [strictjson.loads(line) for line in lines if line.strip()]
    except FileNotFoundError as error:
        if required:
            msg = f"{path.name} is missing from the report directory"
            raise ProductError(msg) from error
        return []
    except OSError as error:
        if required:
            raise
        console.warn(f"could not read {path.name}, so no record is read from it: {error}")
        return []
    except ValueError as error:
        msg = f"{path.name} is not valid JSONL: {error}"
        raise ProductError(msg) from error
    found = [row for row in rows if is_map(row) and is_str(row.get("id"))]
    if len(found) != len(rows):
        msg = f"{path.name} holds a record that is not an object with an id"
        raise ProductError(msg)
    return found


def finding_records(report_dir: Path, stamp: Stamp) -> list[JsonMap]:
    """The report's finding records; refused where they are not as many as the stamp counts."""
    rows = records(report_dir / plugin.JSONL_NAME, required=True)
    if stamp.total != len(rows):
        held = f"{len(rows)} finding record{'' if len(rows) == 1 else 's'}"
        counted = "gives no count of findings" if stamp.total is None else f"counts {stamp.total}"
        msg = (
            f"{plugin.JSONL_NAME} holds {held}, and the revision stamp {counted}, so the report is "
            "not whole. Run the scan, or the job, again."
        )
        raise ProductError(msg)
    return rows


def names_credential(value: object) -> bool:
    """Whether `value` is a CWE id that rolls up to Use of Hard-coded Credentials; one that
    cannot be read refuses the run rather than count as no credential."""
    try:
        return secret.is_credential_id(clean(value))
    except ValueError:
        msg = f"{value!r} is not a CWE id the renderer writes"
        raise ProductError(msg) from None


def is_credential_record(row: JsonMap) -> bool:
    """Whether a JSONL finding record's `cwe_id`, or any of its `other_cwe_ids`, rolls up to
    Use of Hard-coded Credentials. An absent `other_cwe_ids` counts as none. One that is not a list
    refuses the run, and so does any id that cannot be read."""
    others = row.get("other_cwe_ids", [])
    if not is_list(others):
        msg = "its other_cwe_ids is not a list"
        raise ProductError(msg)
    credential = [names_credential(cwe_id) for cwe_id in (row.get("cwe_id"), *others)]
    return any(credential)


def withholds(rows: list[JsonMap], stamp: Stamp) -> bool:
    """Whether the review withholds the report's prose: a JSONL finding record is a hard-coded
    credential finding, or the render refused a finding, which may have been one. A record that the
    credential check cannot read refuses the run."""
    try:
        credential = [is_credential_record(row) for row in rows]
        return stamp.refused or any(credential)
    except ProductError as error:
        msg = (
            f"{plugin.JSONL_NAME} holds a finding record that cannot be read ({error}). Run the "
            "scan, or the job, again."
        )
        raise ProductError(msg) from error


def _grade(row: JsonMap) -> Graded:
    """The record's severity and confidence; refused when either is not a name that the renderer
    writes, or the record's cwe_id does not read as CWE- and digits."""
    severity, confidence = row.get("severity"), row.get("confidence")
    if not (
        is_str(severity)
        and severity in Severity.__members__
        and is_str(confidence)
        and confidence in Confidence.__members__
        and CWE_ID_RE.fullmatch(clean(row.get("cwe_id")))
    ):
        msg = (
            f"{plugin.JSONL_NAME}: finding {row.get('id')!r} has a severity, confidence or "
            "cwe_id the renderer does not write"
        )
        raise ProductError(msg)
    return Graded(Severity[severity], Confidence[confidence])


def _is_older(row: JsonMap) -> bool:
    """Whether the record has the mark `older_than_the_change`; refused where the mark is not set
    to true."""
    if _OLDER in row and row[_OLDER] is not True:
        msg = (
            f"{plugin.JSONL_NAME}: finding {row.get('id')!r} has {_OLDER} in a form that the "
            "renderer never writes. A record has it only as true. Run the scan, or the job, again."
        )
        raise ProductError(msg)
    return _OLDER in row


class Words(NamedTuple):
    """What a comment says of one finding."""

    headline: str
    notice: str
    what: str
    why: str
    fix: str
    fix_unverified: bool
    no_fix: str
    steps: list[str]
    diagram: Diagram | None
    via: str
    scenario: str


def _spelled(prefix: str, file: str) -> tuple[str, str]:
    """A JSONL record's `file` as Item's `path`, then as Item's `name`."""
    name = repository_file(prefix, file=unpercent(file))
    shown_as_written = strictjson.has_lone_surrogate(name)
    return (repository_file(prefix, file=file) if shown_as_written else name), name


def _names_a_file(prefix: str, path: str) -> bool:
    """Whether an Item's or a Place's `path` can be a file's: it lies below the repository top
    level, and is neither the scan's own folder nor a folder above it."""
    return absolute.below_top(path) and not prefix.startswith(f"{path}/")


class Place(NamedTuple):
    """A place of a flaw: a finding's own, one that its record lists in `also_at`, or one that
    the stamp gives for a candidate that the panel set aside."""

    path: str
    name: str
    line: int

    @classmethod
    def of(cls, entry: JsonMap, prefix: str) -> Place | None:
        """A place that a record gives by its `file` and `line`. None where its file or line fails
        its check here, or it names no file below the repository top level."""
        file, line = clean(entry.get("file")), entry.get("line")
        if not (file and surrogates_are_bytes(file) and is_int(line)):
            return None
        path, name = _spelled(prefix, file)
        return cls(path, name, line) if _names_a_file(prefix, path) else None

    @property
    def identity(self) -> tuple[str, int]:
        """What makes two places one: the file's real name and the line."""
        return self.name, self.line

    @property
    def location(self) -> str:
        """The place's path, defused to one line, and its line as one code span."""
        return gfm.code_span(f"{gfm.plain_line(self.path)}:{self.line}")


class Item(NamedTuple):
    """One finding as the review reads it: the JSONL record narrowed once, its prose defused."""

    id: str
    title: str
    path: str
    name: str
    line: int
    severity: Severity
    confidence: Confidence
    cwe: int
    category: str
    # Plain text, not defused: show it in a code span.
    symbol: str
    impact: str
    description: str
    scenario: str
    preconditions: list[str]
    recommendation: str
    via: str
    key: str | None
    explanation: Explanation | None = None
    notice: str = ""
    also: tuple[Place, ...] = ()
    joined: bool = False
    older: bool = False
    shared_grade: Graded | None = None

    def withheld(self) -> Item:
        """This finding keeping its id, places, severity, confidence and CWE, titled by its
        CWE category, with the fixed notice in place of every free-prose field."""
        return self._replace(
            notice=Withheld.NOTICE,
            title=self.category,
            symbol="",
            impact="",
            description="",
            scenario="",
            preconditions=[],
            recommendation="",
            via="",
            explanation=None,
        )

    def explained(self, folder: Path) -> Item:
        """This finding with the explanation that `folder` holds for it. Where none can be used, a
        warning says why; so does one for each part of it that cannot."""
        found = explanation.read(folder, self.id)
        if isinstance(found, Flaw):
            own = "so the review shows the scan's own text for it"
            console.warn(f"{self.id}: no explanation is used, {own}: {found.reason}")
            return self
        for part in found.dropped:
            console.warn(f"{self.id}: the explanation is used without {part}")
        return self._replace(explanation=found)

    def words(self, patch: Patch | None = None) -> Words:
        """What a comment says of this finding, whose fix `patch` records. Without an explanation,
        a written fix's summary stands in for the scan's recommendation where the fix's patch file
        was read back as a patch and the summary is not empty."""
        told = self.explanation
        if told is not None:
            scenario = "" if told.steps else self.scenario
            note = [part for part in self.description.split("\n\n") if OVERRULED_NOTE in part]
            return Words(
                headline=told.headline,
                notice="",
                what="\n\n".join([told.what, *note]),
                why=told.why,
                fix=told.fix,
                fix_unverified=patch is None or patch.file is None,
                no_fix=told.no_fix,
                steps=told.steps,
                diagram=told.diagram,
                via="",
                scenario=scenario,
            )
        summary = patch.summary if patch and patch.diff is not None else ""
        return Words(
            headline=self.title,
            notice=self.notice,
            what=self.description,
            why=self.impact,
            fix=summary or self.recommendation,
            fix_unverified=not summary,
            no_fix="",
            steps=[],
            diagram=None,
            via=self.via,
            scenario=self.scenario if self.scenario != self.description else "",
        )

    @property
    def graded(self) -> Graded:
        """What the verdict reads of this finding."""
        return Graded(self.severity, self.confidence)

    @property
    def location(self) -> str:
        """The finding's path and line as one code span."""
        return self.place.location

    @property
    def place(self) -> Place:
        """The finding's own place."""
        return Place(self.path, self.name, self.line)

    @classmethod
    def of(cls, row: JsonMap, prefix: str) -> Item:
        """One JSONL finding record narrowed to what the review reads; refused when its id, file,
        line, title, severity, confidence, cwe_id or older_than_the_change fails its check here, or
        it names no file below the repository top level."""
        finding_id, own = clean(row.get("id")), Place.of(row, prefix)
        if not (FINDING_ID_RE.match(finding_id) and own and clean(row.get("title"))):
            msg = (
                f"{plugin.JSONL_NAME}: finding {row.get('id')!r} lacks an id, a title, a line or a "
                "file below the repository top level, as the renderer writes them"
            )
            raise ProductError(msg)
        graded = _grade(row)
        number = cwe.id_number(clean(row.get("cwe_id")))
        category = cwe.catalog.category_name(number)
        preconditions = row.get("preconditions")
        key = clean(row.get(FINDING_ID))
        others: dict[tuple[str, int], Place] = {}
        for entry in listed_in(row) or []:
            if place := Place.of(entry, prefix):
                others.setdefault(place.identity, place)
        joined = bool(others)
        others.pop(own.identity, None)
        return cls(
            id=finding_id,
            title=gfm.one_line(row.get("title")),
            path=own.path,
            name=own.name,
            line=own.line,
            severity=graded.severity,
            confidence=graded.confidence,
            cwe=number,
            category=category,
            symbol=gfm.plain_line(clean(row.get("symbol"))),
            impact=gfm.prose(row.get("impact")),
            description=gfm.prose(row.get("description")),
            scenario=gfm.prose(row.get("exploit_scenario")),
            preconditions=[
                text
                for entry in (preconditions if is_list(preconditions) else [])
                if (text := gfm.one_line(entry))
            ],
            recommendation=gfm.prose(row.get("recommendation")),
            via=gfm.prose(row.get("via_change")),
            key=key if sarif.FINGERPRINT_RE.fullmatch(key) else None,
            also=tuple(others.values()),
            joined=joined,
            older=_is_older(row),
        )


def findings_of(rows: list[JsonMap], stamp: Stamp) -> list[Item]:
    """Each finding record as an Item, in the records' order; refused where Item.of refuses one,
    where two of them have one id, where the stamp lacks a count of a severity and confidence, or
    where its count of the mark older_than_the_change, or of a severity and confidence among
    those without it, differs from the records'."""
    items = [Item.of(row, stamp.prefix) for row in rows]
    ids = Counter(item.id for item in items)
    if twice := sorted(one for one, times in ids.items() if times > 1):
        msg = (
            f"{plugin.JSONL_NAME} holds more than one finding with the id {twice[0]}. Run the "
            "scan, or the job, again."
        )
        raise ProductError(msg)
    _hold_to_the_stamp(items, stamp)
    return items


def _hold_to_the_stamp(items: list[Item], stamp: Stamp) -> None:
    """Refuse `items`, a report's findings, as findings_of() says of the stamp's counts."""
    older = sum(item.older for item in items)
    if older != stamp.older:
        msg = (
            f"{plugin.JSONL_NAME} and the revision stamp differ in how many findings have the mark "
            f"{_OLDER}. The file holds {older}. The revision stamp counts {stamp.older}. So the "
            "report is not as it was rendered. Run the scan, or the job, again."
        )
        raise ProductError(msg)
    if stamp.tally is None:
        msg = (
            "the revision stamp does not give a count of findings for every severity and "
            f"confidence, so those in {plugin.JSONL_NAME} cannot be checked. Run the scan, or the "
            "job, again."
        )
        raise ProductError(msg)
    grades = Counter(item.graded for item in items if not item.older)
    if stamp.tally != {one: grades[one] for one in stamp.tally}:
        msg = (
            f"{plugin.JSONL_NAME} does not hold as many findings of each severity and confidence "
            "as the revision stamp counts, so the report is not as it was rendered. Run the scan, "
            "or the job, again."
        )
        raise ProductError(msg)


def _reported_in(rows: list[JsonMap]) -> frozenset[FindingLine]:
    """The key and the line of each finding in `rows`, and of each one that a row lists."""
    return frozenset(
        at
        for row in rows
        for at in map(FindingLine.of, (row, *(listed_in(row) or [])))
        if sarif.FINGERPRINT_RE.fullmatch(at.key)
    )


def _shared_grade(item: Item, items: list[Item]) -> Graded | None:
    """The highest severity and the highest confidence among the `items` with `item`'s key; None
    where `item` alone has it."""
    grades = [one.graded for one in items if item.key and one.key == item.key]
    return Graded(*highest(grades)) if len(grades) > 1 else None


def _names_by_id(rows: list[JsonMap], prefix: str) -> dict[str, str]:
    """What a posted text calls each finding of `rows`, and each that one of them lists, where the
    fix step's words have its id."""
    return {
        clean(one.get("id")): f"finding {place.location}"
        for one in (*(entry for row in rows for entry in listed_in(row) or []), *rows)
        if (place := Place.of(one, prefix))
    }


def _without_ids(value: object, names: Mapping[str, str]) -> str:
    """A record's text field with each finding id outside a code span of single backticks, and any
    "the", "finding" or "findings" just before it, replaced by its name in `names`. An id that
    `names` lacks, or that is a part of a longer word, stays."""
    return _ID_RE.sub(lambda found: names.get(found[1], found[0]), clean(value))


class Assessment(NamedTuple):
    """What the panel said of one claim about a patch: its state and the evidence for it."""

    state: str
    evidence: str

    @classmethod
    def of(cls, said: JsonMap, names: Mapping[str, str]) -> Assessment:
        """One claim of a patches.jsonl record, for the review. No text but a state of
        plugin.CLAIM_STATES stands for one. In its evidence, each finding id becomes the finding's
        name in `names`."""
        state = clean(said.get("state"))
        known = state if state in plugin.CLAIM_STATES else "UNKNOWN"
        return cls(known, gfm.prose(_without_ids(said.get("evidence"), names)))


def _read_patch(file: Path) -> tuple[str, bool] | None:
    """A patch file's diff, from where DIFF_START_RE finds its start, and whether the file is UTF-8,
    the only encoding a comment shows unaltered; None when it cannot be read or holds no diff."""
    try:
        data = plain.read_bytes(file)
    except OSError as error:
        console.warn(f"could not read the patch file back: {error}")
        return None
    try:
        text, utf8 = data.decode("utf-8"), True
    except UnicodeDecodeError:
        text, utf8 = data.decode("utf-8", "replace"), False
    start = DIFF_START_RE.search(text)
    return (text[start.start() :], utf8) if start else None


class Patch(NamedTuple):
    """One unit of the patch record, narrowed once: what the review says about the fix. The
    defaults are a unit with no patch and nothing vouched for."""

    summary: str = ""
    file: Path | None = None
    diff: str | None = None
    # Whether a comment shows the diff byte for byte, and whether a suggestion may carry it.
    exact: bool = False
    suggestable: bool = False
    base: str = ""
    applies: bool = False
    decline_reason: str = ""
    refusal: str = ""
    claims: Mapping[plugin.Claim, Assessment] = MappingProxyType({})
    untested: bool = False
    tests_run: str = ""
    set_aside: tuple[str, ...] = ()

    @classmethod
    def of(cls, row: JsonMap, patches_dir: Path, names: Mapping[str, str]) -> Patch:
        """One patches.jsonl record narrowed to what the review reads, with its diff when
        written. A record without patch_artifacts.py's provenance mark reads as a declined
        unit: nothing it says about a patch or its verification is repeated. In its decline reason,
        evidence and set-aside weaknesses, each finding id becomes the finding's name in `names`,
        and the unit's own id becomes "this finding"."""
        if row.get("provenance") != plugin.PATCHES_PROVENANCE:
            return cls(refusal=UNRECORDED)
        names = {**names, clean(row.get("id")): "this finding"}
        name = row.get("patch")
        file = patches_dir / name if is_str(name) and PATCH_NAME_RE.fullmatch(name) else None
        diff, utf8 = (_read_patch(file) if file is not None else None) or (None, False)
        claims = row.get("claims")
        recorded: JsonMap = claims if is_map(claims) else {}
        paths = row.get("attack_paths")
        return cls(
            summary=gfm.one_line(row.get("summary")),
            file=file,
            diff=diff,
            exact=diff is not None and utf8 and fenceable(diff) == diff,
            suggestable=diff is not None and utf8 and gfm.carriable(diff),
            base=clean(row.get("base")),
            applies=row.get("apply_check") == plugin.APPLY_CLEAN,
            decline_reason=gfm.prose(_without_ids(row.get("decline_reason"), names)),
            claims={
                claim: Assessment.of(said, names)
                for claim in plugin.Claim
                if is_map(said := recorded.get(claim.key))
            },
            untested=row.get("untested") is True,
            tests_run=gfm.prose(row.get("tests_run")),
            set_aside=tuple(
                line
                for path in (paths if is_list(paths) else [])
                if is_map(path)
                and path.get("kind") == plugin.SET_ASIDE
                and (line := gfm.inert(_without_ids(path.get("text"), names))).strip(". ")
            ),
        )

    def offerable(self, commit: str) -> Path | None:
        """The patch file a suggestion may be offered from at `commit`: written, with a diff a
        suggestion can carry, built against this commit and applying cleanly; else None."""
        fresh = self.diff is not None and self.suggestable and not self.stale_for(commit)
        return self.file if fresh else None

    def stale_for(self, commit: str) -> bool:
        """Whether the patch was built against another revision than `commit`, or did not apply
        cleanly when written, whatever git could still make of it now."""
        return self.base != commit or not self.applies


class Recheck(NamedTuple):
    """The session's recorded re-check of one place of a previously reported finding: whether it
    found the flaw fixed there, and its note. Not fixed covers a flaw that it found still there, and
    one that it could not judge."""

    fixed: bool
    note: str


def rechecks(report_dir: Path) -> dict[FindingLine, Recheck]:
    """The re-checks the session recorded beside the report, by finding key and line; empty when the
    file is absent or unreadable, with malformed entries skipped. A `fixed` with no line is
    malformed, and a doubt with no line is held at line 0. Of two entries for one place, one that
    is not fixed stands."""
    try:
        value = strictjson.loads(plain.read_text(report_dir / plugin.PREVIOUS_NAME))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        console.warn(f"could not read the recorded re-checks in {plugin.PREVIOUS_NAME}: {error}")
        return {}
    if not is_list(value):
        console.warn(f"{plugin.PREVIOUS_NAME} is not a JSON array; no re-check is read from it")
        return {}
    found: dict[FindingLine, Recheck] = {}
    for at, entry in enumerate(value):
        fields: JsonMap = entry if is_map(entry) else {}
        place, status = FindingLine.of(fields), clean(fields.get("status"))
        known = status == "not_reassessed" or (status == "fixed" and is_int(fields.get("line")))
        if sarif.FINGERPRINT_RE.fullmatch(place.key) and known:
            if place not in found or found[place].fixed:
                found[place] = Recheck(status == "fixed", gfm.one_line(fields.get("note")))
        else:
            console.warn(
                f"{plugin.PREVIOUS_NAME} entry {at} does not name a finding id, a line and a "
                "status of fixed or not_reassessed; it is skipped"
            )
    return found


def report_markdown(report_dir: Path, *, withheld: bool) -> str:
    """The report's Markdown made safe to fold into a section (empty when it cannot be read),
    or, for a `withheld` report, the notice that stands in for it."""
    if withheld:
        return Withheld.REPORT
    try:
        data = plain.read_bytes(report_dir / plugin.RESULTS_MD_NAME)
    except OSError as error:
        console.warn(f"could not read the full report, so it is left out: {error}")
        return ""
    return gfm.section(data.decode("utf-8", "replace"))


class Report(NamedTuple):
    """What the scan and the patch job left in the report directory; in a job that was handed the
    report, its patches come from that job's session's output."""

    top: str
    stamp: Stamp
    commit: str
    merge_base: str
    findings: list[Item]
    older: list[Item]
    markdown: str
    fixes: bool
    patches: dict[str, Patch]
    withheld: bool
    reported: frozenset[FindingLine]
    older_keys: frozenset[str]

    @property
    def keys(self) -> frozenset[str]:
        """The keys of the findings that the report holds or lists."""
        return frozenset(at.key for at in self.reported)

    @property
    def shows_report(self) -> bool:
        """Whether the review has the scan's report to show, in its body or on the job summary: it
        has text, and is not withheld. The job summary holds the whole of it only up to
        actions.SUMMARY_LIMIT."""
        return bool(self.markdown.strip()) and not self.withheld

    @property
    def lost_the_changes_findings(self) -> bool:
        """Whether the render refused a finding and the report holds no finding of the change."""
        return self.stamp.refused and not self.findings

    @property
    def older_listed(self) -> int:
        """How many flaws the review lists as older than the change."""
        return len(self.older or self.stamp.set_aside)

    @classmethod
    def load(
        cls,
        report_dir: Path,
        stamp: Stamp,
        *,
        top: str,
        merge_base: str,
        fixes: bool,
        drafted: Path | None = None,
    ) -> Report:
        """Everything the review is built from, for a stamp whose change() is known and whose
        merge base this checkout resolves to `merge_base`. patches/ lies in `drafted`, if given, and
        else in the report's directory. It is read only when `fixes` is on, the report withholds
        nothing and the folder is no link. With `drafted` no explanation is read: those of the
        report were written before its fixes, and the review shows the scan's own text.
        ProductError as finding_records(), withholds(), findings_of() and records() raise it."""
        rows = finding_records(report_dir, stamp)
        withheld = withholds(rows, stamp)
        found = findings_of(rows, stamp)
        reported = _reported_in(rows)
        counted = _reported_in([row for row, item in zip(rows, found) if not item.older])
        items = [item for item in found if not item.older]
        older = [item for item in found if item.older]
        items = [item._replace(shared_grade=_shared_grade(item, items)) for item in items]
        folder = explanation.folder_of(report_dir)
        if withheld:
            items = [item.withheld() for item in items]
            older = [item.withheld() for item in older]
        elif drafted is None:
            if not isinstance(folder, Flaw):
                items = [item.explained(folder) for item in items]
            elif items:
                console.warn(f"{folder.reason}, so the review shows the scan's own text")
        patches_dir = (drafted or report_dir) / plugin.PATCHES_DIR_NAME
        wanted = fixes and not withheld
        linked = link.is_link(patches_dir)
        if wanted and linked:
            console.warn(f"{plugin.PATCHES_DIR_NAME} is a link, so no patch is read from it")
        patches_jsonl = patches_dir / plugin.PATCHES_JSONL_NAME
        patch_rows = records(patches_jsonl, required=False) if wanted and not linked else []
        names = _names_by_id(rows, stamp.prefix)
        return cls(
            top=top,
            stamp=stamp,
            commit=stamp.change().commit,
            merge_base=merge_base,
            findings=items,
            older=older,
            markdown=report_markdown(report_dir, withheld=withheld),
            fixes=fixes,
            patches={clean(row.get("id")): Patch.of(row, patches_dir, names) for row in patch_rows},
            withheld=withheld,
            reported=reported,
            older_keys=frozenset(at.key for at in reported) - {at.key for at in counted},
        )
