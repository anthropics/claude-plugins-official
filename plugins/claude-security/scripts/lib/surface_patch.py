"""The patches of an attack surface analysis: each as its stage left it, the answer on it, which of
them may clash, and which of their files are not committed. A scan's "Suggest patches"
(patch_artifacts.py) also uses its check of what stands in a patch's way, its words on a git apply
that fails halfway, and its words on what a request to apply a patch means."""

from __future__ import annotations

import itertools
import os
import re
from collections import Counter
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final, NamedTuple

from . import git, plugin, unidiff
from .link import is_link
from .markdown import at_most, span
from .surface import Outcome
from .surface_dir import Stage, paths_in

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from typing import Literal

SUITE_NAME: Final = "regression.patch"


class Held(Enum):
    """Why a patch is held back. Each member has the prefix that a stage puts before the patch's
    name, and the words that tell the user why."""

    WAITING = ("waiting-", "it waits on your answer to a question")
    UNRESOLVED = (
        "unresolved-",
        (
            "its stage marked it unresolved, or its finding is unresolved, or no record confirms "
            "this patch's own claim to leave default behavior unchanged, or the record may speak "
            "of another patch for the same finding"
        ),
    )
    REFUTED = ("refuted-", "it or its finding was refuted, so do not apply it")

    def __init__(self, prefix: str, words: str) -> None:
        self.prefix = prefix
        self.words = words

    @classmethod
    def of(cls, name: str) -> Held | None:
        """The member whose prefix starts a patch's name, whatever follows it. None if no prefix
        does."""
        return next((held for held in cls if name.startswith(held.prefix)), None)

    @classmethod
    def by_claim(cls, answers: Iterable[Outcome | None]) -> Held | None:
        """Why a gate is held back, by the independent check's answers on its claim to leave default
        behavior unchanged: one for each finding that the gate names. REFUTED if one of them is
        REFUTED. Else None, if there is an answer, and each is CONFIRMED. Else UNRESOLVED: an answer
        that is missing, or that the check does not give, counts as unresolved, and so do no answers
        at all."""
        heard = set(answers)
        if Outcome.REFUTED in heard:
            return cls.REFUTED
        return None if heard == {Outcome.CONFIRMED} else cls.UNRESOLVED


ID: Final = plugin.PATCH_UNIT_ID_PATTERN
JOINT: Final = "[-_.]"
# The name goes into a printed command, so it holds nothing that a shell would act on.
PATCH_RE: Final = re.compile(
    rf"(?:{'|'.join(held.prefix for held in Held)})?"
    rf"(?P<ids>{ID}(?:{JOINT}{ID})*)(?:{JOINT}[A-Za-z0-9._-]*)?\.patch"
)
LOOSE: Final = (
    "its name is not in the form F101-words.patch, "
    "where each id is a confirmed finding of its stage"
)
NOT_READ: Final = "it is not a file inside the output directory, so it was not read"


WHY_UNTRIED: Final = "since git did not run, failed, was killed or took too long"
LEFT_HALFWAY: Final = "it may already have removed, changed or added files that the patch names."
WAY_BACK: Final = (
    "`git status` lists most of them, but not all. `git restore <file>` can bring a listed file "
    "back as you committed or staged it, and drops every other change in it: copy the file first "
    "if it holds changes of your own. It takes no added file away."
)
COPY_FIRST: Final = "commit your own changes or make a copy of them"
AFTER_APPLY: Final = (
    "After you apply a patch, run your project's tests. Asking Claude to apply it, to open a pull "
    "request for it, or to run the tests is not a request to install or set up anything beyond "
    "what your project's test command does itself. Claude should ask you before it installs or "
    "sets up anything more."
)
PATHS_NAMED: Final = 20
LFS_OID: Final = re.compile(rb"^\+oid sha256:[0-9a-f]{64}\r?$", re.MULTILINE)


