"""The refusals of an attack surface analysis, and the checks on the record that a stage leaves for
each finding."""

from __future__ import annotations

import contextlib
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, NoReturn

from . import git, secret, source, strictjson
from .finding import (
    Built,
    Confidence,
    Finding,
    FindingError,
    FindingPathError,
    Severity,
    build_finding,
    file_field,
    line_field,
    listed_in,
    text_field,
)
from .markdown import one_line
from .strictjson import JsonMap, is_list, is_map, is_str
from .surface_dir import paths_in

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from .surface_dir import Stage

PLACE_KEYS: Final = ("file", "line", "snippet", "symbol")
TEXT_KEYS: Final = ("title", "impact", "description", "exploit_scenario", "recommendation")
KEPT: Final = ("id", "cwe_id", "preconditions", *PLACE_KEYS, *TEXT_KEYS)
NO_SUCH_LINE: Final = "its line is not the number of a line of"
UNSHOWN_CHAIN: Final = (
    "This item's `chain` is not text that this report can show: see its `.json` file, in its "
    "stage's `findings` folder."
)
FAULT_HEAD: Final = 120
FAULT_TAIL: Final = 60


class AnalysisError(Exception):
    """What is wrong, in a message that says how to fix it. A RecordError leaves one record out; any
    other is a refusal."""


class RecordError(AnalysisError):
    """A fault in one record. That record is left out, and the analysis goes on."""


def refuse(fault: str) -> NoReturn:
    raise AnalysisError(fault)


def unusable(fault: str) -> NoReturn:
    raise RecordError(fault)


class Outcome(Enum):
    """The outcome of a finding, in the report's order. Each member has its word, whether the
    independent check gives it, and the report's heading for its findings. CONFIRMED has no heading,
    since the report shows those findings in full. `count_word` is the word in a stage's counts: the
    member's word, unless it gives another."""

    CONFIRMED = ("confirmed", True, "")
    OBSERVED = ("observed", False, "Flagged along the way", "flagged")
    UNRESOLVED = ("unresolved", True, "Unresolved: the independent check did not settle it")
    LEFT_OUT = ("left out", False, "Left out: its record could not be used")
    UNPROVEN = (
        "unproven",
        False,
        "Unproven: its trace was not completed, or it waits on your answer",
    )
    REFUTED = ("refuted", True, "Refuted by the independent check")

    def __init__(self, word: str, from_check: bool, heading: str, count_word: str = "") -> None:
        self.word = word
        self.from_check = from_check
        self.heading = heading
        self.count_word = count_word or word

    @classmethod
    def named(cls, word: object) -> Stated | None:
        """The outcome that a record's word states, stripped and in any letter case; None when it
        states none. No word gives LEFT_OUT."""
        return STATED.get(word.strip().lower()) if is_str(word) else None


Stated = Literal[
    Outcome.CONFIRMED, Outcome.OBSERVED, Outcome.UNRESOLVED, Outcome.UNPROVEN, Outcome.REFUTED
]
STATED: Final[dict[str, Stated]] = {
    each.word: each for each in Outcome if each is not Outcome.LEFT_OUT
}


class Entry(NamedTuple):
    """One finding's record, checked. `evidence` is a path below the output directory, `place` an
    observed finding's file and line. `verification`, `question` and `chain` are as one_line() gives
    them. A refuted record's `chain` is empty, and one that cannot be shown is UNSHOWN_CHAIN."""

    id: str
    stage: Stage
    outcome: Stated
    evidence: str
    title: str
    verification: str
    question: str
    chain: str
    place: str = ""


class LeftOut(NamedTuple):
    """A record that cannot be used. `evidence` is as an Entry's, and `fault` says what is wrong."""

    id: str
    stage: Stage
    evidence: str
    fault: str

    @property
    def outcome(self) -> Literal[Outcome.LEFT_OUT]:
        return Outcome.LEFT_OUT


class Rated(NamedTuple):
    """A confirmed finding: its `entry`, and what only a confirmed finding has. `raw` is what
    build_finding takes. `finding` is what it gives for this record alone, on the line where the
    file places it. `stated` is the stage's rating, and `checked` the independent check's: the
    finding shows the lower. `gate` is the outcome that the record states for its gate's claim, or
    None. With `off_disk`, its file is an OffDisk."""

    entry: Entry
    raw: JsonMap
    finding: Finding
    stated: Severity
    checked: Severity
    gate: Stated | None
    off_disk: bool

    @property
    def severity(self) -> Severity:
        return Severity[self.finding["severity"]]


class OnDisk(NamedTuple):
    """A record's file that is on disk. `file` is its path below the checkout. `text` is its text,
    or None if it cannot be read."""

    file: str
    text: str | None


class OffDisk(NamedTuple):
    """A record's file that git keeps off the disk, as a sparse checkout does. `text` is its text in
    the commit that is checked out."""

    file: str
    text: str


