"""The Finding every product is built from, and build_finding, which validates a raw one."""

from __future__ import annotations

import hashlib
import ntpath
import os
import posixpath
import re
from enum import IntEnum
from itertools import dropwhile
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, TypedDict
from urllib.parse import unquote

from . import absolute, cwe, strictjson
from .strictjson import JsonMap, has_lone_surrogate, is_int, is_list, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class _Predates(TypedDict, total=False):
    """How many of a panel's `true` votes call the flaw older than the change. Only a panel at
    Change Scan Effort high records it."""

    predates: int


class Panel(_Predates):
    """A validated panel round: the vote counts and how many voters cast them."""

    true: int
    false: int
    voters: Literal[2, 3]


class _Listed(TypedDict):
    id: str
    file: str
    line: int
    cwe_id: str
    severity: str
    title: str
    recommendation: str


class AlsoAt(_Listed, total=False):
    """Another confirmed finding, listed under the one the report carries, with its own fix. In a
    Record it also carries the claudeSecurityPluginFindingId it would have alone."""

    claudeSecurityPluginFindingId: str


class FiledAt(TypedDict):
    """A researcher's report that the finding was written in place of."""

    file: str
    line: int
    cwe_id: str
    other_cwe_ids: list[str]
    title: str


class _Optional(TypedDict, total=False):
    """Keys that a finding has only where they apply. They follow `also_at`, in this order."""

    also_filed_at: list[FiledAt]
    older_than_the_change: Literal[True]


class Finding(_Optional):
    """One validated finding, in the JSONL record's field order; the record adds the id (Record).
    `also_filed_at` is present only where it has an entry; `older_than_the_change`, only where
    true."""

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
    via_change: str | None
    other_cwe_ids: list[str]
    also_at: list[AlsoAt]


class Record(Finding):
    """A finding as every product carries it: placed on its line (sarif.placed), its id last."""

    claudeSecurityPluginFindingId: str


FINDING_ID: Final = "claudeSecurityPluginFindingId"


class Severity(IntEnum):
    """A finding's severity."""

    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1

    @classmethod
    def of(cls, record: JsonMap) -> Severity | None:
        """A record's severity from its word, stripped and in any letter case; None when the
        word names none.
        """
        return cls.named(record.get("severity", ""))

    @classmethod
    def named(cls, word: object) -> Severity | None:
        """The severity a word names, stripped and in any letter case; None when it names none."""
        return cls.__members__.get(str(word).strip().upper())


class Confidence(IntEnum):
    """A finding's confidence."""

    low = 1
    medium = 2
    high = 3


PANEL_VOTER_COUNT: Final = 3
PANEL_KEEP_QUORUM: Final = 2

# \Z, not $: `$` also matches before a trailing newline, and this names a file.
FINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")


class FindingError(Exception):
    """A refusal; the message names what a findings.json record got wrong."""


class FindingPathError(FindingError):
    """A refusal of one finding's model-written path; the rest of a report can still carry.

    The message names the finding and quotes the declared path; `finding_id`,
    `wrong` (what is wrong with the path, without the path), `filed_entry`
    and `replaced` are what a caller surviving the refusal may record in any product.
    `finding`, which build_finding() sets on a refusal of a finding's own path, is the refused
    finding with no file, no link to the change and no listed finding, at the severity in its vote
    record where that has one, and at a confidence no higher than its panel's cap. Apart from that,
    a severity, a confidence or a fix that workflows/scan.js took from a listed finding can stay.
    Its texts are a model's and can quote the path: it is for the Markdown report alone.
    """

    finding_id: str
    wrong: str
    cwes: tuple[int, ...] = ()
    snippet: str = ""
    listed: tuple[Finding | FindingPathError, ...] = ()
    filed_entry: int = 0
    replaced: tuple[str, ...] = ()
    uncarried: tuple[FindingPathError, ...] = ()

    def __init__(self, finding_id: str, *, declared: str, wrong: str) -> None:
        super().__init__(f"finding {finding_id} file {declared!r} {wrong}")
        self.finding_id = finding_id
        self.wrong = wrong
        self.finding: Finding

    @property
    def gone_with(self) -> str:
        """The clause that ends a refusal of a finding that replaced reports: it names each of
        `replaced`. Empty where there is none."""
        if not self.replaced:
            return ""
        return f"; the reports that it replaced go with it: {', '.join(self.replaced)}"