class Way(Enum):
    """How a path is in a diff's way or, for POINTER, what the diff lacks for it. Each value is the
    words that tell the user, with a place for the paths."""

    FILE = "it needs a folder at {}, where a file stands"
    NO_FOLDER = "it needs a folder at {}, where something else stands"
    FOLDER = "it names a file at {}, where a folder stands"
    BOTH = "it needs a folder at {}, and names a file there too"
    CASE = "it names a file and needs a folder at {}, which some file systems take for one name"
    POINTER = "for {} it holds a Git LFS pointer, and not the new content that the pointer names"

    def told(self, paths: tuple[str, ...]) -> str:
        """The member's words, with the first PATHS_NAMED of `paths` as the user reads them, and
        how many more there are."""
        return self.value.format(at_most(PATHS_NAMED, [span(path) for path in paths]))


class Tried(Enum):
    """Whether one patch, or several together, would apply. For one patch, git's answer, and
    in_the_way()'s answer. For several, git's answer in the orders that would_apply() tries, and its
    check of their paths. The last two members are suite_of()'s, on the paths of a regression suite
    that git accepts. suite_of() says when it also gives NO_ANSWER. Each value is the words that
    tell the user about one patch."""

    APPLIES = ""
    REFUSED = "git apply --check refuses it"
    BLOCKED = "git apply can fail halfway on it, though git apply --check passes"
    NO_ANSWER = f"it could not be tried, {WHY_UNTRIED}"
    NOT_CHECKED = (
        f"{NO_ANSWER}: run git apply --check on it from the folder that was analyzed to see what "
        "git says"
    )
    NOT_NEW = "it names a path that already exists"
    UNSEEN = "its paths could not be checked, since the project is not the top of its repository"

    @classmethod
    def of(cls, fits: bool | None) -> Tried:
        """The member for lib.git's answer: True, False or None."""
        return cls.NO_ANSWER if fits is None else cls.APPLIES if fits else cls.REFUSED

    @classmethod
    def on_disk(
        cls, blockers: Mapping[Way, tuple[str, ...]] | None
    ) -> Literal[Tried.NO_ANSWER, Tried.BLOCKED, Tried.APPLIES]:
        """The member for a patch that git accepts, by in_the_way()'s answer on it."""
        return cls.NO_ANSWER if blockers is None else cls.BLOCKED if blockers else cls.APPLIES

    def told(self, said: tuple[str, ...]) -> str:
        """The member's words, with `said` after them, if it holds anything."""
        shown = "; ".join(said)
        return self.value + (f": {shown}" if shown else "")


class Patch(NamedTuple):
    """A file in a stage's folder of patches, as its stage left it. `applies` is the answer on it
    alone. `said` holds git's first line as a code span, most often the cause, if git refuses it
    and gives one, or the words on the paths that are in its way.
    `under` maps each confirmed finding in the patch's name to the finding that the report shows it
    under. It is empty for a patch that is not copied into attack-surface-patches/. `ids` are its
    keys, and `owners` its values, each once."""

    path: Path
    stage: Stage
    diff: bytes
    held: Held | None
    applies: Tried
    said: tuple[str, ...]
    under: dict[str, str]

    @property
    def ids(self) -> list[str]:
        return list(self.under)

    @property
    def owners(self) -> list[str]:
        return list(dict.fromkeys(self.under.values()))

    @property
    def copied(self) -> bool:
        return bool(self.under)

    def shown(self, out: Path) -> str:
        """Its name in attack-surface-patches/, or, where it is not copied, its path below the
        output directory."""
        return self.path.name if self.copied else self.path.relative_to(out).as_posix()

    @property
    def ready(self) -> bool:
        """Whether it is ready to apply: copied, not held back, and accepted by git on its own, with
        nothing in its way."""
        return self.copied and self.held is None and self.applies is Tried.APPLIES

    @property
    def reason(self) -> str:
        """Why the patch is set aside. Empty for one that is ready to apply."""
        held = self.held.words if self.held else ""
        loose = "" if self.copied or (self.held and PATCH_RE.fullmatch(self.path.name)) else LOOSE
        return "; ".join(filter(None, (held, loose, self.applies.told(self.said))))


