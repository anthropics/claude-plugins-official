#!/usr/bin/env python3
"""Write the results of an attack surface analysis in the same formats as a scan's results.

`start` makes the analysis's output directory in the current directory, and records what is
analyzed. `check` compares the checkout with what `start` recorded. `write` turns the records that
the stages left there into CLAUDE-SECURITY-RESULTS.md, .jsonl and .sarif, and the
CLAUDE-SECURITY-REVISION-<tag>.json stamp. It can also write attack-surface-patches/, with its
index. It changes nothing under a stage's directory. It prints the facts that the session reports
to the user.

Usage:
  attack_surface_report.py start [--stage <1|2|3>]...
  attack_surface_report.py check <output_dir>
  attack_surface_report.py write <output_dir> [--same <id>,<id>[,...]]...

<output_dir> must lie in the current directory. --same names findings that are one flaw. If a
finding's record cannot be read or used, the finding is left out. The report lists it with what is
wrong, and the whole report is marked unverified.
`write` builds its files in a scratch folder, and moves them to their names once all are written.

Exits 0 when done, and 2 on a usage error. Exits 1 on a refusal, which says on stderr what is wrong,
or when a file cannot be read or written. A refusal changes nothing, with two exceptions: `check`
adds to the list of what it found, and `write` removes a scratch folder that a killed write left.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import itertools
import os
import re
import shlex
import sys
import textwrap
import time
import uuid
from collections import Counter, defaultdict
from contextlib import suppress
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, NoReturn, TypedDict

# -P and PYTHONSAFEPATH leave this script's folder, which holds lib/, off sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, cwe, git, plugin, sarif, secret, strictjson
from lib.display import counted
from lib.duration import elapsed_seconds
from lib.exhaustiveness import unreachable
from lib.finding import FindingError, Severity, strength, unrecognized_cwes
from lib.link import is_link
from lib.markdown import at_most, code_span, one_line, printable, span, unbroken, under_a_heading
from lib.place import in_git_directory
from lib.removal import remove_tree
from lib.revision import SELF_REPORTED, RevisionError, checked_out, revision_tag
from lib.strictjson import is_list, is_map, is_str
from lib.surface import (
    AnalysisError,
    Entry,
    LeftOut,
    Outcome,
    Rated,
    built,
    fault,
    gathered,
    records_in,
    refuse,
    refuses_its_gate,
)
from lib.surface_dir import (
    OUTPUT_FORM,
    OUTPUT_RE,
    WORK_DIR_NAME,
    Stage,
    in_current_directory,
    output_name,
)
from lib.surface_patch import (
    AFTER_APPLY,
    COPY_FIRST,
    LEFT_HALFWAY,
    NOT_READ,
    SUITE_NAME,
    WAY_BACK,
    Clash,
    Held,
    Patch,
    Suite,
    Tried,
    claims_of,
    clashes_of,
    in_place,
    not_committed,
    patch_of,
    patches_in,
    paths_of,
    suite_of,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from lib.finding import Finding, Record
    from lib.revision import Revision

MODE: Final = "attack-surface"
COVERAGE_NAME: Final = plugin.COVERAGE_MD_NAME
COVERAGE_HEADING: Final = "Coverage"
NOT_CONFIRMED_HEADING: Final = "Not confirmed"
ALSO_LABEL: Final = "Also reached at"
LISTED_NEEDS_OPENING: Final = (
    f'Below are the preconditions of each finding under "{ALSO_LABEL}", unless they are the same '
    "as this finding's. A flaw can affect you if the preconditions of any one finding fit you."
)
LISTED_FIXES_OPENING: Final = (
    f'Below is the fix of each finding under "{ALSO_LABEL}" that gives one, unless it is the same '
    "as this finding's. Read each one: one finding's fix can name a step that another's lacks."
)
NOTHING_NEEDED: Final = "none needed"
LISTED_NOT_PRINTED: Final = (
    f'This section does not give the preconditions of the findings under "{ALSO_LABEL}", or the '
    "text of their fixes. For both, see each finding's record, in the `findings/` folder of its "
    "stage."
)
QUESTION_LABEL: Final = "Open question"
CHAIN_LABEL: Final = "Attack chain, not independently checked"
REPORT_NAME: Final = "report.md"
# How many characters of a report has_report() and message_of() read.
REPORT_HEAD: Final = 1 << 16
# The stage agent's own file under agents/ gives it this line, word for word.
COMPLETED: Final = "This stage completed, and had no finding to send to the independent check."
SUITE_STAGE: Final = Stage.ONE
SUITE_PLACE: Final = f"{SUITE_STAGE.folder}/{SUITE_NAME}"
PATCHES: Final = plugin.ANALYSIS_PATCHES_DIR_NAME
INDEX: Final = f"{PATCHES}/{plugin.PATCHES_INDEX_NAME}"
APPLY: Final = "git apply --verbose"
SCRATCH: Final = ".unfinished-results"
GIT_FAILED: Final = "git did not run, failed on the checkout, or took too long"
CHECKOUT_CHANGED: Final = "the checkout changed while the analysis ran"
STATUS_SECONDS: Final = 90
TRIAL_SECONDS: Final = 100
CHANGES_NAME: Final = "checkout-changes.txt"
CHANGE_LIST_LOST: Final = (
    f"what a check wrote down is lost: {CHANGES_NAME} was empty, was a link, was no file, or could "
    "not be read"
)


SEE_GIT: Final = "Run git status to see what git says."
ASK_GIT: Final = f"{SEE_GIT} Then ask for a new analysis."
NEW_ANALYSIS: Final = "Ask for a new analysis, and leave the project's files alone while it runs."
RUN_AGAIN: Final = (
    "Want me to run the analysis again? Please leave the project's files alone while it runs."
)
MAY_NOT_FIT: Final = (
    "the results may no longer fit your code. A clean git status does not show that they fit: a "
    "change made while the analysis ran may now be committed or undone."
)
NOT_COUNTED_LISTED: Final = (
    f'report\'s "{NOT_CONFIRMED_HEADING}" section lists what is not counted as a finding, and '
    "says why."
)
NOT_COUNTED_STEP: Final = f"This {NOT_COUNTED_LISTED}"
NOT_COUNTED_SAID: Final = f"The {NOT_COUNTED_LISTED}"
NOT_SHOWN: Final = (
    "The status does not show how much of your code the stages examined: the report's "
    f'"{COVERAGE_HEADING}" section gives an account of that.'
)


class Texts(NamedTuple):
    """What the user is told of a reason. `means` is what it means for the results, and opens in
    lower case. `step` is what to do, or where to read, as the report says it. `said` ends the
    closing message. An offer to go through the open questions can follow it."""

    means: str
    step: str
    said: str


class Reason(Enum):
    """Why an analysis is unverified, in the order in which the report gives the reasons. Each
    member has its `reason_kind` word, whether it is about the checkout, and its texts. The stamp
    carries the word of the first reason that applies."""

    GIT_FAILED = (
        "git-failed",
        True,
        Texts(
            means=MAY_NOT_FIT,
            step=ASK_GIT,
            said=f"{SEE_GIT} Once git works here, I can run the analysis again: just ask.",
        ),
    )
    CHANGE_LIST_LOST = (
        "change-list-lost",
        True,
        Texts(
            means=MAY_NOT_FIT,
            step=NEW_ANALYSIS,
            said=RUN_AGAIN,
        ),
    )
    CHECKOUT_CHANGED = (
        "checkout-changed",
        True,
        Texts(
            means=MAY_NOT_FIT,
            step=NEW_ANALYSIS,
            said=RUN_AGAIN,
        ),
    )
    NO_STAGE_REPORT = (
        "no-stage-report",
        False,
        Texts(
            means="not every stage of the analysis gave a report, so findings may be missing.",
            step="Ask for an analysis of each stage that gave no report.",
            said="Want me to run what is missing on its own? Just ask.",
        ),
    )
    RECORDS_UNUSABLE = (
        "records-unusable",
        False,
        Texts(
            means="a record that could not be used may describe a serious finding.",
            step=NOT_COUNTED_STEP,
            said=NOT_COUNTED_SAID,
        ),
    )
    FINDINGS_UNRESOLVED = (
        "findings-unresolved",
        False,
        Texts(
            means="what the check did not settle may still be real.",
            step=NOT_COUNTED_STEP,
            said=NOT_COUNTED_SAID,
        ),
    )
    STAGE_NOT_CHECKED = (
        "stage-not-checked",
        False,
        Texts(
            means=(
                "a stage that sent the check nothing may have had nothing to report, may have "
                "skipped it, or may not have completed."
            ),
            step=(
                f"To see whether a stage skipped the independent check, read the {REPORT_NAME} in "
                "the folder of each stage that sent it nothing."
            ),
            said=(
                "Want me to read the report of each stage that sent nothing, and tell you whether "
                "it ran its check? Just ask."
            ),
        ),
    )

    def __init__(self, word: str, of_checkout: bool, texts: Texts) -> None:
        self.word = word
        self.of_checkout = of_checkout
        self.texts = texts


MARKS: Final = (GIT_FAILED, CHANGE_LIST_LOST)
STAMP_ONLY: Final = frozenset({"plugin_version", "reason_kind"})
CHANGES_PRINTED: Final = 20
CHANGES_IN_REASON: Final = 3
LEFT_OUT_IN_REASON: Final = 3
FOLDERS_NAMED: Final = 20
FINDINGS_LISTED: Final = 10
TEXT_SHOWN: Final = 500


class Kind(Enum):
    """A kind of change to the checkout. Its value starts the change's line."""

    HEAD_MOVED = "HEAD moved to"
    ADDED = "+"
    GONE = "-"


class Change(NamedTuple):
    """One difference between the checkout and what `start` recorded."""

    kind: Kind
    what: str

    @property
    def line(self) -> str:
        """The change on one line. A name in it that is not UTF-8 is written as escapes."""
        return utf8(f"{self.kind.value} {self.what}").decode()


SIGNS: Final = {
    Kind.ADDED: f"Each {Kind.ADDED.value} line is new in git status since the start.",
    Kind.GONE: f"Each {Kind.GONE.value} line was there at the start, and is gone now.",
}
READ_ONLY: Final = "The agents were told to read your code, and to build and run none of it."