def cwe_number(item: JsonMap, finding_id: str) -> int:
    """A finding's CWE number; a cwe_id missing, unreadable or malformed is refused.

    A well-formed id is accepted as declared, whether or not the pinned CWE
    release defines it.
    """
    declared = text_field(item, "cwe_id", finding_id, required=True)
    return cwe_parsed(declared, finding_id, "cwe_id")


def cwe_parsed(declared: str, finding_id: str, field: str) -> int:
    """The number in one CWE id as a record may spell it; anything else is refused."""
    matched = re.fullmatch(
        r"(?:CWE-)?0*([1-9][0-9]{0,4})", declared.strip().upper().replace("_", "-")
    )
    if not matched:
        msg = f"finding {finding_id} {field} {declared!r} is not a CWE id such as CWE-89"
        raise FindingError(msg)
    return int(matched[1])


OVERRULED_NOTE: Final = (
    " could excuse this flaw. The scan took that into account and reports it anyway: "
)
# The research schema opens every change link with "file:line "; sarif.placed reads that site.
LINK_SITE = re.compile(r"(.+?):([1-9][0-9]{0,14})(?:-([1-9][0-9]{0,14}))?\b")


def link_field(item: JsonMap, finding_id: str, scan_root: str, scan_prefix: str) -> str | None:
    """A change scan's via_change with its leading file normalised like `file`; None when absent.

    A link that does not open with a file:line the scan can place is kept as written.
    """
    link = text_field(item, "via_change", finding_id, path=True).strip() or None
    matched = LINK_SITE.match(link or "")
    if not (link and matched):
        return link
    try:
        file = relative_path(matched[1], finding_id, scan_root, scan_prefix, must_exist=False)
    except FindingPathError:
        return link
    return file + link[matched.end(1) :]


def escaped(finding: Record) -> dict[str, object]:
    """`finding` as the JSONL and the SARIF property bag write it: `file`, each listed file
    and `via_change` by `percent`, with `via_change` keeping its "%". The keys of _Optional, in
    their order, and then the id come last, wherever `finding` has them."""
    link = finding["via_change"]
    written = link and percent(link, percent_sign=False)
    record: dict[str, object] = {
        **finding,
        "file": percent(finding["file"]),
        "via_change": written,
        "also_at": [{**entry, "file": percent(entry["file"])} for entry in finding["also_at"]],
    }
    if "also_filed_at" in finding:
        filed = [{**entry, "file": percent(entry["file"])} for entry in finding["also_filed_at"]]
        record["also_filed_at"] = filed
    last = (*_Optional.__annotations__, FINDING_ID)
    return {
        **{key: value for key, value in record.items() if key not in last},
        **{key: record[key] for key in last if key in record},
    }


def percent(path: str, *, percent_sign: bool = True) -> str:
    """`path` with each surrogate in DC80-DCFF written as %XX, the byte it stands for, and with
    `percent_sign` each "%" as %25, so that for a file name decoded with errors="surrogateescape",
    urllib.parse.unquote(result, errors="surrogateescape") gives `path` back."""
    return re.sub(
        "[%\udc80-\udcff]" if percent_sign else "[\udc80-\udcff]",
        lambda c: f"%{c[0].encode('utf-8', 'surrogateescape')[0]:02X}",
        path,
    )


def unpercent(file: str) -> str:
    """A `file` as the JSONL writes it, read back: decoded when `percent` of the decoded name gives
    `file` back, otherwise as written."""
    name = unquote(file, errors="surrogateescape")
    return name if percent(name) == file else file