class Suite(NamedTuple):
    """Stage 1's regression suite. `applies` and `said` are as a Patch's, but for two members that
    suite_of() gives a suite alone. Under NOT_NEW, `said` holds one path that the suite names and
    that already exists, as a code span. Under UNSEEN, it is empty. suite_of() says when each
    stands, and has cases of its own for NO_ANSWER."""

    diff: bytes
    applies: Tried
    said: tuple[str, ...]


class Clash(NamedTuple):
    """The names of patches, and the advice for the user on applying them. In a pair, the second may
    be a refuted patch."""

    names: tuple[str, ...]
    advice: str


SAME: Final = "are the same change: one of them is enough"
SECOND_REFUTED: Final = (
    "and the independent check refuted the second or its finding: "
    f"read what {plugin.RESULTS_MD_NAME} says of the findings of both before you apply the first"
)
SAME_AS_REFUTED: Final = f"are the same change, {SECOND_REFUTED}"
DISPUTED: Final = f"change the same file or path, {SECOND_REFUTED}"
PAIR: Final = (
    "may clash. Read both first. If they fix the same flaw, choose one of them. Otherwise, apply "
    "one of them, try the other, look at what each changed, and carry over by hand what git refuses"
)
ALL: Final = (
    "do not all apply together, and git may put a change in the wrong place: apply them one at a "
    "time, look at what each changed, and carry over by hand what git refuses"
)
ONE_AT_A_TIME: Final = "apply them one at a time, and look at what each changed"
UNTRIED: Final = f"could not be tried together, {WHY_UNTRIED}: {ONE_AT_A_TIME}"
OUT_OF_TIME: Final = (
    "were not all tried with each other before the time set for such trials ran out: "
    f"{ONE_AT_A_TIME}"
)
UNTRIED_REFUTED: Final = (
    f"may change the same file or path and could not be tried together, {SECOND_REFUTED}"
)


def at(root: str, path: str) -> Path:
    """Where `path`, a name as git spells it, lies on disk below `root`."""
    return Path(root, git.for_disk(path))


def would_apply(root: str, *diffs: bytes) -> Tried:
    """Whether the diffs apply together on the target: git apply --check accepts them all at once,
    in this order, in the reverse order and with each of them last, no two of them make the same new
    path, none renames or copies a file that another names, none makes a file where another needs a
    new folder, and no two of them name one path in two cases (a renamed or copied file counts by
    its old path). Otherwise they may clash. Three or more can still clash in an order that is not
    tried. New paths that differ only in case count as the same path. For one diff alone: git's
    answer, or BLOCKED where in_the_way() names a path. NO_ANSWER where git gave no answer, or no
    list of a diff's paths. It changes nothing."""
    each_last = ((*diffs[:n], *diffs[n + 1 :], diff) for n, diff in enumerate(diffs))
    for order in dict.fromkeys((diffs, diffs[::-1], *each_last)):
        answer = Tried.of(git.check_patch_bytes(root, b"\n".join(order)))
        if answer is not Tried.APPLIES:
            return answer
        if len(diffs) == 1:
            return Tried.on_disk(in_the_way(root, diffs[0]))
    made: Counter[str] = Counter()
    made_by: dict[str, int] = {}
    named: Counter[str] = Counter()
    caseless: Counter[str] = Counter()
    moved_away: set[str] = set()
    for number, diff in enumerate(diffs):
        old, new = git.patch_paths(root, diff, before=True), git.patch_paths(root, diff)
        if old is None or new is None:
            return Tried.NO_ANSWER
        added = {path.casefold() for path in new if not os.path.lexists(at(root, path))}
        made.update(added)
        made_by.update(dict.fromkeys(added, number))
        named.update(old)
        caseless.update({path.casefold() for path in old})
        moved_away |= old - new
    clash = (
        any(count > 1 for count in made.values())
        or any(named[path] > 1 for path in moved_away)
        or any(caseless[path.casefold()] > count for path, count in named.items())
        or any(
            made_by.get(str(folder), own) != own
            for path, own in made_by.items()
            for folder in PurePosixPath(path).parents
        )
    )
    return Tried.REFUSED if clash else Tried.APPLIES


