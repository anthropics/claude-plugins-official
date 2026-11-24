"""What one run of the Actions job leaves on a pull request for a later run: the marker a
finding's review comment ends with, the line each later part of its fix ends with, and the line a
review's body ends with. Each is read back here, only as spelt here. lib/receipt.py says which
reviews the job posted, from their texts and their comments."""

from __future__ import annotations

import enum
import posixpath
import re
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import quote, unquote

from . import sarif, verdict
from .absolute import below_top
from .finding import FINDING_ID, Confidence, Severity
from .gfm import one_line, plain_line
from .gh import in_carets
from .strictjson import as_int, clean, is_int, is_str
from .unidiff import HUNK

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from .effort import ChangeScanEffort
    from .strictjson import JsonMap

_HIDDEN_LINE_OPENING = "<!-- claude-security "
MARKER = _HIDDEN_LINE_OPENING + "finding {} -->"
LOCATION = " at {}:{}"
GRADE = " severity={} confidence={}"
SHARED = " shared"
_PART = "\n\n" + _HIDDEN_LINE_OPENING + "part {} -->"
_PART_RE = re.compile(_PART.format(f"({sarif.FINGERPRINT_PATTERN})") + r"\s*\Z")
_SEVERITY_PATTERN = "({})".format("|".join(Severity.__members__))
_CONFIDENCE_PATTERN = "({})".format("|".join(Confidence.__members__))


class Tag(enum.Enum):
    """What a finding's lead comment carried, least first. The marker spells it after the place."""

    WITHHELD = " withheld"
    # The write-up. Empty, so that a marker with no tag reads as one.
    WRITE_UP = ""
    FIX = " fix"

    @property
    def rank(self) -> int:
        """Its position in that order: a comment of higher rank carried more."""
        return list(Tag).index(self)


# The account that every workflow's GITHUB_TOKEN posts as.
POSTER_LOGIN = "github-actions[bot]"
# What is asked of GitHub for each earlier review comment; only this module reads these keys.
COMMENT_FIELDS = (
    ".[] | {path, start_line, line, original_start_line, original_line, diff_hunk, body, "
    "html_url, review: .pull_request_review_id, login: .user.login, type: .user.type}"
)
TRAILER_RE = re.compile(
    MARKER.format(
        f"({sarif.FINGERPRINT_PATTERN})"
        f"{LOCATION.format('([!-9;-~]+)', '(-?[0-9]{1,15})')}"
        f"({'|'.join(re.escape(tag.value) for tag in Tag)})"
        f"(?:{GRADE.format(_SEVERITY_PATTERN, _CONFIDENCE_PATTERN)}({SHARED})?)?"
    )
    + r"\s*\Z"
)
VERDICT_LINE = _HIDDEN_LINE_OPENING + "{} fail_on={} head={} base={} change_scan_effort={} -->"
VERDICT_OPENING = f"{_HIDDEN_LINE_OPENING}{verdict.KEYS[0]}="
NO_VERDICT_LINE = f"{VERDICT_OPENING}none -->"
# The key=value tokens a verdict line carries: Verdict.lines in lib/verdict.py writes them.
TOKENS_RE = re.compile(
    f"{verdict.KEYS[0]}=(?:{verdict.PASS}|{verdict.FAIL}) "
    + " ".join(f"{key}=[0-9]{{1,6}}" for key in verdict.KEYS[1:])
)
# What is asked of GitHub for each review on a pull request; Recorded.of reads exactly these keys.
REVIEW_FIELDS = (
    ".[] | {id, body, commit_id, submitted_at, html_url, login: .user.login, type: .user.type}"
)
REF_LIMIT = 255
BASE_REF_RE = re.compile(rf"[A-Za-z0-9._/-]{{1,{REF_LIMIT}}}\Z")


class Terms(NamedTuple):
    """What a verdict was reached under, and must be repeated under: the policy, the Change Scan
    Effort, the head commit and the base branch's name."""

    policy: verdict.FailOn
    change_scan_effort: ChangeScanEffort
    head: str
    base: str

    def line(self, tokens: Sequence[str]) -> str | None:
        """The last line of a review body for the key=value `tokens` of a verdict reached under
        these terms; None when the base is not a name the line carries as written."""
        if not BASE_REF_RE.match(self.base):
            return None
        return VERDICT_LINE.format(
            " ".join(tokens), self.policy.value, self.head, self.base, self.change_scan_effort.value
        )