def commit_text(root: str, file: str) -> str | None:
    """The text of `file` in the commit that is checked out, if git keeps the file off the disk.
    None for any other file, and where git does not give the text. `file` is a path below `root`,
    as file_field() gives it, and is not on disk."""
    no_fetch = {"GIT_NO_LAZY_FETCH": "1"}
    listing = ("ls-files", "-v", "-s", "--", git.argument(file))
    if not (git.run(root, "--literal-pathspecs", *listing, env=no_fetch) or "").startswith("S 100"):
        return None
    try:
        return git.run(
            root, "cat-file", "blob", git.argument(f"HEAD:./{file}"), env=no_fetch, exact=True
        )
    except MemoryError:
        return None


def file_of(row: JsonMap, name: str, root: str) -> OnDisk | OffDisk:
    """The file that the record `row` names, and its text, which is read once. A file that is not on
    disk is refused, unless commit_text() has its text."""
    try:
        file = file_field(row, name, root, "", must_exist=True)
    except FindingPathError:
        with contextlib.suppress(FindingPathError):
            file = file_field(row, name, root, "", must_exist=False)
            if (text := commit_text(root, file)) is not None:
                return OffDisk(file, text)
        raise
    return OnDisk(file, source.read(root, file))


def refused_now(row: JsonMap, root: str) -> FindingPathError | None:
    """What file_field() now refuses the file of `row` for, a finding that was built before, or
    None."""
    try:
        file_field(row, str(row.get("id")), root, "", must_exist=True)
    except FindingPathError as error:
        return error
    return None


def built(raw: JsonMap, root: str, off_disk_ids: Collection[str]) -> Built:
    """`raw`, checked by the scanner's own build_finding as a finding of a scan of the whole
    checkout. `off_disk_ids` holds the id of each finding whose file need not be on disk
    (Rated.off_disk). If `raw` or a finding that it lists is among them, `refused` also holds the
    refusal of each other file that is not on disk, that of `raw` too."""
    rows = [raw, *(listed_in(raw) or ())]
    expected = [row for row in rows if row.get("id") not in off_disk_ids]
    must_exist = len(expected) == len(rows)
    made = build_finding(
        raw,
        index=0,
        rounds_by_id={},
        scan_root=root,
        scan_prefix="",
        must_exist=must_exist,
    )
    if must_exist:
        return made
    asked = filter(None, (refused_now(row, root) for row in expected))
    refused = {error.finding_id: error for error in (*made.refused, *asked)}
    return made._replace(refused=list(refused.values()))


def line_count(text: str) -> int:
    """How many lines a file's text has. LF, CR LF and CR each end a line. A line break at the end
    of the text does not start another line."""
    return text.replace("\r\n", "\n").replace("\r", "\n").removesuffix("\n").count("\n") + 1


def placed(found: OnDisk | OffDisk, line: int, snippet: str = "") -> int:
    """The line of a record's file that places the record, from the line that the record declares
    and the code that it quotes. A record whose place is past the file's last line is left out. If
    the file cannot be read, the declared line stays."""
    at = source.placed_line(found.text, line, snippet)
    if found.text is not None and at > line_count(found.text):
        unusable(f"{NO_SUCH_LINE} {found.file}")
    return at


def rated(row: JsonMap, entry: Entry, root: str, found: OnDisk | OffDisk) -> Rated:
    """A confirmed record, checked as a scan's finding is. It must also have an exploit scenario. It
    shows the lower of its two severities. Its `verification` says what the independent check
    narrowed or corrected, and its confidence is high only if `verification` is empty. If git keeps
    its file off the disk, the code that it quotes must stand in the commit's copy. A finding of a
    hard-coded credential may quote none."""
    stated, checked = Severity.of(row), Severity.named(row.get("checked_severity"))
    if stated is None or checked is None:
        unusable(
            "its severity and checked_severity are not each one of "
            + "/".join(Severity.__members__)
        )
    if not is_list(row.get("preconditions")):
        unusable("its preconditions are not a list")
    text_field(row, "exploit_scenario", entry.id, required=True)
    raw = {
        **{key: row[key] for key in KEPT if key in row},
        "severity": min(stated, checked).name,
        "confidence": (Confidence.medium if entry.verification else Confidence.high).name,
    }
    off_disk_ids = {entry.id} if isinstance(found, OffDisk) else ()
    alone = built(raw, root, off_disk_ids).finding
    if isinstance(found, OffDisk) and not (
        source.quoted_lines(found.text, alone["snippet"], whole=False)
        or (not alone["snippet"] and secret.is_credential(alone))
    ):
        unusable(f"it quotes no code from the commit's copy of {found.file}")
    line = placed(found, alone["line"], alone["snippet"])
    needs = [item for item in alone["preconditions"] if one_line(item)]
    raw = {**raw, "line": line, "declared_line": alone["line"], "preconditions": needs}
    finding = built(raw, root, off_disk_ids).finding
    return Rated(
        entry=entry,
        raw=raw,
        finding=finding,
        stated=stated,
        checked=checked,
        gate=gate_of(row),
        off_disk=isinstance(found, OffDisk),
    )