def other_cwe_numbers(item: JsonMap, finding_id: str, primary: int) -> list[int]:
    """The further CWE numbers a finding carries, the primary and repeats left out."""
    raw = item.get("other_cwe_ids")
    if raw is None:
        return []
    entries = [entry for entry in raw if is_str(entry)] if is_list(raw) else []
    if not is_list(raw) or len(entries) != len(raw):
        msg = f"finding {finding_id} other_cwe_ids is not a list of CWE ids"
        raise FindingError(msg)
    numbers = [cwe_parsed(entry, finding_id, "other_cwe_ids") for entry in entries]
    return [n for n in dict.fromkeys(numbers) if n != primary]


def confidence_value(raw: object) -> Confidence:
    """A finding's stated confidence, in any letter case; refuses any other value."""
    if is_str(raw):
        word = raw.strip().lower()
        if word in Confidence.__members__:
            return Confidence[word]
    msg = f"confidence {raw!r} is not one of {'/'.join(Confidence.__members__)}"
    raise FindingError(msg)


def panel_complete(record: object) -> Panel | None:
    """A round's panel when it records an integer tally and a vote from every voter, or from all
    but one that it marks as not needed, where the others agree; else None, as for any other
    record with that mark."""
    if not is_map(record):
        return None
    panel = record.get("panel")
    if not is_map(panel):
        return None
    panel_true = panel.get("true")
    if not is_int(panel_true):
        return None
    voters: Literal[2, 3] = PANEL_VOTER_COUNT
    if "unasked" in panel:
        unasked = panel["unasked"]
        voters = PANEL_VOTER_COUNT - 1
        if not is_int(unasked) or unasked != 1 or panel_true not in {0, voters}:
            return None
    cast = panel.get("voters")
    if not is_int(cast) or cast != voters:
        return None
    false_votes, predates = panel.get("false"), panel.get("predates")
    complete: Panel = {
        "true": panel_true,
        "false": false_votes if is_int(false_votes) else 0,
        "voters": voters,
    }
    if is_int(predates) and 0 <= predates <= panel_true:
        complete["predates"] = predates
    return complete


def vote_rounds(votes: JsonMap) -> JsonMap:
    """The vote record's rounds by id, or an empty map when it holds none."""
    raw = votes.get("rounds")
    return raw if is_map(raw) else {}


FINDINGS_DIGEST_KEY: Final = "findings_sha256"


def findings_digest(run_dir: Path) -> str:
    """The SHA-256 of the run directory's findings.json."""
    return hashlib.sha256((run_dir / "findings.json").read_bytes()).hexdigest()


def findings_changed(run_dir: Path, votes: JsonMap) -> bool:
    """Whether `votes` holds a digest that the run directory's findings.json does not match."""
    return FINDINGS_DIGEST_KEY in votes and votes[FINDINGS_DIGEST_KEY] != findings_digest(run_dir)


def finding_panels(rounds: JsonMap, ids: list[str]) -> list[tuple[str, Panel | None]]:
    """Each finding id with its complete panel in the rounds, or None, in the order given."""
    return [(i, panel_complete(rounds.get(i))) for i in ids]


def panel_severity(record: object, recorded: Severity) -> Severity:
    """The severity in a finding's vote record, or `recorded` where it holds none."""
    held = record.get("severity") if is_map(record) else None
    final = held.get("final") if is_map(held) else None
    return Severity.named(final) or recorded


def vote_confidence_ceiling(record: object) -> Confidence | None:
    """A finding's vote-backed confidence: `high` if unanimous, `medium` if complete, else None."""
    panel = panel_complete(record)
    if panel is None:
        return None
    return Confidence.high if panel["true"] >= panel["voters"] else Confidence.medium


def older_than_the_change(finding: Finding, rounds: JsonMap) -> Finding:
    """`finding` as Change Scan Effort high reports it: marked `older_than_the_change`, and its
    `via_change` None, where its own panel, and the panel of each finding that it lists, reach the
    keep quorum, but not without the votes that call the flaw older than the change."""

    def older(panel: Panel | None) -> bool:
        if panel is None:
            return False
        return panel["true"] >= PANEL_KEEP_QUORUM > panel["true"] - panel.get("predates", 0)

    ids = [finding["id"], *(entry["id"] for entry in finding["also_at"])]
    if not all(older(panel) for _, panel in finding_panels(rounds, ids)):
        return finding
    return {**finding, "via_change": None, "older_than_the_change": True}