PATCHES_APART: Final = "Patches that may clash, or could not be tried together"
NOT_REDACTED: Final = (
    "Nothing named here has been redacted, so it may still hold credential values. This command "
    "can be run again once the user has deleted everything named here."
)
STAGE_ENDED: Final = "Stage {} ({}) has ended. Confirmed findings come with the final results."
FLAGGED_HEADING: Final = "What this stage flagged, and what it asks you:"
TO_LIST: Final = (
    f'these exact words: "{FLAGGED_HEADING}", and under it each item '
    "that the report flags, under any heading, and each that it calls unproven or unresolved, with "
    'its id, and the report\'s questions, or "nothing". Say which items no independent check '
    "confirmed. Do not say that nothing is unproven. Keep any chain that the report states between "
    "items. List a confirmed finding only if the report also flags it. Say that no answer is due "
    "now. Leave out severities: the results may show lower ones. Do not end your turn to wait for "
    "answers to them."
)
TO_RELAY: Final = (
    "if the stage that just ended gave a report, write to the user now, before any other call, "
    f'these exact words: "{STAGE_ENDED.format("<its number>", "<its name>")}", then {TO_LIST}'
)
RELAY_MARK: Final = "relay:"
RELAY: Final = f"{RELAY_MARK} {TO_RELAY}"
MESSAGE_MARKS: Final = ("<!-- message -->", "<!-- end message -->")
MESSAGE_WORDS: Final = 200
MESSAGE_EDGE: Final = "---"
QUESTIONS_HEADING: Final = "Questions:"
RELAY_THE_TEXT: Final = (
    f"{RELAY_MARK} write the text between the two lines of {MESSAGE_EDGE} above to the user now, "
    "word for word, before any other call. That text is your whole message, with no word on your "
    "next step. Do not end your turn after it."
)
SEVERITY_WORD: Final = re.compile(rf"\b(?:{'|'.join(Severity.__members__)})\b")
NOTHING_UNPROVEN: Final = re.compile(
    r"\b(?:nothing|none(?!\s+of\s+(?:the|these|those)\s+unproven\b))\b[^.\n]{0,40}\bunproven\b"
    r"|\b(?:no|zero)\s+(?:(?:items?|findings?|candidates?|flagged|open|unresolved|or|and|is|are"
    r"|was|were|stays?|remains?|left)\s+){0,4}unproven\b"
    r"|\bunproven\b[^.\n]{0,40}\s(?:nothing|none|0)\b(?:[.*]*\s*$|[.*]+\s)",
    re.IGNORECASE | re.MULTILINE,
)
ORDER_LINE: Final = re.compile(
    rf"\s*(?:{MESSAGE_EDGE}\s*$|{RELAY_MARK}|handoff for stage|write:|next:)"
)
SETTLED: Final = frozenset({Outcome.CONFIRMED, Outcome.REFUTED})
RELAY_AFTER_A_REFUSAL: Final = (
    f"{RELAY_MARK} write to the user now, before any other call: first what the script printed "
    "above this line, and that no further stage runs, then, if the stage that just ended gave a "
    f"report, {TO_LIST} Then do steps 5 and 6 of pipeline.md to their end."
)
NOT_IN_GIT: Final = "tell the user that the project was not in git when the analysis started"
RELAY_OUTSIDE_GIT: Final = (
    f"{RELAY_MARK} first {NOT_IN_GIT}, so its files were not compared with the start. Then, "
    f"{TO_RELAY}"
)
NEXT: Final = (
    "next: no stage is left to run. Once you have done what the last line asks, do steps 5 and 6 "
    "of pipeline.md to their end: write coverage.md, run the write: command, with one --same for "
    "each group of findings that are one flaw, start the redactor, and close."
)


class Meta(TypedDict):
    """analysis.json, as `start` writes it."""

    scan_id: str
    started_at: str
    revision: Revision
    git_status: str
    stages: list[str]


class Analysis(NamedTuple):
    """What `start` recorded. `started_at` is None if the file has no such text. `git_status` is
    what git status printed: empty if there is no git."""

    id: uuid.UUID
    started_at: str | None
    revision: Revision
    git_status: str
    stages: list[Stage]

    @property
    def tag(self) -> str:
        """The revision's name, as in the stamp's file name."""
        return revision_tag(self.revision)

    @property
    def unseen_sentence(self) -> str:
        """The sentence that says what the comparison with the start of the analysis cannot see."""
        label = "Not compared with the start of the analysis"
        if not self.revision.get("versioned"):
            return f"{label}: the target's files, since the target was not in git at the start."
        skipped = (
            "files that git ignores or was told not to check (skip-worktree, assume-unchanged)"
        )
        further = ", and further changes to files that were already changed at the start"
        return f"{label}: {skipped}{further if self.git_status else ''}."

    @property
    def sparse_sentence(self) -> str:
        """The sentence on a checkout that was sparse at the start. Empty if it was not sparse."""
        if not self.revision.get("sparse"):
            return ""
        sparse = (
            "The checkout was sparse at the start of the analysis, so the files that it left out "
            "were not on disk for the stages to read."
        )
        label = "Top-level folders of the commit that were not on disk"
        folders = self.revision.get("not_checked_out_dirs", [])
        absent = at_most(FOLDERS_NAMED, list(map(span, folders)))
        return f"{sparse} {label}: {absent}." if absent else sparse


class Results(NamedTuple):
    """The checked results of an analysis. Every product is written from them."""

    out: Path
    analysis: Analysis
    saved: list[Stage]
    on_own_word: list[Stage]
    coverage: str
    entries: list[Entry | LeftOut]
    confirmed: dict[str, Rated]
    under: dict[str, str]
    scan: sarif.Scan
    records: list[Record]
    unknown_cwes: list[str]
    patches: list[Patch]
    unread: dict[str, str]
    clashes: list[Clash]
    suite: Suite | None
    leftovers: list[str]
    reasons: dict[Reason, str]
    generated: datetime

    @property
    def tally(self) -> Counter[Outcome]:
        return Counter(entry.outcome for entry in self.entries)

    def asked_with(self, name: str) -> list[str]:
        """The findings with an open question in the report's section that shows `name`."""
        return [
            each
            for each, head in self.under.items()
            if head == self.under[name] and self.confirmed[each].entry.question
        ]

    @property
    def status(self) -> str:
        return plugin.UNVERIFIED if self.reasons else plugin.VERIFIED

    @property
    def reason(self) -> str | None:
        """Why the report reads unverified. It names the first few records that were left out."""
        lost = [
            code_span(utf8(name_of(entry)).decode())
            for entry in self.entries
            if entry.outcome is Outcome.LEFT_OUT
        ]
        names = {Reason.RECORDS_UNUSABLE: f": {at_most(LEFT_OUT_IN_REASON, lost)}"}
        return "; ".join(text + names.get(why, "") for why, text in self.reasons.items()) or None

    @property
    def reason_unnamed(self) -> str | None:
        """`reason`, with the records that were left out counted and not named."""
        return "; ".join(self.reasons.values()) or None

    @property
    def status_sentence(self) -> str:
        reason = f" ({self.reason})" if self.reason else ""
        return f"Status of the findings: {self.status}{reason}."

    @property
    def own_word_sentences(self) -> str:
        """The sentences on the stages in `on_own_word`, or "" if there are none."""
        if not self.on_own_word:
            return ""
        stages = series(f"stage {stage.number}" for stage in self.on_own_word)
        says = "It says that it" if len(self.on_own_word) == 1 else "They say that they"
        return (
            f"{capitalized(stages)} sent no finding to the independent check. {says} completed "
            "with none to send; nothing checks that, and the status of the findings takes it as "
            "true."
        )

    @property
    def meanings(self) -> list[str]:
        """What the reasons mean for the results, none twice."""
        told = list(dict.fromkeys(reason.texts.means for reason in self.reasons))
        if told and self.records:
            told[0] = (
                "By the analysis's own account, an independent check still confirmed each finding, "
                f"but {told[0]}"
            )
        return [capitalized(each) for each in told]

    @property
    def reasons_told(self) -> list[Reason]:
        """The reasons whose `step` the report gives. The closing message has the first one's
        `said`."""
        lead = [reason for reason in self.reasons if reason.of_checkout][:1]
        covered = [Reason.NO_STAGE_REPORT] if lead else []
        return [*lead, *(r for r in self.reasons if not r.of_checkout and r not in covered)]

    @property
    def ready(self) -> int:
        """How many patches are ready to apply."""
        return sum(patch.ready for patch in self.patches)

    @property
    def set_aside(self) -> int:
        """How many patches are set aside: each one that is not ready, and each file that could not
        be read, the regression suite too."""
        return len(self.patches) + len(self.unread) - self.ready

    @property
    def clashing(self) -> set[str]:
        """Each patch that PATCHES.md names with another one, as Patch.shown() gives it."""
        return {name for clash in self.clashes for name in clash.names}

    def cautions(self, patch: Patch) -> bool:
        """Whether the patch is ready, and PATCHES.md names it with another patch (a clash, or a
        stage 1 gate's others()) or marks it for an open question."""
        return patch.ready and (
            patch.shown(self.out) in self.clashing
            or any(map(self.asked_with, patch.ids))
            or any(self.others(patch, name) for name in patch.ids)
        )

    @property
    def cautioned(self) -> list[Patch]:
        return list(filter(self.cautions, self.patches))

    def others(self, patch: Patch, name: str) -> list[Patch]:
        """For a ready stage 1 patch, the other copied stage 1 patches for one finding."""
        if not patch.ready or patch.stage is not Stage.ONE:
            return []
        return [each for each in self.patches if each is not patch and name in each.ids]

    @property
    def asking(self) -> int:
        """How many records hold an open question."""
        return asking_in(self.entries)

    @property
    def duration_s(self) -> int | None:
        """Whole seconds from `start` to `write`. None if the start time cannot be read."""
        return elapsed_seconds(self.analysis.started_at, self.generated)

    @property
    def indexed(self) -> bool:
        """Whether PATCHES.md is written. Findings with no patch are not enough for it."""
        return bool(self.patches or self.unread or self.suite)

    @property
    def has_patch_files(self) -> bool:
        """Whether attack-surface-patches/ holds a patch or the regression suite."""
        return bool(self.suite or any(patch.copied for patch in self.patches))

    def suite_sentence(self, index: str) -> str:
        """A caution where the regression suite was not read or is not ready to apply, or "" where
        it is ready or there is none. `index` is how the sentence names PATCHES.md."""
        missed = SUITE_PLACE in self.unread
        told = missed or (self.suite and self.suite.applies is not Tried.APPLIES)
        return f"The regression suite is not ready to apply: {index} says why." if told else ""

    @property
    def grades(self) -> Counter[str]:
        return graded(self.records)

    @property
    def headline(self) -> str:
        """How many findings the report shows, by severity. Then how many records could not be used,
        and how many findings the independent check did not settle."""
        apart = {
            "whose record could not be used": self.tally[Outcome.LEFT_OUT],
            "that the independent check did not settle": self.tally[Outcome.UNRESOLVED],
        }
        rest = "".join(f", plus {number} {what}" for what, number in apart.items() if number)
        if split := by_severity(self.records):
            return f"{counted(len(self.records), 'finding')}: {split}{rest}"
        return f"no confirmed findings{rest}"


def capitalized(sentence: str) -> str:
    return sentence[:1].upper() + sentence[1:]


def with_questions(entries: Iterable[Entry | LeftOut]) -> list[Entry]:
    """The records that hold an open question. Records can share one."""
    return [e for e in entries if e.outcome is not Outcome.LEFT_OUT and e.question]


def asking_in(entries: Iterable[Entry | LeftOut]) -> int:
    """How many of the records hold an open question."""
    return len(with_questions(entries))


def graded(records: Iterable[Record]) -> Counter[str]:
    """How many of the findings have each severity."""
    return Counter(found["severity"] for found in records)


def by_severity(records: Iterable[Record]) -> str:
    """How many of the findings have each severity, gravest first, as in "7 MEDIUM, 16 LOW"."""
    grades = graded(records)
    return ", ".join(f"{grades[grade]} {grade}" for grade in Severity.__members__ if grades[grade])


def cut(text: str) -> str:
    """`text`, or its first TEXT_SHOWN characters with a mark behind them."""
    return text if len(text) <= TEXT_SHOWN else f"{text[:TEXT_SHOWN]} ..."