def _posted_by_a_workflow(record: JsonMap) -> bool:
    """Whether a workflow's GITHUB_TOKEN posted the review or comment `record`."""
    return record.get("login") == POSTER_LOGIN and record.get("type") == "Bot"


class Comment(NamedTuple):
    """One inline review comment on new-side lines start..end of `path`."""

    path: str
    start: int
    end: int
    body: str

    @classmethod
    def of(cls, listed: JsonMap) -> Comment:
        """A listed review comment (COMMENT_FIELDS), on its original lines."""
        path, body, end = listed.get("path"), listed.get("body"), listed.get("original_line")
        return cls(
            path=path if is_str(path) else "",
            start=as_int(listed.get("original_start_line") or end),
            end=as_int(end),
            body=body if is_str(body) else "",
        )


class Recorded(NamedTuple):
    """One review that a workflow posted: when it was submitted, GitHub's number for it, the commit
    GitHub files it under, its address, and its body. Records sort in that order, so two reviews
    submitted in one second sort by that number."""

    submitted: str
    number: int
    commit: str
    url: str
    body: str

    @classmethod
    def of(cls, review: JsonMap) -> Recorded | None:
        """The record of a review (REVIEW_FIELDS); None unless a workflow posted it and it has a
        number."""
        number = review.get("id")
        if not (_posted_by_a_workflow(review) and is_int(number)):
            return None
        return cls(
            submitted=clean(review.get("submitted_at")),
            number=number,
            commit=clean(review.get("commit_id")),
            url=plain_line(clean(review.get("html_url"))),
            body=body if is_str(body := review.get("body")) else "",
        )

    def has_a_line(self) -> bool:
        """Whether the opening of a verdict line stands anywhere in the body."""
        return VERDICT_OPENING in self.body

    def tokens(self, terms: Terms) -> list[str] | None:
        """The verdict's key=value tokens; None unless the whole last line is exactly
        VERDICT_LINE filled with those tokens and `terms`."""
        last_line = self.body.rstrip(" \t\n\f\r").rsplit("\n", 1)[-1]
        found = TOKENS_RE.search(last_line)
        if found is None:
            return None
        tokens = found[0].split()
        return tokens if last_line == terms.line(tokens) else None

    def comments_among(self, comments: Iterable[JsonMap]) -> list[Comment]:
        """Those review `comments` (COMMENT_FIELDS) that stand in this review."""
        return [Comment.of(one) for one in comments if one.get("review") == self.number]


def passes(tokens: Sequence[str]) -> bool:
    """Whether the `tokens` of a verdict line say that the check passes."""
    return f"{verdict.KEYS[0]}={verdict.PASS}" in tokens


def encoded(path: str) -> str:
    """A finding's repository path as its marker carries it: percent-encoded but for "/"."""
    return quote(path, safe="/", errors="surrogateescape")


def decoded(text: str) -> str | None:
    """The repository path a marker names; None unless it is spelt exactly as encoded() spells
    a path the review files a finding under: below the repository top level, nothing to fold."""
    path = unquote(text, errors="surrogateescape")
    spelt = encoded(path) == text and posixpath.normpath(path) == path
    return path if spelt and below_top(path) else None


class Marker(NamedTuple):
    """The marker a finding's lead comment ends with: the finding's id, its place, what the
    comment carried, and the grade that a later run counts, None where the marker names none."""

    key: str
    path: str
    line: int
    tag: Tag
    graded: verdict.Graded | None
    shared: bool = False

    def text(self) -> str:
        """The marker as the comment carries it, after a blank line."""
        place = LOCATION.format(encoded(self.path), self.line)
        graded = self.graded
        named = GRADE.format(graded.severity.name, graded.confidence.name) if graded else ""
        shared = SHARED if self.shared else ""
        return "\n\n" + MARKER.format(self.key + place + self.tag.value + named + shared)

    @classmethod
    def read(cls, body: str) -> Marker | None:
        """The marker a comment body ends with; None when it ends with none, or with one
        naming a place this module does not spell."""
        marked = TRAILER_RE.search(body)
        if not marked:
            return None
        key, named_path, named_line, tag, severity, confidence, shared = marked.groups()
        path = decoded(named_path)
        if path is None:
            return None
        graded = verdict.Graded(Severity[severity], Confidence[confidence]) if severity else None
        return cls(key, path, int(named_line), Tag(tag), graded, bool(shared))