def pointers_in(root: str, diff: bytes) -> frozenset[str] | None:
    """The files of each part of `diff` that holds a new Git LFS pointer, where git's attributes at
    `root` give the file the filter `lfs`, git gives no answer on them or no list of the whole
    diff's paths, or `diff` names a .gitattributes file. A `diff --git` line opens a part, so a diff
    with no such line is one part. None where git gave no list of such a part's paths."""
    found: frozenset[str] = frozenset()
    for part in re.split(rb"(?m)^(?=%b)" % unidiff.DIFF_HEADER.encode("ascii"), diff):
        if not LFS_OID.search(part):
            continue
        named = git.patch_paths(root, part)
        if named is None:
            return None
        found |= named
    asked = ("check-attr", "-z", "filter", "--", *map(git.argument, sorted(found)))
    paths = (paths_of(root, diff) if found else None) or ()
    known = paths and not any(PurePosixPath(path).name == ".gitattributes" for path in paths)
    said = (git.run(root, *asked, exact=True) if known else None) or ""
    fields = said.split("\0")
    other = {path for path, value in zip(fields[::3], fields[2::3]) if value != "lfs"}
    return found - other


def in_the_way(root: str, diff: bytes) -> dict[Way, tuple[str, ...]] | None:
    """The paths that are in `diff`'s way, by Way, and sorted, with names that differ only in case
    side by side. FILE: it needs a folder there, and the disk has a regular file. NO_FOLDER: it
    needs a folder there, and the disk has something else that is neither a folder nor a link to
    one. FOLDER: it names a file there, and the disk has a folder that is no link. BOTH, for the
    others: it both names the path as a file and needs it as a folder. CASE: it needs a folder where
    the disk has nothing or a link to a folder, and does not name that path as a file, but names a
    file that str.casefold() makes equal to it. CASE gives the folder's name and each such file's. A
    name under CASE can stand under another Way too. POINTER: it gives the file a new Git LFS
    pointer, by pointers_in(). A renamed or copied file counts by its new path. Empty if there is
    none. None where git gave no list of the diff's paths, or pointers_in() gives None."""
    paths = git.patch_paths(root, diff)
    if paths is None:
        return None
    pointers = pointers_in(root, diff)
    if pointers is None:
        return None
    folders = {str(folder) for path in paths for folder in PurePosixPath(path).parents}
    no_folder = {
        path
        for path in folders
        if os.path.lexists(place := at(root, path)) and not os.path.isdir(place)
    }
    real = {
        path
        for path in paths | folders
        if os.path.isdir(place := at(root, path)) and not is_link(place)
    }
    regular = {
        path for path in no_folder if os.path.isfile(place := at(root, path)) and not is_link(place)
    }
    needed = folders - real - no_folder
    files = {path.casefold() for path in paths}
    folded = {path.casefold() for path in needed - paths if path.casefold() in files}
    case = {path for path in needed | paths if path.casefold() in folded}
    ways = {
        Way.FILE: regular,
        Way.NO_FOLDER: no_folder - regular,
        Way.FOLDER: paths & real,
        Way.BOTH: needed & paths,
        Way.CASE: case,
        Way.POINTER: pointers,
    }
    return {
        way: tuple(sorted(found, key=lambda path: (path.casefold(), path)))
        for way, found in ways.items()
        if found
    }


def paths_of(root: str, diff: bytes) -> frozenset[str] | None:
    """Each path that the patch names, with both the old path and the new one of a file that it
    renames or copies. None where git gave no list."""
    old = git.patch_paths(root, diff, before=True)
    new = None if old is None else git.patch_paths(root, diff)
    return None if old is None or new is None else old | new


def in_place(root: str, diff: bytes) -> str | None:
    """A path that `diff` names and at which something stands on disk. Empty if there is none. None
    where git gave no list of the diff's paths, or an empty one. Where `root` lies below the top of
    a repository, git lists paths from that top, and they are looked for in the wrong folder."""
    named = paths_of(root, diff)
    if not named:
        return None
    there = (path for path in named if os.path.lexists(at(root, path)))
    return min(there, default="")