def series(items: Iterable[str]) -> str:
    """The items as a list inside a sentence: "a", "a and b", or "a, b and c"."""
    listed = list(items)
    return f"{', '.join(listed[:-1])} and {listed[-1]}" if len(listed) > 1 else "".join(listed)


def noted(*notes: str) -> str:
    """The notes that are not empty, in one pair of parentheses."""
    said = "; ".join(filter(None, notes))
    return f" ({said})" if said else ""


def utf8(text: str) -> bytes:
    """A product's bytes, in UTF-8. What UTF-8 cannot encode is written as escapes."""
    return text.encode("utf-8", "backslashreplace")


def json_file(value: object) -> bytes:
    return utf8(strictjson.text(value, indent=2) + "\n")


def has_no_commit(root: str) -> bool:
    """Whether git answers that HEAD's branch has no commit yet. False if git gave no answer."""
    branch = git.run(root, "symbolic-ref", "--quiet", "HEAD")
    refs = None if branch is None else git.run(root, "for-each-ref", "--format=%(refname)", branch)
    return refs is not None and branch not in refs.split("\n")


def observed(root: str) -> tuple[Revision, str] | None:
    """The checkout's revision, and the text that git status printed. The revision is unversioned if
    git finds no work tree here and no folder from here up holds a .git. None if git found no work
    tree although a .git lies here or above, or gave no usable answer on the work tree that it
    found."""
    if git.run(root, "rev-parse", "--is-inside-work-tree") != "true":
        return None if git.holder_of(root) else ({"versioned": False}, "")
    revision, status = checked_out(root, timeout=STATUS_SECONDS)
    commit = revision.get("commit")
    failed = not (has_no_commit(root) if commit is None else plugin.SHA_RE.match(commit))
    return None if status is None or failed else (revision, status)


def sparse_keys(root: str) -> Revision:
    """A revision's two keys for a sparse checkout, as in a scan: that it is sparse, and the
    commit's top-level folders that are not on disk. Empty if `root` is not sparse."""
    if git.run(root, "config", "--bool", "core.sparseCheckout") != "true":
        return {}
    tops = git.run(root, "ls-tree", "-d", "-z", "--name-only", "HEAD") or ""
    there = (top for top in tops.split("\0") if top)
    absent = [top for top in there if not os.path.lexists(Path(root, git.for_disk(top)))]
    return {"sparse": True, "not_checked_out_dirs": absent}


RENAME: Final = "tell the user to rename that folder"


def refuse_unprintable(place: str, path: str, encoding: str) -> None:
    """Refuse a `path` whose bytes, read as UTF-8, split into lines or are not valid, or which
    `encoding` cannot write. `place` says, in the refusal, whose path it is."""
    read = console.read_as_utf8(path, encoding)
    if read.splitlines() != [read]:
        refuse(
            f"the name of {place} or of a folder above it holds a line break or a control "
            f"character: {RENAME}"
        )
    try:
        path.encode(encoding).decode("utf-8")
    except UnicodeError as error:
        invalid = "utf-8" if isinstance(error, UnicodeDecodeError) else encoding
        refuse(
            f"the name of {place} or of a folder above it holds a byte that is not valid "
            f"{invalid}: {RENAME}. The path is {printable(read)}"
        )


def admitted(target: str) -> tuple[Revision, str]:
    """What observed() gives for `target`. Refuses a folder where no analysis may start."""
    refuse_unprintable("this folder", target, console.paths_encoding())
    try:
        home = Path(os.path.realpath(Path.home()))
    except (RuntimeError, KeyError):
        refuse(
            "your home folder cannot be found, so it cannot be told whether this is it or a folder "
            "above it: set HOME, or USERPROFILE on Windows"
        )
    if home.is_relative_to(target):
        refuse("this is your home folder or a folder above it: open Claude Code in the project")
    if in_git_directory(target):
        refuse(
            "this folder is, or lies inside, a repository's git directory, such as .git or a bare "
            "repository: open Claude Code in a checkout of that repository"
        )
    top, at_the_top = git.toplevel(target), False
    if top is not None:
        refuse_unprintable("the repository's root", top, "utf-8")
        at_the_top = git.is_top(target, top)
        top = git.for_disk(top)
    if top is not None and home.is_relative_to(os.path.realpath(top)):
        refuse(
            f"this folder is part of the repository at {top}, which holds your home folder: give "
            "the project a repository of its own (git init)"
        )
    if top is not None and not at_the_top:
        refuse(f"open Claude Code at the repository's root, {top}: an analysis starts there")
    here = Path(os.path.realpath(target))
    if top is None and (holder := git.holder_of(target)) not in {None, here}:
        refuse(
            f"{holder} holds a .git, but git reads no repository in {target}. Run git status in "
            f"{holder} to see what git says. An analysis starts at a repository's root, once git "
            f"can read it. If {target} is part of no repository, run git init in it."
        )
    seen = observed(target)
    if seen is None:
        refuse(f"{GIT_FAILED}, so the checkout's revision cannot be read. {SEE_GIT}")
    return seen


def spelled(called: str) -> str:
    """This script's path as the printed commands spell it. `called` is as for start()."""
    return called if os.path.isabs(called) else os.path.abspath(called)


def to_write(out: Path, here: str) -> str:
    """The `write:` line that `start` and `check` print. `here` is what spelled() gives."""
    return f'write: python3 "{here}" write {shlex.quote(str(out))}'


def commands(out: Path, stages: Sequence[Stage], called: str) -> list[str]:
    """The commands for the later steps, as `start` prints them. `called` is as for start()."""
    here = spelled(called)
    # Not Path.with_name(): the printed commands must keep this path's spelling.
    remover = here.removesuffix(Path(here).name) + "remove_work_dir.py"
    return [
        f'check: python3 "{here}" check {shlex.quote(str(out))}',
        to_write(out, here),
        *(
            f'remove: python3 "{remover}" {shlex.quote(str(out / stage.folder / WORK_DIR_NAME))}'
            for stage in stages
        ),
    ]


def start(numbers: Sequence[int], called: str) -> list[str]:
    """Make the output directory in the current directory, ignored by git. Record in it the
    target's revision and the stages asked for (all three by default). On an error, remove the
    directory, or name it on stderr if it stays. `called` is this script's path as the caller
    spelled it."""
    target = str(Path.cwd())
    revision, status = admitted(target)
    refuse_unprintable("the plugin's folder", called, console.paths_encoding())
    if revision.get("versioned"):
        revision.update(sparse_keys(target))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    out = Path(target, output_name(now))
    try:
        out.mkdir()
    except FileExistsError:
        refuse(f"{out.name} already exists: another scan or analysis started in the same second")
    stages = [stage for stage in Stage if stage.number in numbers or not numbers]
    meta: Meta = {
        "scan_id": str(uuid.uuid4()),
        "started_at": now.isoformat(),
        "revision": revision,
        "git_status": status,
        "stages": [stage.folder for stage in stages],
    }
    try:
        for stage in stages:
            (out / stage.folder).mkdir()
        (out / ".gitignore").write_bytes(b"*\n")
        (out / plugin.ANALYSIS_META_NAME).write_bytes(json_file(meta))
    except OSError:
        with suppress(OSError):
            remove_tree(out)
        if os.path.lexists(out):
            sys.stderr.write(
                f"attack_surface_report.py: this start did not finish. Left behind: {out.name}. It "
                "holds no results. Delete it.\n"
            )
        raise
    return [
        f"output directory: {out}",
        *(f"stage directory: {out / stage.folder}" for stage in stages),
        f"pin: {revision_tag(revision)}",
        *commands(out, stages, called),
    ]


def refuse_unread(out: Path) -> NoReturn:
    """Refuse a directory whose analysis.json is gone, is no file, or cannot be examined."""
    try:
        os.lstat(out / plugin.ANALYSIS_META_NAME)
    except FileNotFoundError:
        pass
    except OSError as error:
        refuse(
            f"{out.name}/{plugin.ANALYSIS_META_NAME} cannot be examined: {error.strerror}. This "
            "command can be run again once the user has access to the folder."
        )
    refuse(
        f"{out.name} holds no {plugin.ANALYSIS_META_NAME} that can be read, so 'check' and "
        "'write' cannot use it. A scan's report directory has a name of the same form, but holds "
        f"no {plugin.ANALYSIS_META_NAME}: name the directory that 'start' made. If 'start' made "
        f"this one, its {plugin.ANALYSIS_META_NAME} is gone or cannot be read: ask for a new "
        "analysis."
    )


def output_directory(given: str) -> Path:
    """The output directory named on the command line. A path that refuse_unprintable() refuses, is
    not in the current directory, is not named as `start` names one, or does not hold what `start`
    recorded, is refused."""
    # abspath folds ".." without following links, so the link check below sees this path's own name.
    out = Path(os.path.abspath(given))
    refuse_unprintable("the output directory", str(out), console.paths_encoding())
    if is_link(out):
        refuse(f"{given} is a link, and not the directory that 'start' made")
    if not (OUTPUT_RE.match(out.name) and out.is_dir()):
        refuse(f"not a {OUTPUT_FORM} directory: {given}")
    if not in_current_directory(out):
        refuse(f"{out.name} is not in the current directory: run this from {out.parent}")
    if not plugin.holds_analysis(out):
        refuse_unread(out)
    return out


def narrowed(revision: object) -> Revision | None:
    """A revision in one of the three forms that `start` writes. None for anything else."""
    if not is_map(revision):
        return None
    if set(revision) == {"versioned"} and revision["versioned"] is False:
        return {"versioned": False}
    plain = {"versioned", "commit", "branch", "dirty"}
    if set(revision) not in (plain, plain | {"sparse", "not_checked_out_dirs"}):
        return None
    commit, branch, dirty = revision["commit"], revision["branch"], revision["dirty"]
    if revision["versioned"] is not True or not isinstance(dirty, bool):
        return None
    if not (commit is None or is_str(commit)) or not (branch is None or is_str(branch)):
        return None
    checked: Revision = {"versioned": True, "commit": commit, "branch": branch, "dirty": dirty}
    if set(revision) == plain:
        return checked
    absent = revision["not_checked_out_dirs"]
    if revision["sparse"] is not True or not is_list(absent) or not all(map(is_str, absent)):
        return None
    return {**checked, "sparse": True, "not_checked_out_dirs": list(filter(is_str, absent))}


def recorded(out: Path) -> Analysis:
    """What `start` left in the output directory."""
    broken = (
        f"{plugin.ANALYSIS_META_NAME} is not the file that 'start' wrote: ask for a new analysis"
    )
    try:
        meta = strictjson.load(out / plugin.ANALYSIS_META_NAME)
    except OSError as error:
        if not plugin.holds_analysis(out):
            refuse_unread(out)
        refuse(
            f"{out.name}/{plugin.ANALYSIS_META_NAME} cannot be read: {error.strerror}. This "
            "command can be run again once the user has made the file readable."
        )
    except ValueError:
        refuse(broken)
    if not is_map(meta):
        refuse(broken)
    text, status, raw_stages = meta.get("scan_id"), meta.get("git_status"), meta.get("stages")
    revision = narrowed(meta.get("revision"))
    folders = raw_stages if is_list(raw_stages) else []
    stages = [stage for stage in Stage if stage.folder in folders]
    if not (revision and stages and is_str(status) and is_str(text)) or len(stages) != len(folders):
        refuse(broken)
    try:
        scan_id = uuid.UUID(text)
        revision_tag(revision)
    except (ValueError, RevisionError):
        refuse(broken)
    if scan_id.version not in sarif.GUID_VERSIONS:
        refuse(broken)
    return Analysis(
        id=scan_id,
        started_at=started if is_str(started := meta.get("started_at")) else None,
        revision=revision,
        git_status=status,
        stages=stages,
    )