def strength(finding: Finding) -> tuple[Severity, Confidence]:
    """A finding's rank: severity first, then confidence."""
    return Severity[finding["severity"]], Confidence[finding["confidence"]]


def highest(grades: Iterable[tuple[Severity, Confidence]]) -> tuple[Severity, Confidence]:
    """The highest severity and the highest confidence among `grades`, each by itself."""
    severities, confidences = zip(*grades)
    return max(severities), max(confidences)


def line_number(raw: object) -> int | None:
    """A findings.json line value as an integer: an int, or digits in a string; None otherwise."""
    if is_str(raw) and re.fullmatch(r"\s*-?[0-9]{1,15}\s*", raw):
        return int(raw.strip())
    return raw if is_int(raw) else None


def line_field(item: JsonMap, key: str, finding_id: str, default: int) -> int:
    """One of a finding's line fields as an integer (line_number); absent reads as `default`."""
    line = line_number(item.get(key, default))
    if line is None:
        msg = f"finding {finding_id} {key} {item.get(key)!r} is not an integer"
        raise FindingError(msg)
    return line


def repository_file(scan_prefix: str, *, file: str) -> str:
    """A scan-root-relative `file` made repository-relative by a lexical fold."""
    return posixpath.normpath(scan_prefix + file)


def scan_prefix_fits(prefix: str, *, scan_root: str) -> bool:
    """Whether `prefix` has no more components than the scan root's real path, as a prefix git
    printed always does."""
    try:
        return prefix.count("/") <= len(Path(os.path.realpath(scan_root)).parents)
    except (OSError, ValueError):
        return False


def scan_prefix_shaped(prefix: str) -> bool:
    """Whether `prefix` is empty, or a relative path that ends in a slash, such as `a/b/`. It holds
    no empty, "." or ".." part, no backslash and no Windows drive."""
    if not prefix:
        return True
    return (
        prefix.endswith("/")
        and "\\" not in prefix
        and not ntpath.splitdrive(prefix)[0]
        and all(segment not in {"", ".", ".."} for segment in prefix.split("/")[:-1])
    )


def text_field(
    item: JsonMap, key: str, finding_id: str, required: bool = False, *, path: bool = False
) -> str:
    """One of a finding's text fields; absent or null reads as empty unless it is required.

    With `path`, the field may hold a file name that is not UTF-8 (strictjson.surrogates_are_bytes).
    """
    value = item.get(key)
    if value is None:
        text = ""
    elif is_str(value):
        text = value
    else:
        msg = f"finding {finding_id} {key} is {type(value).__name__}, not a string"
        raise FindingError(msg)
    lone = not strictjson.surrogates_are_bytes(text) if path else has_lone_surrogate(text)
    if lone:
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
    item: JsonMap,
    finding_id: str,
    scan_root: str,
    scan_prefix: str,
    must_exist: bool,
    *,
    blank_alone: bool = False,
) -> str:
    """A finding's file relative to the scan root; a path that leaves the repository is refused.

    `scan_prefix` is the scan root's path below the repository top level (`a/b/`, or empty).
    With `must_exist` (a codebase scan) a missing file is refused. relative_path has the rules.
    With `blank_alone`, a file that is a blank string raises FindingPathError, so that finding
    alone is refused; without it, FindingError.
    """
    spelled = item.get("file")
    if is_str(spelled) and not strictjson.surrogates_are_bytes(spelled):
        wrong = "holds characters this report cannot write"
        raise FindingPathError(finding_id, declared=spelled, wrong=wrong)
    if blank_alone and is_str(spelled) and not spelled.strip():
        raise FindingPathError(finding_id, declared=spelled, wrong="is blank")
    declared = text_field(item, "file", finding_id, required=True, path=True).strip()
    return relative_path(declared, finding_id, scan_root, scan_prefix, must_exist)