def paths_and_folders(root: str, diff: bytes) -> tuple[frozenset[str], frozenset[str]] | None:
    """The paths that a diff names, old and new, with case folded as would_apply() folds it, and the
    folders above them. None where git gave no list."""
    named = paths_of(root, diff)
    if named is None:
        return None
    paths = frozenset(path.casefold() for path in named)
    return paths, frozenset(str(folder) for path in paths for folder in PurePosixPath(path).parents)


def may_meet(root: str, one: bytes, other: bytes) -> bool:
    """Whether two diffs name a common path, or one names a folder above a path of the other, with
    paths folded as would_apply() folds them. Two diffs that do neither change files apart, and
    would_apply() finds no clash in their paths. True where git gave no list."""
    first, second = paths_and_folders(root, one), paths_and_folders(root, other)
    if first is None or second is None:
        return True
    (paths, folders), (their_paths, their_folders) = first, second
    return bool(paths & (their_paths | their_folders) or folders & their_paths)


def groups_of(root: str, joint: Sequence[tuple[str, bytes]]) -> list[list[tuple[str, bytes]]]:
    """The patches in groups, in the order given. Two that may meet stand in one group, so a group
    can also hold two that do not, joined through a third."""
    groups: list[set[int]] = []
    for index, (_, diff) in enumerate(joint):
        meets = [
            group for group in groups if any(may_meet(root, diff, joint[each][1]) for each in group)
        ]
        groups = [*(group for group in groups if group not in meets), {index}.union(*meets)]
    return [[joint[each] for each in sorted(group)] for group in sorted(groups, key=min)]


def not_committed(root: str, paths: Iterable[str]) -> set[str] | None:
    """Those of `paths` that are not committed as they are now. `root` must be the top of its
    repository. A file counts as committed only where `git ls-files -v` lists it with an "H", and
    `git status` says nothing of it. A path with nothing on disk counts only where `git status`
    names it, or `git ls-files -v` lists it with another letter. None where a call gives no
    answer."""
    asked = set(paths)
    if not asked:
        return set()
    literal = "--literal-pathspecs"
    named = ("--", *map(git.argument, sorted(asked)))
    listed = git.run(root, literal, "ls-files", "-v", "-z", *named)
    status = git.run(root, literal, "status", "--porcelain=v1", "-z", "--no-renames", *named)
    if listed is None or status is None:
        return None
    there = {path for path in asked if os.path.lexists(at(root, path))}
    letters = {entry[2:]: entry[:1] for entry in listed.split("\0")[:-1]}
    changed = {entry[3:] for entry in status.split("\0")[:-1]}
    checked = {path for path, letter in letters.items() if letter == "H"}
    return ((there | asked & letters.keys()) - checked) | (asked & changed)


def patches_in(out: Path, stage: Stage) -> list[Path]:
    """What the stage's folder of patches holds, in order, but no name that starts with a dot. A
    stage with no such folder has none."""
    if not stage.patch_folder:
        return []
    folder = out / stage.folder / stage.patch_folder
    return sorted(path for path in paths_in(folder) if not path.name.startswith("."))


def ways_told(blockers: Mapping[Way, tuple[str, ...]]) -> tuple[str, ...]:
    """in_the_way()'s answer in words, for Tried.BLOCKED.told()."""
    return tuple(way.told(paths) for way, paths in blockers.items())


def alone(path: Path, root: str, diff: bytes) -> tuple[Tried, tuple[str, ...]]:
    """A Patch's `applies` and `said`, for the file at `path`, below `root`, which holds `diff`."""
    relative = path.relative_to(root)
    checked = git.check_patch_file(root, relative)
    if checked is None:
        return Tried.NOT_CHECKED, ()
    fits, said = checked
    if fits:
        blockers = in_the_way(root, diff)
        return Tried.on_disk(blockers), ways_told(blockers or {})
    return Tried.REFUSED, (span(said),) if said else ()