def lines_of(text: str) -> list[str]:
    """The lines of git status's text, or of `check`'s list. No line for an empty text."""
    return text.split("\n") if text else []


def drift(analysis: Analysis, root: str) -> list[Change] | None:
    """How the checkout differs from what `start` recorded. If HEAD moved, only that change. Empty
    if nothing differs, and None if git gave no usable answer."""
    seen = observed(root)
    if seen is None:
        return None
    revision, status = seen
    commit = revision.get("commit")
    if commit != analysis.revision.get("commit"):
        return [Change(Kind.HEAD_MOVED, commit[: plugin.SHORT_ID_CHARS] if commit else "no commit")]
    before, after = lines_of(analysis.git_status), lines_of(status)
    old, new = set(before), set(after)
    return [
        *(Change(Kind.ADDED, line) for line in after if line not in old),
        *(Change(Kind.GONE, line) for line in before if line not in new),
    ]


def is_plain_file(path: Path) -> bool:
    """Whether `path` is a file that is not a symbolic link and has no other name."""
    return path.is_file() and not is_link(path) and path.stat().st_nlink < 2


def seen_by_check(out: Path) -> list[str]:
    """The lines that earlier runs of `check` wrote down, less blank ones: each change that one of
    them saw, GIT_FAILED if git gave one no usable answer, and CHANGE_LIST_LOST if one found the
    list lost. [CHANGE_LIST_LOST] if no line is left, or if a link, symbolic or hard, or something
    that is no file stands at the list's name. [] if nothing stands there. Raises OSError if the
    list cannot be read."""
    path = out / CHANGES_NAME
    if not os.path.lexists(path):
        return []
    real = is_plain_file(path)
    noted = lines_of(path.read_text(encoding="utf-8", errors="replace")) if real else []
    return [line for line in noted if line.strip()] or [CHANGE_LIST_LOST]


def refuse_and_note(out: Path, message: str, lines: Iterable[str]) -> NoReturn:
    """Add `lines` to what earlier runs of `check` wrote down, and refuse with `message`. If the
    lines cannot be written, the refusal says so."""
    path = out / CHANGES_NAME
    try:
        all_seen = dict.fromkeys([*seen_by_check(out), *lines])
        with path.open("wb" if is_plain_file(path) else "xb") as noted:
            noted.write(utf8("\n".join(all_seen)))
    except OSError as error:
        why = error.strerror
        if isinstance(error, FileExistsError) or os.path.isdir(path):
            why = "a link, a folder or something else that is not a plain file has that name"
        failure = f"{CHANGES_NAME} could not be updated ({why})"
        message += f"\n{failure}, so the results may not show what changed."
    refuse(message)


def has_report(out: Path, stage: Stage) -> bool:
    """Whether the stage's report is saved. A file with no letter or number in its first REPORT_HEAD
    characters is no report. One that is not empty and cannot be opened counts as saved. May raise
    OSError if the stage's folder cannot be searched."""
    report = out / stage.folder / REPORT_NAME
    if not (report.is_file() and report.stat().st_size):
        return False
    try:
        with report.open(encoding="utf-8", errors="replace") as text:
            return any(map(str.isalnum, text.read(REPORT_HEAD)))
    except OSError:
        return True


def says_completed(out: Path, stage: Stage) -> bool:
    """Whether COMPLETED is the last line of the stage's saved report that is not blank. False for a
    report that cannot be read."""
    try:
        text = (out / stage.folder / REPORT_NAME).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return text.rstrip().rpartition("\n")[2] == COMPLETED


def handoff_of(out: Path, before: Stage, stage: Stage) -> Path | None:
    """The handoff that `stage` starts from: the one that the stage just before it left, if that
    stage's report is saved. None otherwise."""
    handoff = out / before.folder / "handoff.md"
    saved = has_report(out, before) and handoff.is_file()
    return handoff if saved and before.number + 1 == stage.number else None


def message_of(out: Path, stage: Stage) -> list[str] | None:
    """The lines of the message after `stage`, a stage that has_report() passed, from the one text
    between MESSAGE_MARKS in the first REPORT_HEAD characters of its report. The text is then marked
    as told. Each record's question stands below the text. None where those characters hold no such
    text, where the text or a question fails a check, where a record cannot be used, where the text
    was told before, where the report or the findings folder cannot be read, or where the mark
    cannot be left."""
    try:
        with (out / stage.folder / REPORT_NAME).open(encoding="utf-8", errors="replace") as report:
            text = report.read(REPORT_HEAD)
    except OSError:
        return None
    lines = text.splitlines()
    start, end = MESSAGE_MARKS
    if lines.count(start) != 1 or lines.count(end) != 1:
        return None
    block = "\n".join(lines[lines.index(start) + 1 : lines.index(end)]).strip()
    if not block or len(block.split()) > MESSAGE_WORDS:
        return None
    try:
        entries = gathered(out, [stage])[0]
    except OSError:
        return None
    if any(each.outcome is Outcome.LEFT_OUT for each in entries):
        return None
    needed = {each.id for each in entries if each.outcome not in SETTLED}
    if not all(re.search(rf"\b{re.escape(name)}\b", block) for name in needed):
        return None
    asked: dict[str, list[str]] = {}
    for each in with_questions(entries):
        asked.setdefault(each.question, []).append(each.id)
    questions = [f"{', '.join(names)}: {question}" for question, names in asked.items()]
    said = "\n\n".join(filter(None, [block, listing(QUESTIONS_HEADING, questions)]))
    if SEVERITY_WORD.search(said) or NOTHING_UNPROVEN.search(said):
        return None
    if any(ORDER_LINE.match(line) for line in said.splitlines()):
        return None
    try:
        (out / f"{plugin.MESSAGE_TOLD}{stage.folder}").touch(exist_ok=False)
    except OSError:
        return None
    return [
        MESSAGE_EDGE,
        STAGE_ENDED.format(stage.number, stage.title),
        "",
        FLAGGED_HEADING,
        "",
        said,
        "",
        "No answer is due now.",
        MESSAGE_EDGE,
    ]


def check(given: str, called: str) -> list[str]:
    """Compare the checkout with what `start` recorded. Refuse where they differ or git gives no
    usable answer, and write that down. Say what the comparison cannot see, or that the target's
    files were not compared, and which handoff each later stage starts from. Once the last stage
    that was asked for has a report, and until a write has finished, give the next step, with the
    `write:` command. Last, tell the session what to pass on to the user. `called` is as for
    start(). May raise OSError where a folder of the analysis cannot be searched or listed: main()
    reports that as a refusal."""
    out = output_directory(given)
    analysis = recorded(out)
    changes = drift(analysis, str(out.parent))
    if changes is None:
        refuse_and_note(out, f"{GIT_FAILED}. {ASK_GIT}", [GIT_FAILED])
    if changes:
        shown, rest = changes[:CHANGES_PRINTED], changes[CHANGES_PRINTED:]
        more = [f"... and {len(rest)} more"] if rest else []
        kinds = {change.kind for change in shown}
        signs = [text for kind, text in SIGNS.items() if kind in kinds]
        undo = "Undo each change that is not yours, and keep your own. Then ask for a new analysis."
        advice = "Ask for a new analysis." if Kind.HEAD_MOVED in kinds else " ".join([*signs, undo])
        shown_lines = [change.line for change in shown]
        message = "\n".join([f"{CHECKOUT_CHANGED}:", *shown_lines, *more, advice])
        refuse_and_note(out, message, (change.line for change in changes))
    next_step: list[str] = []
    if has_report(out, analysis.stages[-1]) and not stamped(out):
        next_step = [NEXT, to_write(out, spelled(called))]
    no_change = "the comparison with the start of the analysis shows no change"
    outside = "the target's files were not compared, since the target was not in git at the start"
    handoffs = [
        f"handoff for stage {stage.number}: {handoff_of(out, before, stage) or 'none'}"
        for before, stage in zip(analysis.stages, analysis.stages[1:])
    ]
    if analysis.revision.get("versioned"):
        opening = [f"{no_change}: {analysis.tag}", analysis.unseen_sentence]
        ended = next((stage for stage in analysis.stages[::-1] if has_report(out, stage)), None)
        lines = ended and message_of(out, ended)
        last = [*lines, RELAY_THE_TEXT] if lines else [RELAY]
    else:
        opening, last = [f"{outside}: so {no_change}"], [RELAY_OUTSIDE_GIT]
    return [*opening, *handoffs, *next_step, *last]


def stamped(out: Path) -> bool:
    """Whether a write to the output directory `out` has finished: whether `out` holds a revision
    stamp. May raise OSError if `out` cannot be listed."""
    return any(plugin.is_revision_stamp(path) and path.is_file() for path in out.iterdir())


def inside(out: Path, path: Path) -> bool:
    """Whether `path` is a file whose real place is in the output directory `out`."""
    return path.is_file() and Path(os.path.realpath(path)).is_relative_to(os.path.realpath(out))


def why_unread(out: Path, path: Path) -> str:
    """Why `write` does not read what stands at `path`, where a patch or the regression suite may
    lie. Empty if `write` reads it."""
    try:
        if not inside(out, path):
            return NOT_READ
        with path.open("rb"):
            return ""
    except OSError as error:
        return fault(error)