def located(spelled: str, *, root: Path, top: Path) -> Path | None:
    """The path `spelled` resolves to from the scan root `root` or the repository top level `top`.

    The result may lie outside the repository, through a link. None when no place holds the folder
    the path names and the path has a `..` after its leading climb.
    """
    if Path(spelled).is_absolute():
        return Path(os.path.realpath(spelled))
    missing: Path | None = None
    for base in dict.fromkeys((root, top)):
        spelled_from = Path(base, spelled)
        if top not in Path(os.path.normpath(spelled_from)).parents:
            continue
        inside = Path(os.path.realpath(spelled_from.parent)).is_relative_to(top)
        if inside and not spelled_from.parent.is_dir():
            continue
        if not inside and missing is not None:
            continue
        file = Path(os.path.realpath(spelled_from))
        if not inside or top not in file.parents:
            if missing is None:
                return file
            continue
        if file.exists():
            return file
        if missing is None:
            missing = file
    if missing is None and ".." not in dropwhile(lambda part: part == "..", Path(spelled).parts):
        return Path(os.path.realpath(Path(root, spelled)))
    return missing


def relative_path(
    declared: str, finding_id: str, scan_root: str, scan_prefix: str, must_exist: bool
) -> str:
    """A file as a finding spells it, resolved and made relative to the scan root.

    The path is refused when it resolves outside the repository, to the scan root or above, or
    to a missing file that a codebase scan needs or whose stored path would name another file.
    """
    depth = scan_prefix.count("/")
    escapes = f"escapes the {'repository' if depth else 'scan root'}"
    unresolved = "cannot be resolved"
    elsewhere = "could be mistaken for a path at the repository top level"
    root = Path(os.path.realpath(scan_root))
    top = (root, *root.parents)[depth]
    written = Path(os.path.normpath(Path(root, declared)))
    kept = "\\" in declared and os.name != "nt" and top in written.parents
    kept = kept and os.path.lexists(os.path.join(scan_root, declared))
    spelled = declared if kept else declared.replace("\\", "/")
    prefix = scan_root.replace("\\", "/").rstrip("/") + "/"
    if scan_root and spelled.startswith(prefix):
        spelled = spelled[len(prefix) :].lstrip("/")
    leaves = top not in Path(os.path.normpath(Path(root, spelled))).parents
    if leaves and not Path(spelled).is_absolute():
        raise FindingPathError(finding_id, declared=declared, wrong=escapes)
    try:
        file = located(spelled, root=root, top=top)
    except (OSError, ValueError) as error:
        wrong = escapes if leaves else unresolved
        raise FindingPathError(finding_id, declared=declared, wrong=wrong) from error
    if file is None:
        unreadable = "cannot be read from the scan root or the repository top level"
        raise FindingPathError(finding_id, declared=declared, wrong=unreadable)
    if top not in file.parents:
        raise FindingPathError(finding_id, declared=declared, wrong=escapes)
    if root.is_relative_to(file):
        raise FindingPathError(finding_id, declared=declared, wrong="names a folder, not a file")
    relative = Path(os.path.relpath(file, root)).as_posix()
    if leaked_spelling(relative, first=relative.split("/")[0], scan_root=scan_root):
        raise FindingPathError(finding_id, declared=declared, wrong=escapes)
    try:
        exists = file.exists()
    except OSError as error:
        raise FindingPathError(finding_id, declared=declared, wrong=unresolved) from error
    if exists:
        return relative
    if must_exist:
        raise FindingPathError(
            finding_id, declared=declared, wrong="does not exist in the scanned tree"
        )
    try:
        again = located(relative, root=root, top=top)
    except OSError as error:
        raise FindingPathError(finding_id, declared=declared, wrong=unresolved) from error
    if (
        again is None
        or top not in again.parents
        or Path(os.path.relpath(again, root)).as_posix() != relative
    ):
        raise FindingPathError(finding_id, declared=declared, wrong=elsewhere)
    return relative


class Built(NamedTuple):
    """What build_finding returns: the finding, the path error of each listed finding it refused,
    each listed finding it kept, in full, and the path error of each replaced report it left out."""

    finding: Finding
    refused: list[FindingPathError]
    carried: list[Finding]
    uncarried: list[FindingPathError]