def gate_of(row: JsonMap) -> Stated | None:
    """The outcome that a record states for its gate's claim, or None."""
    said = row.get("gate")
    refuted = is_str(said) and said.strip().lower().startswith(Outcome.REFUTED.word)
    return Outcome.REFUTED if refuted else Outcome.named(said)


def refuses_its_gate(record: Path) -> bool:
    """Whether the file `record` states refuted for its gate's claim, also where the record cannot
    be used, or its finding is not confirmed. Its `id` must be its file's name."""
    try:
        row = strictjson.load(record)
    except (ValueError, OSError):
        return False
    return is_map(row) and row.get("id") == record.stem and gate_of(row) is Outcome.REFUTED


def attack_chain(row: JsonMap, name: str, outcome: Stated) -> str:
    """A record's `chain`, on one line. Empty if the finding is refuted, or `chain` is absent, null
    or blank. UNSHOWN_CHAIN for any other value that is not text that the report can carry."""
    if outcome is Outcome.REFUTED:
        return ""
    try:
        return one_line(text_field(row, "chain", name))
    except FindingError:
        return UNSHOWN_CHAIN


def read_record(record: Path, stage: Stage, out: Path) -> Entry | Rated:
    """Read one finding's record, and check what can be checked without the other records."""
    name, root, evidence = record.stem, str(out.parent), record.with_suffix(".md")
    if not stage.holds(name):
        ids = f"stage {stage.number}'s ids ({stage.id_range})"
        unusable(f"its name is not one of {ids}, so it was not read")
    if not evidence.is_file():
        unusable(f"its evidence record, {evidence.name}, is not beside it")
    if not record.is_file():
        unusable(f"it is missing, though its evidence record, {evidence.name}, is there")
    try:
        row = strictjson.load(record)
    except ValueError as error:
        unusable(f"it is not JSON: {error}")
    if not is_map(row) or row.get("id") != name:
        unusable(f"it is not one JSON object whose id is {name}")
    outcome = Outcome.named(row.get("outcome"))
    if outcome is None:
        unusable(f"its outcome is none of {', '.join(STATED)}")
    confirmed = outcome is Outcome.CONFIRMED
    shown = {key: one_line(text_field(row, key, name)) for key in ("verification", "question")}
    if not confirmed and not shown["verification"]:
        unusable("its verification is missing or empty")
    entry = Entry(
        name,
        stage,
        outcome,
        evidence.relative_to(out).as_posix(),
        title=text_field(row, "title", name, required=True),
        verification=shown["verification"],
        question=shown["question"],
        chain=attack_chain(row, name, outcome),
    )
    if not confirmed and outcome is not Outcome.OBSERVED:
        return entry
    found, line = file_of(row, name, root), line_field(row, "line", name, 0)
    if line < 1 or not (isinstance(found, OffDisk) or Path(root, found.file).is_file()):
        unusable(f"{NO_SUCH_LINE} {found.file}")
    if confirmed:
        return rated(row, entry, root, found)
    return entry._replace(place=f"{found.file}:{placed(found, line)}")


def entry_of(record: Path, stage: Stage, out: Path) -> Entry | Rated | LeftOut:
    """One finding's record, or a LeftOut if it cannot be used."""
    try:
        return read_record(record, stage, out)
    except (RecordError, FindingError, OSError) as error:
        same_stem = [path for path in sorted(record.parent.iterdir()) if path.stem == record.stem]
        files = [p for p in (record.with_suffix(".md"), record) if p in same_stem and p.is_file()]
        shown = next(iter([*files, *same_stem]), record)
        evidence = shown.relative_to(out).as_posix()
        return LeftOut(record.stem, stage, evidence=evidence, fault=fault(error))


def fault(error: Exception) -> str:
    """What is wrong with a record, or with another file that a stage left, in a few words."""
    if isinstance(error, FindingPathError):
        return f"its file {error.wrong}"
    if isinstance(error, OSError):
        return f"it cannot be read: {error.strerror}"
    text = " ".join(filter(None, str(error).splitlines()))
    return min(text, f"{text[:FAULT_HEAD]} ... {text[-FAULT_TAIL:]}", key=len)


def records_in(out: Path, stage: Stage) -> list[Path]:
    """The path of each record of a stage, whether or not the file is there: one for each name in
    findings/, without its last suffix. Hidden files are skipped."""
    folder = out / stage.folder / "findings"
    names = {path.stem for path in paths_in(folder) if not path.name.startswith(".")}
    return [folder / f"{name}.json" for name in sorted(names)]


def gathered(out: Path, stages: Iterable[Stage]) -> tuple[list[Entry | LeftOut], dict[str, Rated]]:
    """Every record of the stages, and the confirmed findings among them by id."""
    read = [entry_of(record, stage, out) for stage in stages for record in records_in(out, stage)]
    confirmed = {each.entry.id: each for each in read if isinstance(each, Rated)}
    return [each.entry if isinstance(each, Rated) else each for each in read], confirmed