class Lines(NamedTuple):
    """Where GitHub lists a comment on several lines at the head, and the lines it was made on, in
    caret form."""

    path: str
    start: int
    end: int
    made_on: tuple[str, ...]

    @classmethod
    def of(cls, listed: JsonMap) -> Lines | None:
        """The lines of a listed review comment (COMMENT_FIELDS); None for a comment on one line,
        an outdated one, one whose hunk GitHub gave in another form, or one whose path gh may have
        rewritten."""
        path, start, end, hunk = (
            listed.get(k) for k in ("path", "start_line", "line", "diff_hunk")
        )
        first, last = listed.get("original_start_line"), listed.get("original_line")
        if not (is_str(path) and is_int(start) and is_int(end) and is_str(hunk)):
            return None
        if "^" in path:
            return None
        if not (is_int(first) and is_int(last) and first < last):
            return None
        header, *body = _lines(hunk)
        opened = HUNK.match(header)
        new_side = [line[1:] for line in body if line[:1] in {" ", "+"}]
        count = last - first + 1
        if not opened or int(opened[3]) + len(new_side) - 1 != last or count > len(new_side):
            return None
        return cls(path, start, end, tuple(new_side[-count:]))

    def at(self, text: str) -> tuple[str, ...]:
        """The lines that the comment sits on now, in caret form. `text` is the file at the head."""
        return tuple(_lines(text)[self.start - 1 : self.end])


def _lines(text: str) -> list[str]:
    """`text`'s lines in caret form, split at each newline alone, each without a CR at its end."""
    return [line.removesuffix("\r") for line in in_carets(text).split("\n")]


class Anchor(NamedTuple):
    """Where a live comment puts the finding that its marker names."""

    gap: int
    line: int


class FindingLine(NamedTuple):
    """A line of the head where a finding with this id can be. Equal code has one id."""

    key: str
    line: int

    @classmethod
    def of(cls, record: JsonMap) -> FindingLine:
        """The id and the line that a finding's record, a probe's entry or a re-check's entry
        names; an empty id or line 0 where it names none."""
        return cls(clean(record.get(FINDING_ID)), as_int(record.get("line")))


# The line of facts in a finding's comment, up to its CWE entry (review.finding_markdown).
_FACTS = re.compile(r"^[A-Z][a-z]+ severity · .*?\[CWE-([0-9]{1,5})\]\(", re.MULTILINE)


class Prior(NamedTuple):
    """One finding that an earlier review comment marks: its id and place, and the comment."""

    key: str
    path: str
    line: int
    live: bool
    url: str
    headline: str
    tag: Tag
    review: int | None
    graded: verdict.Graded | None
    lines: Lines | None
    anchor: Anchor | None
    shared: bool = False
    broken: bool = False
    cwe: int | None = None

    @property
    def place(self) -> FindingLine:
        """Where the comment puts its finding now: on its anchor's line, or else its marker's."""
        return FindingLine(self.key, self.anchor.line if self.anchor else self.line)

    @classmethod
    def of(cls, comment: JsonMap) -> Prior | None:
        """The earlier finding a review comment (COMMENT_FIELDS) answers for; None unless a
        workflow posted it with a marker as this module writes one."""
        body, url = comment.get("body"), comment.get("html_url")
        if not (_posted_by_a_workflow(comment) and is_str(body) and is_str(url)):
            return None
        marker = Marker.read(body)
        if marker is None:
            return None
        made, now = Comment.of(comment), comment.get("line")
        first = comment.get("start_line") if made.start < made.end else now
        own = in_carets(made.path) == in_carets(marker.path) and 0 < made.start <= marker.line
        gap = marker.line - made.start
        anchor = Anchor(gap, first + gap) if own and is_int(now) and is_int(first) else None
        return cls(
            key=marker.key,
            path=marker.path,
            line=marker.line,
            live=is_int(now),
            url=url,
            headline=one_line(body.strip().splitlines()[0]),
            tag=marker.tag,
            review=review if is_int(review := comment.get("review")) else None,
            graded=marker.graded,
            lines=Lines.of(comment),
            anchor=anchor,
            shared=marker.shared,
            cwe=int(facts[1]) if (facts := _FACTS.search(body)) else None,
        )


def part_line(key: str | None) -> str:
    """The line that ends a later part of the fix of finding `key`, empty for no key."""
    return _PART.format(key) if key else ""