def suite_of(path: Path, root: str) -> Suite:
    """The regression suite in the file at `path`. Where alone() says that it applies or is blocked,
    its state is decided in this order. UNSEEN: git names a top that is not the project. NO_ANSWER:
    git names no top, though the project's folder or one above it holds a .git; or git lists no path
    of the suite. NOT_NEW: one of its paths exists. Else, and where alone() says anything else,
    alone()'s answer stands. So NOT_NEW and UNSEEN say that git accepts it."""
    diff = path.read_bytes()
    applies, said = alone(path, root, diff)
    if applies not in {Tried.APPLIES, Tried.BLOCKED}:
        return Suite(diff, applies, said)
    top = git.toplevel(root)
    if top and not git.is_top(root, top):
        return Suite(diff, Tried.UNSEEN, ())
    held = not top and git.holder_of(root)
    there = None if held else in_place(root, diff)
    if there is None:
        return Suite(diff, Tried.NO_ANSWER, ())
    if there:
        return Suite(diff, Tried.NOT_NEW, (span(there),))
    return Suite(diff, applies, said)


def claims_of(
    names: Iterable[str], stated: Mapping[str, Outcome | None]
) -> dict[str, Outcome | None]:
    """The answer that patch_of() takes for each id in `stated`: its outcome there, or None in place
    of a CONFIRMED where more than one of `names`, with no prefix and in a patch's form, names the
    id. None too in place of a REFUTED where one of `names`, with the prefix refuted- and in a
    patch's form, names it. `names` are the names in stage 1's folder of patches, but for one with a
    prefix that was not read. `stated` holds each confirmed stage 1 finding's `gate`, and REFUTED
    for each other stage 1 id whose record refuses_its_gate()."""
    found = ((Held.of(name), PATCH_RE.fullmatch(name)) for name in names)
    named = [(held, set(re.split(JOINT, match["ids"]))) for held, match in found if match]
    bare = Counter(each for held, ids in named if not held for each in ids)
    refuted = {each for held, ids in named if held is Held.REFUTED for each in ids}
    return {
        name: None
        if (gate is Outcome.CONFIRMED and bare[name] > 1)
        or (gate is Outcome.REFUTED and name in refuted)
        else gate
        for name, gate in stated.items()
    }


def patch_of(
    path: Path,
    stage: Stage,
    root: str,
    under: Mapping[str, str],
    claims: Mapping[str, Outcome | None],
) -> Patch:
    """One file in a stage's folder of patches. For each confirmed finding, `under` gives the one
    that the report shows it under. `claims` is what claims_of() gives. A stage 1 patch is held as
    refuted where the answer for one of its ids is REFUTED, else by its prefix. Else, where its ids
    are each a confirmed finding of the stage, as unresolved unless each answer is CONFIRMED."""
    match, diff = PATCH_RE.fullmatch(path.name), path.read_bytes()
    given = re.split(JOINT, match["ids"]) if match else []
    fit = all(name in under and stage.holds(name) for name in given)
    held = Held.of(path.name)
    if given and stage is Stage.ONE:
        claim = Held.by_claim(claims.get(name) for name in given)
        if claim is Held.REFUTED or (fit and not held):
            held = claim
    ids = given if fit and held is not Held.REFUTED else []
    applies, said = alone(path, root, diff)
    return Patch(path, stage, diff, held, applies, said, {name: under[name] for name in ids})


def change_of(diff: bytes) -> bytes:
    """`diff` without the `diff --git` lines that end it with no change after them, and any white
    space after those."""
    lines, header = diff.split(b"\n"), unidiff.DIFF_HEADER.encode("ascii")
    ending = itertools.takewhile(
        lambda line: line.startswith(header) or not line.strip(), reversed(lines)
    )
    tail = list(ending)
    while tail and not tail[-1].startswith(header):
        tail.pop()
    return b"\n".join([*lines[: -len(tail)], b""]) if tail else diff


OPENS_A_DIFF: Final = re.compile(rb"^[ \t]*(?:diff --git |---[ \t]|\+\+\+[ \t]|@@ -)", re.MULTILINE)