def coverage_of(out: Path) -> str:
    """The session's account of what the stages covered, as the report carries it. A line that opens
    with "#" gets a backslash before it, so that it opens no heading."""
    path = out / COVERAGE_NAME
    if not inside(out, path):
        refuse(
            f"{COVERAGE_NAME} is not a file in the output directory (it is missing, or something "
            "else stands at its name): write it there as a file first"
        )
    try:
        text = under_a_heading(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        refuse(f"{COVERAGE_NAME} is not UTF-8: write it again")
    if not text.strip():
        refuse(f"{COVERAGE_NAME} holds no text: write it again")
    return text


def united(groups: Iterable[Sequence[str]]) -> list[list[str]]:
    """The groups, with any groups that share a finding merged into one."""
    whole: list[list[str]] = []
    for group in groups:
        linked = [other for other in whole if set(other) & set(group)]
        whole = [other for other in whole if other not in linked]
        whole.append(list(dict.fromkeys(itertools.chain(*linked, group))))
    return whole


class Group(NamedTuple):
    """Confirmed findings that the report shows as one: `head`, the most severe of them, with `rest`
    listed under it."""

    head: str
    rest: list[str]


def place_of(found: Finding, scan: sarif.Scan) -> tuple[str, int]:
    """A finding's file, as the SARIF log names it, and its line."""
    return sarif.repository_path(scan, found), found["line"]


def credential_lines(confirmed: Mapping[str, Rated], scan: sarif.Scan) -> set[tuple[str, int]]:
    """The place of each of `confirmed` that reports a hard-coded credential."""
    credentials = filter(secret.is_credential, (each.finding for each in confirmed.values()))
    return {place_of(found, scan) for found in credentials}


def findings_of(
    confirmed: Mapping[str, Rated], groups: Sequence[Group], root: str, scan: sarif.Scan
) -> list[Record]:
    """The findings as every product carries them, in the report's order. A finding on a line that a
    confirmed finding reports as a hard-coded credential has an empty `snippet`."""
    listed = {group.head: group.rest for group in groups}
    below = {name for group in groups for name in group.rest}
    grouped = [
        {
            **first.raw,
            "also_at": [
                {**confirmed[name].raw, "confidence": first.raw["confidence"]}
                for name in listed.get(head, ())
            ],
        }
        for head, first in confirmed.items()
        if head not in below
    ]
    off_disk_ids = {name for name, each in confirmed.items() if each.off_disk}
    made = [built(row, root, off_disk_ids) for row in grouped]
    if gone := [error.finding_id for each in made for error in each.refused]:
        refuse(f"the code of {series(gone)} changed while this command ran: run it again")
    findings = [each.finding for each in made]
    findings.sort(key=lambda found: ([-grade for grade in strength(found)], found["id"]))
    carried = {found["id"]: found for each in made for found in each.carried}
    records = sarif.placed(findings, scan, {}, listed=carried, refused_secrets=())
    secrets = credential_lines(confirmed, scan)
    return [
        {**found, "snippet": ""} if place_of(found, scan) in secrets else found for found in records
    ]


def flaw_groups(
    same_groups: Sequence[Sequence[str]],
    entries: Sequence[Entry | LeftOut],
    confirmed: Mapping[str, Rated],
    scan: sarif.Scan,
) -> list[Group]:
    """The groups of confirmed findings that the report shows as one finding each: the groups in
    `same_groups`, which the session named, and the findings that share one site. It refuses an id
    in `same_groups` that names neither a confirmed finding nor a record that is left out."""
    left_out_ids = {entry.id for entry in entries if entry.outcome is Outcome.LEFT_OUT}
    unknown = [
        f"--same {','.join(group)}: {name or 'an empty id'} is not a confirmed finding"
        for group in same_groups
        for name in group
        if name not in confirmed and name not in left_out_ids
    ]
    if unknown:
        refuse("\n".join(unknown))
    by_session = [[name for name in group if name in confirmed] for group in same_groups]
    sites: defaultdict[sarif.Site, list[str]] = defaultdict(list)
    for name, each in confirmed.items():
        if site := sarif.site(each.finding, scan):
            sites[site].append(name)
    by_site = [names for names in sites.values() if len(names) > 1]
    ordered = (
        sorted(group, key=lambda name: -confirmed[name].severity)
        for group in united([*by_session, *by_site])
        if len(group) > 1
    )
    return [Group(head, rest) for head, *rest in ordered]


def reasons_of(
    analysis: Analysis,
    saved: Sequence[Stage],
    on_own_word: Sequence[Stage],
    entries: Sequence[Entry | LeftOut],
    marks: Sequence[str],
    changes: Sequence[str],
) -> dict[Reason, str]:
    """Why the report reads unverified, each reason in a sentence. Empty where it reads verified.
    `on_own_word` holds the saved stages that are taken at their word: none of them counts as a
    stage that sent nothing. `marks` holds those of MARKS that apply. `changes` names what drift()
    found, or else what an earlier `check` saw."""
    unsaved = [f"stage {stage.number}" for stage in analysis.stages if stage not in saved]
    sent = {e.stage for e in entries if e.outcome.from_check or e.outcome is Outcome.LEFT_OUT}
    unchecked = [f"stage {s.number}" for s in saved if s not in sent and s not in on_own_word]
    left_out_count = sum(entry.outcome is Outcome.LEFT_OUT for entry in entries)
    unresolved_count = sum(entry.outcome is Outcome.UNRESOLVED for entry in entries)
    shown = [code_span(cut(" ".join(change.splitlines()))) for change in changes]
    changes_text = at_most(CHANGES_IN_REASON, shown)
    no_report = f"the results hold nothing from {series(unsaved)}, for which no report was saved"
    not_checked = f"{series(unchecked)} sent no finding to the independent check"
    unusable = f"{left_out_count} of {counted(len(entries), 'record')} could not be used"
    unresolved = f"the independent check did not settle {counted(unresolved_count, 'finding')}"
    sentences = {
        Reason.GIT_FAILED: GIT_FAILED if GIT_FAILED in marks else "",
        Reason.CHANGE_LIST_LOST: CHANGE_LIST_LOST if CHANGE_LIST_LOST in marks else "",
        Reason.CHECKOUT_CHANGED: f"{CHECKOUT_CHANGED}: {changes_text}" if changes else "",
        Reason.NO_STAGE_REPORT: no_report if unsaved else "",
        Reason.RECORDS_UNUSABLE: unusable if left_out_count else "",
        Reason.FINDINGS_UNRESOLVED: unresolved if unresolved_count else "",
        Reason.STAGE_NOT_CHECKED: not_checked if unchecked else "",
    }
    return {reason: sentences[reason] for reason in Reason if sentences[reason]}


def results_of(out: Path, analysis: Analysis, same_groups: Sequence[Sequence[str]]) -> Results:
    """Everything that the stages and the session left in the output directory, checked."""
    ends = time.monotonic() + TRIAL_SECONDS
    root = str(out.parent)
    saved = [stage for stage in analysis.stages if has_report(out, stage)]
    if not saved:
        refuse(f"no stage's {REPORT_NAME} holds a report, so there are no results to write")
    coverage = coverage_of(out)
    entries, confirmed = gathered(out, saved)
    part = [str(stage.number) for stage in saved] if len(saved) < len(Stage) else []
    mode = "-".join([MODE, *part])
    scan = sarif.Scan(analysis.id, mode, prefix="", remote=None, scope=(), revision=None)
    groups = flaw_groups(same_groups, entries, confirmed, scan)
    under = {name: name for name in confirmed} | {n: g.head for g in groups for n in g.rest}
    on_disk = [(stage, path) for stage in saved for path in patches_in(out, stage)]
    suite_path = out / SUITE_PLACE
    has_suite = SUITE_STAGE in saved and os.path.lexists(suite_path)
    paths = [*(path for _, path in on_disk), *([suite_path] if has_suite else [])]
    unread = {path: why for path in paths if (why := why_unread(out, path))}
    stated = {name: each.gate for name, each in confirmed.items() if each.entry.stage is Stage.ONE}
    stated |= {
        record.stem: Outcome.REFUTED
        for record in (records_in(out, Stage.ONE) if Stage.ONE in saved else ())
        if Stage.ONE.holds(record.stem) and refuses_its_gate(record)
    }
    gates = (
        path.name
        for stage, path in on_disk
        if stage is Stage.ONE and (path not in unread or not Held.of(path.name))
    )
    claims = claims_of(gates, stated)
    patches = [
        patch_of(path, stage, root, under, claims) for stage, path in on_disk if path not in unread
    ]
    suite = suite_of(suite_path, root) if has_suite and suite_path not in unread else None
    records = findings_of(confirmed, groups, root, scan)
    work = (f"{stage.folder}/{WORK_DIR_NAME}" for stage in analysis.stages)
    drifted = drift(analysis, root)
    try:
        noted = seen_by_check(out)
    except OSError:
        noted = [CHANGE_LIST_LOST]
    current = [change.line for change in drifted or ()]
    changes = current or [line for line in noted if line not in MARKS]
    marks = [mark for mark in MARKS if mark in noted or (mark == GIT_FAILED and drifted is None)]
    barred = {entry.stage for entry in entries} | {stage for stage, _ in on_disk}
    on_own_word = [stage for stage in saved if stage not in barred and says_completed(out, stage)]
    return Results(
        out=out,
        analysis=analysis,
        saved=saved,
        on_own_word=on_own_word,
        coverage=coverage,
        entries=entries,
        confirmed=confirmed,
        under=under,
        scan=scan,
        records=records,
        unknown_cwes=unrecognized_cwes(records),
        patches=patches,
        unread={path.relative_to(out).as_posix(): why for path, why in unread.items()},
        clashes=clashes_of(root, out, patches, suite, lambda: time.monotonic() < ends),
        suite=suite,
        leftovers=[folder for folder in work if os.path.lexists(out / folder)],
        reasons=reasons_of(analysis, saved, on_own_word, entries, marks, changes),
        generated=datetime.now(timezone.utc).replace(microsecond=0),
    )


def stamp_of(results: Results) -> dict[str, object]:
    """The revision stamp. It has the keys of a scan's stamp that apply to an analysis, with `model`
    always null, and also `stages`. It has no `duration_s`. As in a scan's stamp, `reason_kind` is
    the word of the first reason."""
    grades, tally = results.grades, results.tally
    return {
        "generated_at": results.generated.isoformat(),
        "scan_id": str(results.analysis.id),
        "mode": plugin.ANALYSIS_STAMP_MODE,
        "plugin_version": plugin.version(),
        "scan_prefix": results.scan.prefix,
        "scope": list(results.scan.scope),
        "revision": results.analysis.revision,
        "revision_source": SELF_REPORTED,
        "model": None,
        "stages": [stage.folder for stage in results.saved],
        "findings": {
            "total": len(results.records),
            **{g.lower(): grades[g] for g in Severity.__members__},
        },
        "verification": {
            "status": results.status,
            "records": len(results.entries),
            **{each.name.lower(): tally[each] for each in Outcome},
            "stages_on_own_word": [stage.folder for stage in results.on_own_word],
            "reason": results.reason_unnamed,
            "reason_kind": next((reason.word for reason in results.reasons), None),
        },
    }


def log_of(results: Results) -> dict[str, object]:
    """The SARIF log. Its run's property bag is the stamp, without the STAMP_ONLY keys and the
    top-level keys that are null."""
    bag = {
        key: {k: v for k, v in value.items() if k not in STAMP_ONLY} if is_map(value) else value
        for key, value in stamp_of(results).items()
        if value is not None and key not in STAMP_ONLY
    }
    notes = list(map(sarif.unrecognized_cwe_note, results.unknown_cwes))
    if sparse := results.analysis.sparse_sentence:
        notes.append(sarif.notification("coverage/sparse-checkout", "note", sparse))
    if results.reason:
        notes.append(sarif.unverified_note(results.reason))
    return sarif.log(results.records, results.scan, plugin.version(), bag, {}, notes)


def location(file: str, line: int) -> str:
    return span(f"{file}:{line}")


def labeled(label: str, *texts: str) -> str:
    """One labeled part of the report, with each text ended as a sentence. Empty if every text is
    empty."""
    said = " ".join(sarif.sentence(text) for text in texts if text)
    return f"**{label}.** {said}" if said else ""


def listing(opening: str, items: Sequence[str]) -> str:
    """A list under its opening line; empty when it has no item."""
    return "\n".join([opening, *(f"- {item}" for item in items)]) if items else ""


def as_code(text: str) -> str:
    """A model's text on one line, as a code span."""
    return code_span(one_line(text))


def on_credential_line(findings: Iterable[Finding], results: Results) -> bool:
    """Whether one of `findings` stands on the line of a confirmed hard-coded credential."""
    places = {place_of(each, results.scan) for each in findings}
    return not places.isdisjoint(credential_lines(results.confirmed, results.scan))


def listed_needs(shown: Sequence[str], listed: Sequence[Finding]) -> list[str]:
    """A bullet for each of `listed` whose preconditions differ from `shown`, the shown finding's
    as section() prints them."""
    return [
        f"{each['id']}: {'; '.join(map(as_code, each['preconditions'])) or NOTHING_NEEDED}"
        for each in listed
        if set(map(one_line, each["preconditions"])) != set(shown)
    ]


def listed_fixes(shown: str, listed: Sequence[Finding]) -> list[str]:
    """A bullet for each of `listed` that gives a fix, unless it is `shown`, the shown finding's
    fix on one line, once both end as sentences."""
    known = {"", sarif.sentence(shown)}
    return [
        f"{each['id']}: {as_code(each['recommendation'])}"
        for each in listed
        if sarif.sentence(one_line(each["recommendation"])) not in known
    ]


def weakness(cwe_id: str) -> str:
    """A finding's CWE id, as the report shows it."""
    known = cwe.catalog.defines(cwe.id_number(cwe_id))
    return cwe_id if known else f"{cwe_id} (not a weakness in CWE {cwe.catalog.version})"


def offer_of(patch: Patch, owner: str) -> str:
    """A patch as the report offers it under the finding `owner`: its copy's path, and what a
    user must know of it first."""
    partly = f"written for {series(patch.ids)}, so it may not cover all of this finding"
    set_aside = f"set aside: {patch.reason}" if patch.reason else ""
    notes = "; ".join(filter(None, ("" if owner in patch.ids else partly, set_aside)))
    name = code_span(f"{PATCHES}/{patch.path.name}")
    return f"{name} ({notes})" if notes else name


def section(found: Record, results: Results) -> str:
    """One finding's section: a scan's heading and labels, an attack chain and an open question.
    The fix's label is "Fix", without a scan's "(not verified)"."""
    first = results.confirmed[found["id"]]
    offered = [
        offer_of(patch, found["id"]) for patch in results.patches if found["id"] in patch.owners
    ]
    group = [first.entry, *(results.confirmed[other["id"]].entry for other in found["also_at"])]
    stated, checked, symbol = first.stated, first.checked, found["symbol"].strip()
    where = location(found["file"], found["line"]) + (f" in {span(symbol)}" if symbol else "")
    also = [
        f"{other['id']} — {location(other['file'], other['line'])} — {weakness(other['cwe_id'])}, "
        f"{other['severity']}: {one_line(other['title'])}"
        for other in found["also_at"]
    ]
    needs = [one_line(item) for item in found["preconditions"]]
    listed = [results.confirmed[other["id"]].finding for other in found["also_at"]]
    withheld = bool(listed) and on_credential_line((found, *listed), results)
    to_print = [] if withheld else listed
    their_needs = listed_needs(needs, to_print)
    own_fix = one_line(found["recommendation"])
    their_fixes = listed_fixes(own_fix, to_print)
    attached = "Suggested fixes are attached" if len(offered) > 1 else "A suggested fix is attached"
    fixes = f"{attached}, untested: {', '.join(offered)}." if offered else ""
    several = f"Read {code_span(INDEX)} before you apply more than one."
    fix_part = labeled(
        "Fix",
        own_fix,
        fixes,
        several if len(offered) > 1 else "",
        LISTED_FIXES_OPENING if their_fixes else "",
    )
    ratings = ""
    if checked < stated:
        ratings = (
            f"The independent check lowered the severity from {stated.name} to {checked.name}."
        )
    elif checked > stated:
        ratings = (
            f"The independent check rated it {checked.name}. The stage's lower rating is shown."
        )
    evidence = f"Evidence: {', '.join(code_span(entry.evidence) for entry in group)}."
    rating = f"({found['severity']}, confidence {found['confidence']})"
    parts = [
        f"### {found['id']} — {one_line(found['title'])} {rating}",
        labeled("Impact", one_line(found["impact"])),
        f"**Where.** {where} — {weakness(found['cwe_id'])}",
        listing(f"**{ALSO_LABEL}.**", also),
        labeled("What", one_line(found["description"])),
        labeled("Exploit scenario", one_line(found["exploit_scenario"])),
        listing("**Preconditions.**", needs) or "**Preconditions.** None.",
        LISTED_NOT_PRINTED if withheld else listing(LISTED_NEEDS_OPENING, their_needs),
        listing(fix_part, their_fixes) or fix_part,
        labeled(
            CHAIN_LABEL,
            first.entry.chain,
            *(f"{e.id}: {e.chain}" for e in group[1:] if e.chain),
        ),
        labeled(
            QUESTION_LABEL,
            first.entry.question,
            *(f"{e.id}: {e.question}" for e in group[1:] if e.question),
        ),
        labeled(
            "Verification",
            "Confirmed by an independent check.",
            first.entry.verification,
            ratings,
            *(f"{e.id}: {e.verification}" for e in group[1:] if e.verification),
            evidence,
        ),
    ]
    return "\n\n".join(filter(None, parts))


def glance(found: Record) -> str:
    """One finding's line in the list under the report's opening."""
    rating = f"{found['severity']}, confidence {found['confidence']}"
    place = location(found["file"], found["line"])
    return f"{found['id']} — {rating} — {place} — {one_line(found['title'])}"


def name_of(entry: Entry | LeftOut) -> str:
    """A record's id, as the report shows it."""
    return entry.id if entry.stage.holds(entry.id) else unbroken(f"{entry.stage.folder}/{entry.id}")


def aside(entry: Entry | LeftOut) -> str:
    """The report's line for a record that is not confirmed."""
    name = name_of(entry)
    if entry.outcome is Outcome.LEFT_OUT:
        where, texts = "", (unbroken(entry.fault), f"See {span(entry.evidence)}")
    else:
        where = span(entry.place) if entry.place else ""
        chained, asked = labeled(CHAIN_LABEL, entry.chain), labeled(QUESTION_LABEL, entry.question)
        texts = (one_line(entry.title), entry.verification, chained, asked)
    said = " ".join(sarif.sentence(text) for text in texts if text)
    return " — ".join(filter(None, [name, where, said]))


def markdown_of(results: Results) -> str:
    """CLAUDE-SECURITY-RESULTS.md."""
    tally, entries, records = results.tally, results.entries, results.records
    asides = [
        listing(f"**{each.heading}.**", [aside(e) for e in entries if e.outcome is each])
        for each in Outcome
        if each is not Outcome.CONFIRMED
    ]
    confirmed, refuted = tally[Outcome.CONFIRMED], tally[Outcome.REFUTED]
    unresolved = tally[Outcome.UNRESOLVED]
    target, tag = span(git.from_disk(results.out.parent.name)), code_span(results.analysis.tag)
    revision = results.analysis.revision
    marked = f", so the revision ends in {code_span('-dirty')}" if revision.get("commit") else ""
    changed = f" The checkout already had uncommitted changes at the start of the analysis{marked}."
    opening = (
        f"{capitalized(results.headline)}. This is an attack surface analysis of {target} at "
        f"revision {tag}, written on {results.generated:%Y-%m-%d} at {results.generated:%H:%M} "
        f"UTC. It maps what an attacker can reach, and what would shrink that. {READ_ONLY} It is "
        "not a vulnerability scan." + (changed if revision.get("dirty") else "")
    )
    overlap = (
        " The stages judge and count independently: one issue may be counted by more than one "
        "stage, or be confirmed by one stage and not by another."
    )
    unrecorded = (
        f" A stage's own {REPORT_NAME} can list or flag more items. They have no record, so "
        "this report does not count or list them."
    )
    stages = listing(
        "An id shows which stage reported a finding."
        + (overlap if len(results.saved) > 1 else "")
        + unrecorded,
        [stage_line(results, stage) for stage in results.saved],
    )
    lost, sent = tally[Outcome.LEFT_OUT], sum(tally[each] for each in Outcome if each.from_check)
    method = (
        "Each stage traces its findings through the code. An independent check then tries to prove "
        "each finding wrong. It is given the finding, and not the analysis behind it."
    )
    counts = (
        f"Of {counted(sent, 'finding')} meant for it: confirmed {confirmed}, refuted {refuted}, "
        f"not settled {unresolved}."
    )
    unused = (
        f"Not in these counts: {counted(lost, 'record')} that could not be used." if lost else ""
    )
    basis = (
        "Each finding shows the lower of the stage's rating and the independent check's. These "
        "counts are summed up from the analysis's own records, in which each stage wrote down what "
        "came of that check."
    )
    above = (
        "Confirmed findings that are one flaw, or that report the same category of weakness on the "
        f"same line, are shown as one. That gives the {counted(len(records), 'finding')} above."
    )
    merged = above if confirmed != len(records) else ""
    checked = " ".join(filter(None, (method, counts, unused, merged, basis)))
    patches = labeled(
        "Patches",
        f"{code_span(INDEX)} describes each patch file of the stages that saved a report",
        "None has been tested",
        results.suite_sentence(code_span(INDEX)),
    )
    rests_on = (
        "This status rests on the analysis's own files, on the files of the checkout that its "
        "records name and, if the checkout is in git, on what git says of the checkout. It does "
        f'not show how much of the code the stages examined. The "{COVERAGE_HEADING}" section '
        "above gives the account of the Claude Code session that ran the analysis."
    )
    parts = [
        "# Claude Security results: attack surface analysis",
        f"**This report is unverified: {results.reason}.**" if results.reason else "",
        " ".join(
            dict.fromkeys((*results.meanings, *(each.texts.step for each in results.reasons_told)))
        ),
        results.own_word_sentences,
        *(
            f"**{code_span(left)} was left behind. It can hold copies of your code. If it is still "
            "there, delete it before you build or test.**"
            for left in results.leftovers
        ),
        opening,
        listing("**At a glance.**", list(map(glance, records))),
        f"## {COVERAGE_HEADING}",
        results.analysis.sparse_sentence,
        results.coverage,
        stages,
        "## Findings",
        *([section(found, results) for found in records] or ["None confirmed."]),
        *(["---", patches] if results.indexed else []),
        *(
            [
                f"## {NOT_CONFIRMED_HEADING}",
                "Nothing here is counted among the findings above.",
                *asides,
            ]
            if any(asides)
            else []
        ),
        "## What was verified",
        checked,
        results.analysis.unseen_sentence,
        f"{results.status_sentence} {rests_on}",
    ]
    return "\n\n".join(filter(None, parts)) + "\n"


def first_steps(results: Results, patch: Patch) -> str:
    """What a patch's comment lines say to do before it is applied."""
    lead = "If you ask Claude to apply it,"
    told = f"{lead} Claude should first tell you that the report is unverified."
    if not patch.ready:
        ask = (
            f"{lead} Claude should ask you first, since the patch is set aside. A request to apply "
            "all patches means the ready ones, and not this one."
        )
    elif results.cautions(patch):
        ask = (
            f"{lead} Claude should ask you first, since {plugin.PATCHES_INDEX_NAME} names it with "
            "another patch, even one that nobody applies, or marks it for an open question."
        )
    else:
        ask = (
            f"{lead} and the patch changes a file that is not committed as it is now, Claude "
            "should ask you first."
        )
    cannot_answer = (
        "If Claude should ask, and you cannot answer, Claude should leave the patch out and say "
        "why."
    )
    not_allowed = (
        "A request to apply it does not let Claude commit, stash or discard your changes, and a "
        "copy that Claude makes does not take the place of asking you."
    )
    return " ".join([
        f"Before you apply this patch, {COPY_FIRST}.",
        *([told] if results.reasons else []),
        ask,
        cannot_answer,
        not_allowed,
    ])


def copy_of(results: Results, patch: Patch) -> bytes:
    """A patch with comment lines above it that say what it is, what to do before it is applied,
    and what a request to apply it means. git apply ignores those lines."""
    wrap = textwrap.TextWrapper(width=76, break_long_words=False, break_on_hyphens=False).wrap
    advice = (results.confirmed[name].finding["recommendation"] for name in patch.ids)
    changes = [" ".join(printable(text).split()) for text in advice]
    command = f"{APPLY} {results.out.name}/{PATCHES}/{patch.path.name}"
    notice = (
        "The report of this analysis is unverified. Read why at the top of "
        f"{plugin.RESULTS_MD_NAME}, one folder up, before you use this patch."
    )
    paragraphs = [
        [f"Set aside: {patch.reason}."] if patch.reason else [],
        wrap(f"{READ_ONLY} Review the change before you keep it."),
        *map(wrap, changes),
        wrap(notice) if results.reasons else [],
        [
            *wrap(first_steps(results, patch)),
            *(
                [f"Apply, from the folder that was analyzed:  {command}"]
                if patch.applies is Tried.APPLIES
                else []
            ),
        ],
        wrap(AFTER_APPLY),
    ]
    lines = [
        *(
            f"Claude Security -- suggested patch for {name}: "
            + " ".join(printable(results.confirmed[name].entry.title).split())
            for name in patch.ids
        ),
        f"Written against revision {results.analysis.tag}, the revision that was analyzed.",
        *(line for paragraph in paragraphs if paragraph for line in ("", *paragraph)),
        "",
    ]
    return utf8("".join(f"# {line}".rstrip() + "\n" for line in lines)) + patch.diff


def suite_advice(suite: Suite) -> str:
    """The end of PATCHES.md's sentence on the regression suite: whether it can be run, and how."""
    when = (
        "before you apply a patch that is named for a finding from "
        f"{SUITE_STAGE.id_range}, and again after."
    )
    how_to_run = f"with how to run them. Run them {when}"
    if suite.applies is Tried.APPLIES:
        return how_to_run
    if suite.applies is Tried.REFUSED:
        return f"but {suite.applies.told(suite.said)}, so it cannot be run as it is."
    if suite.applies is Tried.BLOCKED:
        caution = f"But {suite.applies.told(suite.said)}."
        return f"with how to run them. {caution} If it applies, run them {when}"
    if (
        suite.applies is Tried.NOT_NEW
        or suite.applies is Tried.UNSEEN
        or suite.applies is Tried.NO_ANSWER
        or suite.applies is Tried.NOT_CHECKED
    ):
        caution = (
            f"But {suite.applies.told(suite.said)}. The suite can change or remove a file, and git "
            "cannot bring back one that is not committed. Read it before you apply it."
        )
        return f"with how to run them. {caution} If it applies, run them {when}"
    return unreachable(suite.applies)


def applying(out: Path) -> str:
    """PATCHES.md's section on how to apply a patch."""
    command = (
        "## Applying a patch\n\nFrom the folder that was analyzed:\n\n"
        f"```\n{APPLY} {out.name}/{PATCHES}/<name>\n```\n"
    )
    before = f"Before you apply a patch, {COPY_FIRST}."
    failed = f"If git apply fails, {LEFT_HALFWAY} In a git repository, {WAY_BACK}"
    after = (
        "After you apply a patch or take one out, look at what changed: where lines are alike, git "
        "may put a change in the wrong place. In a git repository, run git status and git diff."
    )
    undo = (
        "To take a patch out again, run the same command with -R. Unless git picks a wrong place, "
        "that keeps your own changes to the same files. Taking a patch out with git restore can "
        "also drop your own changes. If you have since changed what the patch changed, or one of "
        "the few lines around it, git normally refuses. Where git refuses, undo the whole patch by "
        "hand."
    )
    keep = "Review each change before you keep it."
    return f"{listing(command, [before, failed, undo, after, keep])}\n\n{AFTER_APPLY}"


def shown_under(name: str, head: str) -> str:
    """A note on a finding that the report shows under another one, `head`. Else empty."""
    return "" if head == name else f" (shown under {head})"


def index_of(results: Results) -> str:
    """PATCHES.md: the patches that are ready, those set aside, the findings with no patch in
    its folder, the patches that may clash or could not be tried together, the regression suite, and
    how to apply a patch."""
    out, patches = results.out, results.patches

    clashing = results.clashing

    def title_of(name: str) -> str:
        title = one_line(results.confirmed[name].entry.title)
        return f"**{name}** -- {title}{shown_under(name, results.under[name])}"

    def questions_of(name: str) -> str:
        asked = results.asked_with(name)
        several = len(asked) > 1
        words = "have open questions: read them" if several else "has an open question: read it"
        return f"{series(asked)} {words} in {plugin.RESULTS_MD_NAME} first" if asked else ""

    def partly(patch: Patch, name: str) -> str:
        head = results.under[name]
        return "" if head in patch.ids else f"it may not cover all of {head}"

    def others(patch: Patch, name: str) -> str:
        files = [code_span(each.path.name) for each in results.others(patch, name)]
        instead = " or ".join(files)
        return f"the independent check may have confirmed {instead} instead" if files else ""

    def lines(patch: Patch) -> list[str]:
        """One line for each finding that the patch was written for, named by that finding's title.
        A patch that is not copied gets one line, named by its path."""
        why = f": {patch.reason}" if patch.reason else ""
        see = f'see "{PATCHES_APART}" below' if patch.shown(out) in clashing else ""
        file = f"{code_span(patch.path.name)}{why}"
        attached = [
            f"{title_of(name)}: {file}"
            + noted(partly(patch, name), others(patch, name), see, questions_of(name))
            for name in patch.ids
        ]
        return attached or [span(patch.shown(out)) + why + noted(see)]

    ready = [line for patch in patches if patch.ready for line in lines(patch)]
    set_aside = [
        *(line for patch in patches if not patch.ready for line in lines(patch)),
        *(f"{span(path)}: {why}" for path, why in results.unread.items()),
    ]
    patched = {owner for patch in patches for owner in patch.owners}
    unpatched = [title_of(found["id"]) for found in results.records if found["id"] not in patched]
    apart = [f"{series(map(span, clash.names))} {clash.advice}." for clash in results.clashes]
    opening = (
        f"Patches for findings in {code_span(out.name)}. Each patch was written alone against "
        f"revision {code_span(results.analysis.tag)}. {READ_ONLY} So no patch has been tested. "
        "Nothing here is applied, committed, or opened as a pull request until you choose to do so."
    )
    warning = (
        "A patch holds each line of your code that it changes, and usually a few lines around "
        "them. If those lines hold a credential value, so does the patch. Code that a patch adds, "
        "such as a test, can repeat such a value too. Check each patch for credential values "
        "before you share it."
    )
    tests = f"## The regression suite\n\n{code_span(SUITE_NAME)} adds tests of default behavior, "
    notice = (
        "**The report on these findings is unverified. Read the top of "
        f"{plugin.RESULTS_MD_NAME} first.**"
    )
    parts = [
        "# Suggested patches",
        notice if results.reason else "",
        opening,
        warning,
        listing("## Patches ready to apply\n", ready),
        listing("## Set aside\n", set_aside),
        listing("## Findings with no patch in this folder\n", unpatched),
        listing(f"## {PATCHES_APART}\n", apart),
        tests + suite_advice(results.suite) if results.suite else "",
        applying(out) if results.has_patch_files else "",
    ]
    return "\n\n".join(filter(None, parts)) + "\n"


def stage_line(results: Results, stage: Stage) -> str:
    """A stage's ids, its records by outcome, how many of them hold an open question, and its
    patches that wait on an answer."""
    mine = [entry for entry in results.entries if entry.stage is stage]
    tally = Counter(entry.outcome for entry in mine)
    questions = asking_in(mine)
    waiting = sum(
        p.held is Held.WAITING and p.stage is stage and p.path.suffix == ".patch"
        for p in results.patches
    )
    parts = (
        ", ".join(f"{tally[each]} {each.count_word}" for each in Outcome if tally[each])
        or "no record",
        f"open questions below: {questions}" if questions else "",
        f"patches that wait on your answer: {waiting}" if waiting else "",
    )
    return (
        f"{stage.id_range}, stage {stage.number} ({stage.title}): {'; '.join(filter(None, parts))}"
    )


def finding_line(found: Record, results: Results) -> str:
    """One finding on one line: its id and severity, its place, and at most TEXT_SHOWN characters of
    its title and of its impact. Two notes can stand in parentheses behind the severity: the
    independent check's rating, where it is higher than the stage's, and how many confirmed findings
    the report shows with this one."""
    own = results.confirmed[found["id"]]
    higher = f"the independent check rated this finding {own.checked.name}"
    more = f"the report shows {counted(len(found['also_at']), 'more confirmed finding')} with it"
    tag = noted(higher if own.checked > own.stated else "", more if found["also_at"] else "")
    place = one_line(f"{found['file']}:{found['line']}")
    texts = (cut(one_line(found["title"])), cut(one_line(found["impact"])))
    told = " -- ".join(filter(None, (place, *texts)))
    return f"finding: {found['id']} {found['severity']}{tag} at {told}"


def listed_of(results: Results) -> int:
    """How many of the findings `write` prints: each HIGH or CRITICAL finding, then each lower
    severity whole, gravest first, as long as the list has at most FINDINGS_LISTED findings. If the
    list is then empty, the first FINDINGS_LISTED."""
    grades = results.grades
    grave = sum(grades[grade.name] for grade in Severity if grade >= Severity.HIGH)
    totals = itertools.accumulate(grades[grade] for grade in Severity.__members__)
    limit = max(grave, FINDINGS_LISTED)
    return max((total for total in totals if total <= limit), default=0) or FINDINGS_LISTED


def uncommitted(results: Results) -> tuple[list[Patch], list[Patch]]:
    """The ready patches that change a file that is not committed as it is now. Then those of which
    git did not say whether they do: it gave no list of the patch's paths, or an empty one, or no
    answer on the files, or git names no repository whose top is the project. One exception: the
    project was outside git at the start, git names no repository now, and no folder from the
    project up holds a .git. There, a ready patch stands in the first list if something stands on
    disk at a path that it names, in the second if git lists no path of it, and else in neither."""
    root = str(results.out.parent)
    ready = [(patch, paths_of(root, patch.diff)) for patch in results.patches if patch.ready]
    top = git.toplevel(root)
    outside = not results.analysis.revision.get("versioned") and git.holder_of(root) is None
    if top is None and outside:
        changing = [patch for patch, paths in ready if paths and in_place(root, patch.diff)]
        return changing, [patch for patch, paths in ready if not paths]
    named = (path for _, paths in ready for path in paths or ())
    at_risk = not_committed(root, named) if top and git.is_top(root, top) else None
    unknown = [patch for patch, paths in ready if not paths or at_risk is None]
    return [p for p, paths in ready if paths and not (at_risk or set()).isdisjoint(paths)], unknown


def patch_lines(results: Results, promised: int) -> list[str]:
    """What `write` prints of the patches. `promised` is how many of them promise() names."""
    suite = [f"patches.regression_suite: {PATCHES}/{SUITE_NAME}"] if results.suite else []
    if results.ready + results.set_aside:
        return [
            f"patches.ready: {results.ready}",
            f"patches.set_aside: {results.set_aside}",
            *([f"patches.cautioned: {promised}"] if promised else []),
            *suite,
        ]
    no_folder = all(stage.patch_folder is None for stage in results.analysis.stages)
    why = "the stage that ran writes no patches" if no_folder else "there are no confirmed findings"
    return [
        f"patches: none ({why})" if no_folder or not results.records else "patches: none",
        *suite,
    ]


def ones_for(patches: Sequence[Patch]) -> str:
    """The patches, by the ids in their names: "the ones for F101 and F103 (shown under F201)"."""
    named = (item for patch in patches for item in patch.under.items())
    ids = series(dict.fromkeys(name + shown_under(name, head) for name, head in named))
    return f"the {'one' if len(patches) == 1 else 'ones'} for {ids}"


def each_once(cautioned: Sequence[Patch], changing: Sequence[Patch]) -> list[Patch]:
    """The patches of both lists. A patch can stand in both."""
    return [*cautioned, *(patch for patch in changing if patch not in cautioned)]


def promise(cautioned: Sequence[Patch], changing: Sequence[Patch], unknown: Sequence[Patch]) -> str:
    """The closing message's sentence on `Results.cautioned` and on both lists of uncommitted().
    Empty where all three are empty."""
    verb = "changes" if len(changing) == 1 else "change"
    told = (
        f"It cautions about {ones_for(cautioned)}" if cautioned else "",
        f"{ones_for(changing)} {verb} a file that is not committed" if changing else "",
        f"I could not check whether the files of {ones_for(unknown)} are committed"
        if unknown
        else "",
    )
    said = capitalized(", and ".join(filter(None, told)))
    them = "that one" if len(each_once(cautioned, [*changing, *unknown])) == 1 else "those"
    return f"{said}, so I will ask you before I apply {them}." if said else ""


def last_sentence(results: Results) -> str:
    """What ends the closing message: what to do about the first reason, or an offer. Empty where
    there is neither: then NOT_SHOWN ends the message."""
    questions = "go through the open questions with you"
    if results.reasons:
        said = results.reasons_told[0].texts.said
        return f"{said} I can also {questions}." if results.asking else said
    fix = "apply a patch" if results.ready else ""
    if offers := list(filter(None, (fix, questions if results.asking else ""))):
        return f"Want me to {', or '.join(offers)}? Just ask."
    return ""


def as_one_line(line: str) -> str:
    """`line`, if the bytes that this script prints for it, read as UTF-8, hold no character at
    which Python splits lines. If not, `line` on one line, with each character beyond ASCII as an
    escape."""
    read = console.read_as_utf8(line)
    if read.splitlines() == [read]:
        return line
    return " ".join(line.encode("ascii", "backslashreplace").decode("ascii").splitlines())


def facts_of(results: Results) -> list[str]:
    """What `write` prints, for the session to fill the closing message from: one fact to a line,
    then what the session passes on, as lines that start with RELAY_MARK, and the findings last."""
    out, records, listed = results.out, results.records, listed_of(results)
    waiting = {
        "open_questions": results.asking,
        "unproven": results.tally[Outcome.UNPROVEN],
        "flagged": results.tally[Outcome.OBSERVED],
    }
    products = series((plugin.RESULTS_MD_NAME, plugin.JSONL_NAME, plugin.SARIF_NAME))
    part = {1: " (one of three stages)", 2: " (two of three stages)"}.get(len(results.saved), "")
    exactly = "exactly as printed:"
    checkout_reason = any(reason.of_checkout for reason in results.reasons)
    unchecked = ", so nothing checked whether its files changed while it ran"
    not_in_git = f"{RELAY_MARK} {NOT_IN_GIT}{'' if checkout_reason else unchecked}"
    cautioned, (changing, unknown) = results.cautioned, uncommitted(results)
    ending = last_sentence(results)
    facts = [
        f"wrote {products} ({results.headline}) into {out.name}",
        f"duration_s: {strictjson.text(results.duration_s)}",
        f"verification.status: {results.status}",
        *([f"verification.reason: {results.reason}"] if results.reason else []),
        f"covers: {series(stage.covers for stage in results.saved)}{part}",
        *patch_lines(results, len(each_once(cautioned, [*changing, *unknown]))),
        *(f"{label}: {count}" for label, count in waiting.items() if count),
        *([f"findings.more: {by_severity(records[listed:])}"] if records[listed:] else []),
        *(
            [f"{RELAY_MARK} say this right after the reason, {exactly} {meaning}"]
            if (meaning := " ".join(results.meanings))
            else []
        ),
        *(
            [f'{RELAY_MARK} say this in the paragraph "{COVERAGE_HEADING}", {exactly} {NOT_SHOWN}']
            if ending
            else []
        ),
        *(
            [f"{RELAY_MARK} say this just before the sentence on the full report, {exactly} {word}"]
            if (word := results.own_word_sentences)
            else []
        ),
        *(
            [f'{RELAY_MARK} say this in the paragraph "Patches", {exactly} {sentence}']
            if (sentence := promise(cautioned, changing, unknown))
            else []
        ),
        *(
            [f'{RELAY_MARK} say this in the paragraph "Patches", {exactly} {caution}']
            if (caution := results.suite_sentence(plugin.PATCHES_INDEX_NAME))
            else []
        ),
        *(
            f"{RELAY_MARK} tell the user that a stage left {out.name}/{left} behind, that it can "
            "hold copies of their code, and to delete it before they build or test"
            for left in results.leftovers
        ),
        *([] if results.analysis.revision.get("versioned") else [not_in_git]),
        *(
            [f"{RELAY_MARK} say this to the user, {exactly} {warning}"]
            if (warning := plugin.worktree_warning(out))
            else []
        ),
        f"{RELAY_MARK} end your message with this sentence, {exactly} {ending or NOT_SHOWN}",
        *(finding_line(found, results) for found in records[:listed]),
    ]
    return [as_one_line(fact) for fact in facts]


def deliver(out: Path, products: dict[str, bytes], stamp_name: str, stamp: bytes) -> None:
    """Write the products to their names in `out`, and the stamp last. Refuse if a name is taken. On
    an error, undo what was written, and name on stderr what is left."""
    names = [*dict.fromkeys(name.partition("/")[0] for name in products), stamp_name]
    scratch = out / SCRATCH
    if scratch.is_dir() and not is_link(scratch):
        remove_tree(scratch)
    if taken := [name for name in names if os.path.lexists(out / name)]:
        refuse(
            f"the results cannot be written. Already in their place: {', '.join(taken)}. A write "
            f"that was stopped can be the cause. {NOT_REDACTED}"
        )
    scratch.mkdir()
    moved: list[str] = []
    try:
        for name, data in (*products.items(), (stamp_name, stamp)):
            (scratch / name).parent.mkdir(exist_ok=True)
            (scratch / name).write_bytes(data)
        for name in names:
            (scratch / name).replace(out / name)
            moved.append(name)
    except BaseException:
        for name in moved:
            with suppress(OSError):
                (out / name).replace(scratch / name)
        with suppress(OSError):
            remove_tree(scratch)
        if left := [name for name in (SCRATCH, *names) if os.path.lexists(out / name)]:
            sys.stderr.write(
                "attack_surface_report.py: this write did not finish. Left in "
                f"{out.name}: {', '.join(left)}. {NOT_REDACTED}\n"
            )
        raise
    with suppress(OSError):
        remove_tree(scratch)


def write(given: str, same_groups: Sequence[Sequence[str]]) -> list[str]:
    """Check everything, build every product, and deliver them with the stamp last."""
    out = output_directory(given)
    if stamped(out):
        refuse(f"the results are already written: an earlier write made {plugin.RESULTS_MD_NAME}")
    analysis = recorded(out)
    results = results_of(out, analysis, same_groups)
    stamp_name = plugin.revision_stamp_name(analysis.tag)
    copies = {f"{PATCHES}/{p.path.name}": copy_of(results, p) for p in results.patches if p.copied}
    if results.suite:
        copies[f"{PATCHES}/{SUITE_NAME}"] = results.suite.diff
    if results.indexed:
        copies[INDEX] = utf8(index_of(results))
    products = {
        plugin.RESULTS_MD_NAME: utf8(markdown_of(results)),
        plugin.JSONL_NAME: utf8(sarif.jsonl_text(results.records)),
        plugin.SARIF_NAME: json_file(log_of(results)),
        **copies,
    }
    facts = facts_of(results)
    deliver(out, products, stamp_name, json_file(stamp_of(results)))
    for text in results.unknown_cwes:
        sys.stderr.write(f"attack_surface_report.py: {text}\n")
    return facts


class Args(argparse.Namespace):
    """The parsed command line."""

    form: Literal["start", "check", "write"] = "start"
    stage: Sequence[int] = ()
    output_dir: str = ""
    same: Sequence[Sequence[str]] = ()


def run(args: Args, called: str) -> list[str]:
    if args.form == "start":
        return start(args.stage, called)
    if args.form == "check":
        return check(args.output_dir, called)
    if args.form == "write":
        return write(args.output_dir, args.same)
    return unreachable(args.form)


def main(argv: list[str], called: str) -> int:
    """`called` is this script's path as the caller spelled it."""
    parser = argparse.ArgumentParser(
        prog="attack_surface_report.py",
        description=(
            "Write the results of an attack surface analysis in the same formats as a scan's "
            "results."
        ),
        allow_abbrev=False,
    )
    forms = parser.add_subparsers(dest="form", metavar="command", required=True)
    output_dir_help = "the output directory that start made"
    starter = forms.add_parser(
        "start", help="make the output directory, and record what is analyzed", allow_abbrev=False
    )
    starter.add_argument(
        "--stage",
        action="append",
        type=int,
        choices=[stage.number for stage in Stage],
        default=[],
        help="a stage to include; give it once for each stage; the default is all three stages",
    )
    checker = forms.add_parser(
        "check", help="compare the checkout with what start recorded", allow_abbrev=False
    )
    checker.add_argument("output_dir", help=output_dir_help)
    writer = forms.add_parser(
        "write", help="write the results from the records that the stages left", allow_abbrev=False
    )
    writer.add_argument("output_dir", help=output_dir_help)
    writer.add_argument(
        "--same",
        action="append",
        type=lambda group: [name.strip() for name in group.split(",")],
        default=[],
        metavar="IDS",
        help="ids of findings that are one flaw, separated by commas; give it once for each group",
    )
    args = parser.parse_args(argv, namespace=Args())
    try:
        lines = run(args, called)
    except (AnalysisError, FindingError) as error:
        fault = str(error)
    except OSError as error:
        fault = f"could not read or write a file: {error}"
        if args.form == "write":
            fault += ". This command can be run again once the user has fixed that."
    else:
        print("\n".join(lines))
        return 0
    ending = f"\n{RELAY_AFTER_A_REFUSAL}" if args.form == "check" else ""
    sys.stderr.write(f"attack_surface_report.py: {fault}{ending}\n")
    return 1


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:], sys.argv[0]))