def with_broken_fixes(
    priors: Sequence[Prior], comments: Iterable[JsonMap], changed: Callable[[Lines], bool]
) -> list[Prior]:
    """`priors`, each with `broken` set where the listed `comments` (COMMENT_FIELDS) hold a later
    part of its fix, in the same review, that is outdated or whose lines have `changed`."""
    held = {prior.review for prior in priors}
    broken = {
        (review, part[1])
        for one in comments
        if (review := as_int(one.get("review"))) in held
        if (part := _PART_RE.search(Comment.of(one).body))
        if not is_int(one.get("line")) or ((lines := Lines.of(one)) and changed(lines))
    }
    return [prior._replace(broken=(prior.review, prior.key) in broken) for prior in priors]


def newest_graded(priors: Iterable[Prior]) -> dict[str, Prior]:
    """By finding id, the newest live comment whose marker names a grade. `priors` come in GitHub's
    order, oldest first."""
    return {prior.key: prior for prior in priors if prior.live and prior.graded}


def shared_keys(priors: Iterable[Prior]) -> set[str]:
    """The finding ids that a live comment among `priors` says are shared."""
    return {prior.key for prior in priors if prior.live and prior.shared}


def newest_by_place(priors: Iterable[Prior]) -> dict[FindingLine, Prior]:
    """newest_graded(), by place. `priors` come oldest first."""
    return {prior.place: prior for prior in priors if prior.live and prior.graded}


class Earlier(NamedTuple):
    """The comments of earlier reviews on findings, oldest first, as the head commit shows them:
    those in a review with its receipt are `believed`, and the others `doubted`."""

    believed: list[Prior]
    doubted: list[Prior]
    holding: Mapping[str, Sequence[int]]

    def is_sure(self, prior: Prior) -> bool:
        """Whether the comment is live, and a finding with its id is, or was, at its place."""
        reach = len(prior.lines.made_on) if prior.lines else 1
        on_it = prior.anchor is not None and prior.anchor.gap < reach
        return prior.live and (on_it or prior.place.line in self.holding.get(prior.key, ()))

    def at_sure_places(self) -> dict[FindingLine, Prior]:
        """By place that a believed comment makes sure, the newest live graded one there."""
        sure = {one.place for one in self.believed if self.is_sure(one)}
        return {at: one for at, one in newest_by_place(self.believed).items() if at in sure}

    def _answers_at(self, prior: Prior) -> FindingLine:
        """The line with the comment's id's code, where the head has just one; else its place."""
        held = self.holding.get(prior.key, ())
        return FindingLine(prior.key, held[0]) if len(held) == 1 else prior.place

    def answering(self) -> dict[FindingLine, Prior]:
        """By the place that _answers_at() gives, the newest live graded comment there, where it
        has the grade of its id's newest: it alone can answer for a finding at that place. A shared
        id has no entry, nor has a place whose newest comment is `broken`."""
        shared = shared_keys(self.believed)
        live = [one for one in self.believed if one.live and one.graded and one.key not in shared]
        last = newest_graded(live)
        newest = {self._answers_at(one): one for one in live}
        return {
            at: one
            for at, one in newest.items()
            if one.graded == last[one.key].graded and not one.broken
        }


def grade_named(fields: JsonMap) -> verdict.Graded | None:
    """The grade that `fields` name by "severity" and "confidence", as a finding record spells
    them; None where either is not such a name."""
    severity, confidence = fields.get("severity"), fields.get("confidence")
    if not (is_str(severity) and severity in Severity.__members__):
        return None
    if not (is_str(confidence) and confidence in Confidence.__members__):
        return None
    return verdict.Graded(Severity[severity], Confidence[confidence])


def still_answers(
    carried: Tag | None, named: verdict.Graded | None, wanted: Tag, graded: verdict.Graded
) -> bool:
    """Whether an earlier comment still answers for a finding that this run grades `graded`: the
    comment that Earlier.answering() gives for its place carried at least `wanted` (`carried`, None
    where it gives none) and names `graded` (`named`)."""
    return carried is not None and carried.rank >= wanted.rank and named == graded


def fullest_by_key(priors: Iterable[Prior]) -> dict[str, Prior]:
    """By finding id, the comment that carried the most; on a tie, the first. The ids keep
    the order in which they were first met."""
    found: dict[str, Prior] = {}
    for prior in priors:
        if prior.key not in found or prior.tag.rank > found[prior.key].tag.rank:
            found[prior.key] = prior
    return found