def listed_in(
    record: JsonMap, key: Literal["also_at", "also_filed_at"] = "also_at"
) -> list[JsonMap] | None:
    """The objects `record` lists under `key`: empty when the field is absent or null, None when
    it is anything but a list of objects."""
    raw = record.get(key)
    if raw is None:
        return []
    if not is_list(raw):
        return None
    entries = [entry for entry in raw if is_map(entry)]
    return entries if len(entries) == len(raw) else None


def also_at_entries(item: JsonMap, finding_id: str) -> list[JsonMap]:
    """The findings `item` lists in `also_at`, as written; absent reads as none. Raises
    FindingError if it is not a list of objects, or an entry has no id, has a further CWE, or
    lists findings or replaced reports itself."""
    entries = listed_in(item)
    if entries is None:
        msg = f"finding {finding_id} also_at is not a list of objects"
        raise FindingError(msg)
    if not all(is_str(entry.get("id")) and entry.get("id") for entry in entries):
        msg = f"finding {finding_id} also_at lists a finding without an id"
        raise FindingError(msg)
    if any(entry.get("other_cwe_ids") or entry.get("also_at") for entry in entries):
        msg = (
            f"finding {finding_id} also_at lists a finding that has other_cwe_ids or an also_at "
            "of its own"
        )
        raise FindingError(msg)
    if any(entry.get("also_filed_at") for entry in entries):
        msg = f"finding {finding_id} also_at lists a finding that has an also_filed_at"
        raise FindingError(msg)
    return entries


def replaced_reports(
    item: JsonMap, finding_id: str, scan_root: str, scan_prefix: str, must_exist: bool
) -> list[FiledAt | FindingPathError]:
    """The reports `item` lists in `also_filed_at`; absent reads as none. An entry whose path cannot
    be carried gives its path error, which bears the entry's number. Raises FindingError if the
    field is not a list of objects, or an entry is malformed."""
    entries = listed_in(item, "also_filed_at")
    if entries is None:
        msg = f"finding {finding_id} also_filed_at is not a list of objects"
        raise FindingError(msg)

    def report(entry: JsonMap, place: int) -> FiledAt | FindingPathError:
        whose = f"{finding_id} also_filed_at entry {place}"
        if not is_str(spelled := entry.get("file")) or strictjson.surrogates_are_bytes(spelled):
            text_field(entry, "file", whose, required=True, path=True)
        line = line_field(entry, "line", whose, 0)
        number = cwe_number(entry, whose)
        others = other_cwe_numbers(entry, whose, number)
        title = text_field(entry, "title", whose, required=True)
        try:
            file = file_field(entry, finding_id, scan_root, scan_prefix, must_exist)
        except FindingPathError as error:
            error.filed_entry = place
            return error
        return {
            "file": file,
            "line": line,
            "cwe_id": f"CWE-{number}",
            "other_cwe_ids": [f"CWE-{n}" for n in others],
            "title": title,
        }

    return [report(entry, place) for place, entry in enumerate(entries, 1)]