def with_refuted(root: str, diff: bytes, against: Patch, in_time: Callable[[], bool]) -> str:
    """The advice on a patch and a refuted one, by the first of these that holds. The same change:
    they are told as such. alone() got no answer on the refuted one: they could not be tried.
    Where the refuted one does not apply alone: none if no line of it opens a diff or a hunk; they
    could not be tried if the time is up, or if the two may meet; else none. Where it applies alone:
    none if the two cannot meet; they could not be tried if the time is up; else by would_apply() on
    the two: none where they apply together; where it gives no answer, they could not be tried; else
    they change the same file or path."""
    change = change_of(against.diff)
    if diff == change:
        return SAME_AS_REFUTED
    if against.applies in {Tried.NO_ANSWER, Tried.NOT_CHECKED}:
        return UNTRIED_REFUTED
    if against.applies is not Tried.APPLIES:
        if not OPENS_A_DIFF.search(against.diff):
            return ""
        return UNTRIED_REFUTED if not in_time() or may_meet(root, diff, against.diff) else ""
    if not may_meet(root, diff, change):
        return ""
    answer = would_apply(root, diff, change) if in_time() else Tried.NO_ANSWER
    if answer is Tried.APPLIES:
        return ""
    return UNTRIED_REFUTED if answer is Tried.NO_ANSWER else DISPUTED


def clashes_of(
    root: str,
    out: Path,
    patches: Sequence[Patch],
    suite: Suite | None,
    in_time: Callable[[], bool],
) -> list[Clash]:
    """Which patches may clash, or could not be tried together. Each patch that applies alone and is
    not refuted counts. A refuted patch counts whether it applies alone or not: see with_refuted().
    The regression suite counts where it applies alone, and under NOT_NEW and UNSEEN. Once `in_time`
    says no, no more patches are tried together, and a group with pairs that are left is told as one
    that ran out of time. Two patches that make the same change, in one group, or a patch and a
    refuted one, are still told as such. The suite is never held against a refuted patch."""
    usable = [(patch.shown(out), patch) for patch in patches if patch.applies is Tried.APPLIES]
    unrefuted = [
        (name, change_of(patch.diff)) for name, patch in usable if patch.held is not Held.REFUTED
    ]
    refuted = [(patch.shown(out), patch) for patch in patches if patch.held is Held.REFUTED]
    disputed = [
        Clash((name, other), advice)
        for name, diff in unrefuted
        for other, against in refuted
        if (advice := with_refuted(root, diff, against, in_time))
    ]
    taken = {Tried.APPLIES, Tried.NOT_NEW, Tried.UNSEEN}
    tests = [(SUITE_NAME, change_of(suite.diff))] if suite and suite.applies in taken else []
    told: list[Clash] = []
    for group in groups_of(root, [*unrefuted, *tests]):
        names = tuple(name for name, _ in group)
        pairs = list(itertools.combinations(group, 2))
        same = [(one, other) for (one, first), (other, second) in pairs if first == second]
        apart = [
            ((one, other), first, second)
            for (one, first), (other, second) in pairs
            if first != second
        ]
        told += [Clash(pair, SAME) for pair in same]
        several = len(group) > 2 and in_time()
        changes = dict.fromkeys(diff for _, diff in group)
        together = would_apply(root, *changes) if several else None
        if together is Tried.NO_ANSWER:
            told.append(Clash(names, UNTRIED))
            continue
        tried = [
            (pair, would_apply(root, first, second))
            for pair, first, second in itertools.takewhile(lambda _: in_time(), apart)
        ]
        told += [
            Clash(pair, UNTRIED if answer is Tried.NO_ANSWER else PAIR)
            for pair, answer in tried
            if answer is not Tried.APPLIES
        ]
        if len(tried) < len(apart):
            told.append(Clash(names, OUT_OF_TIME))
        elif together is Tried.REFUSED and all(answer is not Tried.REFUSED for _, answer in tried):
            copies = {other for _, other in same}
            told.append(Clash(tuple(name for name in names if name not in copies), ALL))
    return [*told, *disputed]