def build_finding(
    raw: object,
    index: int,
    rounds_by_id: JsonMap,
    scan_root: str,
    scan_prefix: str,
    must_exist: bool,
    *,
    blank_alone: bool = False,
) -> Built:
    """Validate one raw findings.json record, each finding it lists in `also_at` and each report in
    `also_filed_at`; the finding shows the highest severity and the highest confidence among itself
    and the findings it lists. `blank_alone` goes to file_field for the record and for each finding
    that it lists in `also_at`."""
    if not is_map(raw):
        msg = f"findings.json item {index} is not an object"
        raise FindingError(msg)
    numbered = f"F{index + 1}"
    finding_id = text_field(raw, "id", numbered) or numbered
    if not FINDING_ID_RE.match(finding_id):
        msg = f"finding id {finding_id!r} is not a valid id"
        raise FindingError(msg)

    severity = Severity.of(raw)
    if severity is None:
        msg = (
            f"finding {finding_id} severity {raw.get('severity')!r} is not one of "
            f"{'/'.join(Severity.__members__)}"
        )
        raise FindingError(msg)

    confidence = confidence_value(raw.get("confidence"))
    ceiling = vote_confidence_ceiling(rounds_by_id.get(finding_id))
    if ceiling is not None:
        confidence = min(confidence, ceiling)

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
    title = text_field(raw, "title", finding_id, required=True)
    impact = text_field(raw, "impact", finding_id)
    description = text_field(raw, "description", finding_id, required=True)
    exploit_scenario = text_field(raw, "exploit_scenario", finding_id).strip()
    recommendation = text_field(raw, "recommendation", finding_id)
    snippet = text_field(raw, "snippet", finding_id).strip()
    symbol = text_field(raw, "symbol", finding_id)
    via_change = link_field(raw, finding_id, scan_root, scan_prefix)
    further = other_cwe_numbers(raw, finding_id, number)
    replaced = replaced_reports(raw, finding_id, scan_root, scan_prefix, must_exist)
    also_filed_at = [entry for entry in replaced if not isinstance(entry, FindingPathError)]
    uncarried = [entry for entry in replaced if isinstance(entry, FindingPathError)]

    def listed_finding(entry: JsonMap) -> Finding | FindingPathError:
        try:
            built = build_finding(
                entry,
                index,
                rounds_by_id,
                scan_root,
                scan_prefix,
                must_exist,
                blank_alone=blank_alone,
            )
        except FindingPathError as error:
            return error
        return built.finding

    listed = [listed_finding(entry) for entry in also_at_entries(raw, finding_id)]
    refused = [entry for entry in listed if isinstance(entry, FindingPathError)]
    carried = [entry for entry in listed if not isinstance(entry, FindingPathError)]
    also_at: list[AlsoAt] = [
        {
            "id": entry["id"],
            "file": entry["file"],
            "line": entry["line"],
            "cwe_id": entry["cwe_id"],
            "severity": entry["severity"],
            "title": entry["title"],
            "recommendation": entry["recommendation"],
        }
        for entry in carried
    ]
    top_severity, top_confidence = highest([(severity, confidence), *map(strength, carried)])
    refusal: FindingPathError | None = None
    try:
        file = file_field(
            raw, finding_id, scan_root, scan_prefix, must_exist, blank_alone=blank_alone
        )
    except FindingPathError as error:
        error.cwes, error.snippet, error.listed = (number, *further), snippet, tuple(listed)
        error.replaced = tuple(
            f"also_filed_at entry {e.filed_entry} (its file {e.wrong})"
            if isinstance(e, FindingPathError)
            else f"{percent(e['file'])}:{e['line']}"
            for e in replaced
        )
        error.uncarried = tuple(uncarried)
        refusal, file = error, ""

    finding: Finding = {
        "id": finding_id,
        "title": title,
        "impact": impact,
        "file": file,
        "line": line,
        "description": description,
        "exploit_scenario": exploit_scenario,
        "preconditions": preconditions,
        "category": cwe.catalog.category_name(number),
        "severity": top_severity.name,
        "confidence": top_confidence.name,
        "recommendation": recommendation,
        "cwe_id": f"CWE-{number}",
        "snippet": snippet,
        "symbol": symbol,
        "declared_line": declared_line,
        "via_change": via_change,
        "other_cwe_ids": [f"CWE-{n}" for n in further],
        "also_at": also_at,
    }
    if also_filed_at:
        finding["also_filed_at"] = also_filed_at
    if refusal:
        refusal.finding = {
            **finding,
            "severity": panel_severity(rounds_by_id.get(finding_id), severity).name,
            "confidence": confidence.name,
            "also_at": [],
            "via_change": None,
        }
        raise refusal
    return Built(finding, refused, carried, uncarried)


def unrecognized_cwes(findings: Sequence[Finding]) -> list[str]:
    """One disclosure sentence per finding whose declared CWE the pinned release does not define,
    including each finding that is listed under another."""
    shown = ((item["id"], item["cwe_id"], "filed as Uncategorized") for item in findings)
    listed = (
        (other["id"], other["cwe_id"], f"listed under {item['id']}")
        for item in findings
        for other in item["also_at"]
    )
    return [
        f"finding {name} cwe_id {cwe_id} is not a weakness in CWE {cwe.catalog.version}; {where}"
        for name, cwe_id, where in (*shown, *listed)
        if not cwe.catalog.defines(cwe.id_number(cwe_id))
    ]
