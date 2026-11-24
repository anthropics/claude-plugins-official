"""A finding explained for the developer who reads the review: the explainer agent's file, checked,
and its diagram as a Mermaid flowchart."""

from __future__ import annotations

import enum
import errno
import os
import re
from typing import TYPE_CHECKING, NamedTuple, TypeVar

from . import gfm, link, plain, plugin, strictjson
from .sarif import sentence
from .strictjson import clean, is_list, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from .strictjson import JsonMap

MOST_BYTES = 64 * 1024
# The most characters that a text may hold before it is escaped, where _LIMITS names no other.
_TEXT_LIMIT = 480
# `fix` can give the scan's whole recommendation, which runs long.
_LIMITS = {"headline": 160, "what": _TEXT_LIMIT, "why": _TEXT_LIMIT, "fix": 960}
_LABEL_LIMIT = 48
BAD_LABEL = "a label that is too long, holds an invisible character or cannot be drawn as typed"

_MOST_STEPS = 6
_FEWEST_BOXES, _MOST_BOXES, _MOST_ARROWS = 3, 8, 12
# Mermaid draws all of this as typed inside a quoted label.
_LABEL_RE = re.compile(r"(?:[\w .,/()'=?*-]|(?<=\w)::(?=\w))+")
# Mermaid reads a line that holds this as a direction statement, even inside a label.
_DIRECTION_RE = re.compile(r"direction\s+(?:TB|BT|RL|LR|TD)", re.IGNORECASE)
SETTINGS = (
    '%%{init: {"flowchart": {"rankSpacing": 24, "nodeSpacing": 32}, '
    '"themeVariables": {"fontSize": "14px"}}}%%'
)
_GREY, _RED = "#8c959f", "#cf222e"


class Flaw(NamedTuple):
    """Why an explanation, or one part of it, is not used, in words for the log."""

    reason: str


_Part = TypeVar("_Part")


def _every(parts: Iterable[_Part | Flaw]) -> list[_Part] | Flaw:
    """Every part, or the first Flaw among them."""
    found: list[_Part] = []
    for part in parts:
        if isinstance(part, Flaw):
            return part
        found.append(part)
    return found


@enum.unique
class Kind(enum.Enum):
    """The kinds of box. Each carries the shape around its label, its style, and its entry in the
    legend, if it has one."""

    ACTOR = ('(["{}"])', f"fill:none,stroke:{_GREY},stroke-width:2px", "")
    VULNERABLE_CODE = (
        '["{}"]',
        f"fill:{_RED},fill-opacity:0.12,stroke:{_RED},stroke-width:2px",
        "Red box: vulnerable code",
    )
    MISSING_CHECK = (
        '["{}"]',
        f"fill:none,stroke:{_RED},stroke-width:2px,stroke-dasharray:5 5",
        "Dashed red box: missing safeguard",
    )
    ASSET = ('("{}")', f"fill:none,stroke:{_GREY},stroke-width:2px", "")
    COMPONENT = ('["{}"]', f"fill:none,stroke:{_GREY}", "")

    shape: str
    style: str
    legend: str

    def __init__(self, shape: str, style: str, legend: str) -> None:
        self.shape = shape
        self.style = style
        self.legend = legend

    @property
    def key(self) -> str:
        """Its name in the agent's file and in the diagram's classes."""
        return self.name.lower()


def is_label(text: str) -> bool:
    """Whether `text` is not empty, is short enough for a label, holds no invisible character, and
    Mermaid draws it as typed in quotes."""
    return (
        len(text) <= _LABEL_LIMIT
        and _LABEL_RE.fullmatch(text) is not None
        and not gfm.INVISIBLE_RE.search(text)
        and not _DIRECTION_RE.search(text)
    )


def _objects_at(raw: JsonMap, key: str) -> list[JsonMap] | Flaw:
    """The objects of the array at `key`, none where the key is absent or null; a Flaw for any
    other value, and for an array that holds anything but objects."""
    value = raw.get(key)
    found = [entry for entry in value if is_map(entry)] if is_list(value) else []
    if value is None or (is_list(value) and len(found) == len(value)):
        return found
    return Flaw(f"{key} is not a list of objects")


def _text_at(
    raw: JsonMap, key: str, limit: int = _TEXT_LIMIT, *, closed: bool = True
) -> str | Flaw:
    """The text at `key` as words and code spans, or the rule that it breaks. Unless `closed`, it
    loses the full stops and spaces at its end."""
    value = raw.get(key)
    if value is not None and not is_str(value):
        return Flaw(f"{key} is not text")
    text = gfm.plain_line(clean(value))
    if not text.strip(". "):
        return Flaw(f"{key} is empty")
    if len(text) > limit:
        return Flaw(f"{key} has more than {limit} characters")
    if strictjson.has_lone_surrogate(text):
        return Flaw(f"{key} holds half of a surrogate pair")
    return gfm.inert(text if closed else text.rstrip(". "))


class Box(NamedTuple):
    """One box of a diagram."""

    label: str
    kind: Kind


class Arrow(NamedTuple):
    """One arrow of a diagram. Each end is a box's index, and both ends may be one box."""

    start: int
    end: int
    label: str


class Diagram(NamedTuple):
    """The system under attack as a small graph. Diagram.of gives one that breaks no rule, which
    is what drawn() takes for granted."""

    boxes: list[Box]
    arrows: list[Arrow]

    @classmethod
    def of(cls, raw: object) -> Diagram | Flaw | None:
        """The diagram the agent named, or the first rule that it breaks; None for null."""
        if raw is None:
            return None
        if not is_map(raw):
            return Flaw("it is not an object")
        lists = _every(_objects_at(raw, key) for key in ("nodes", "edges"))
        if isinstance(lists, Flaw):
            return lists
        nodes, edges = lists
        kinds = {kind.key: kind for kind in Kind}
        position = {clean(node.get("id")): at for at, node in enumerate(nodes)}
        ends = [(clean(edge.get("from")), clean(edge.get("to"))) for edge in edges]
        if "" in position or len(position) < len(nodes):
            return Flaw("a box with no id, or two boxes with one id")
        if any(clean(node.get("kind")) not in kinds for node in nodes):
            return Flaw("a box of no known kind")
        if any(end not in position for pair in ends for end in pair):
            return Flaw("an arrow to or from no box")
        graph = cls(
            [Box(clean(node.get("label")), kinds[clean(node.get("kind"))]) for node in nodes],
            [
                Arrow(position[start], position[end], clean(edge.get("label")))
                for (start, end), edge in zip(ends, edges)
            ],
        )
        return graph.flaw() or graph

    def flaw(self) -> Flaw | None:
        """The first rule on its size and labels that the graph breaks; None for none."""
        labels = [box.label for box in self.boxes] + [arrow.label for arrow in self.arrows]
        rules = (
            (_FEWEST_BOXES <= len(self.boxes) <= _MOST_BOXES, "too few or too many boxes"),
            (len(self.arrows) <= _MOST_ARROWS, "too many arrows"),
            (all(map(is_label, labels)), BAD_LABEL),
        )
        return next((Flaw(broken) for holds, broken in rules if not holds), None)

    def drawn(self) -> str:
        """The diagram as a fenced Mermaid flowchart. If it has a red box, one line under it
        explains the red outlines in use. A line that starts or ends at a missing safeguard is
        dotted and has no arrowhead."""
        kinds = [kind for kind in Kind if any(box.kind is kind for box in self.boxes)]
        boxes = (
            f"  n{at}{kind.shape.format(label)}:::{kind.key}"
            for at, (label, kind) in enumerate(self.boxes)
        )
        absent = {at for at, box in enumerate(self.boxes) if box.kind is Kind.MISSING_CHECK}
        arrows = (
            f'  n{start} {"-.-" if absent & {start, end} else "-->"}|"{label}"| n{end}'
            for start, end, label in self.arrows
        )
        styles = (f"  classDef {kind.key} {kind.style}" for kind in kinds)
        chart = gfm.fenced(
            "\n".join([SETTINGS, "flowchart TD", *boxes, *arrows, *styles]), "mermaid"
        )
        legend = " · ".join(kind.legend for kind in kinds if kind.legend)
        return f"{chart}\n<sub>{legend}</sub>" if legend else chart


def _step_of(raw: JsonMap) -> str | Flaw:
    """One step as a pair of sentences, its actor in bold, or the rule that it breaks."""
    texts = _every(_text_at(raw, key) for key in ("actor", "action", "detail"))
    if isinstance(texts, Flaw):
        return texts
    actor, action, detail = texts
    return f"**{actor}** {sentence(action)} {detail}"


def _steps_of(raw: JsonMap) -> list[str] | Flaw:
    """Each step of the attack, or the rule that the steps break; none where the agent gave none."""
    steps = _objects_at(raw, "steps")
    if isinstance(steps, Flaw):
        return steps
    if len(steps) > _MOST_STEPS:
        return Flaw(f"more than {_MOST_STEPS} steps")
    return _every(map(_step_of, steps))


class Explanation(NamedTuple):
    """The agent's answer on one finding, checked."""

    headline: str
    what: str
    why: str
    fix: str
    # Why no fix is offered, as a sentence; empty when that does not apply.
    no_fix: str
    steps: list[str]
    diagram: Diagram | None
    # Each part that broke a rule and is dropped, with the rule, in words for the log.
    dropped: list[str]

    @classmethod
    def of(cls, raw: JsonMap) -> Explanation | Flaw:
        """The agent's answer. A Flaw when the headline, what, why or fix breaks a rule. If another
        part breaks a rule, only that part is dropped."""
        texts = _every(
            _text_at(raw, key, limit, closed=key != "headline") for key, limit in _LIMITS.items()
        )
        if isinstance(texts, Flaw):
            return texts
        headline, what, why, fix = texts
        dropped: list[str] = []

        def kept(name: str, part: _Part | Flaw, without: _Part) -> _Part:
            if isinstance(part, Flaw):
                dropped.append(f"{name} ({part.reason})")
                return without
            return part

        given = raw.get("no_fix")
        blank = given is None or (is_str(given) and not given.strip())
        no_fix = "" if blank else _text_at(raw, "no_fix")
        return cls(
            headline,
            what,
            why,
            fix,
            sentence(kept("its reason for no fix", no_fix, "")),
            kept("its steps", _steps_of(raw), []),
            kept("its diagram", Diagram.of(raw.get("diagram")), None),
            dropped,
        )


def folder_of(report_dir: Path) -> Path | Flaw:
    """The report's explanations folder, or why no explanation is read from the report."""
    folder = report_dir / plugin.EXPLANATIONS_DIR_NAME
    if link.is_link(folder):
        return Flaw(f"the report's {folder.name} folder is a link")
    return folder if os.path.isdir(folder) else Flaw(f"the report has no {folder.name} folder")


def read(folder: Path, finding: str) -> Explanation | Flaw:
    """The explanation that `folder` holds for the finding with this id, or why none is used."""
    try:
        raw = strictjson.loads(plain.read_text(folder / f"{finding}.json", MOST_BYTES))
    except FileNotFoundError:
        return Flaw("its file is missing")
    except OSError as error:
        if error.errno == errno.EFBIG:
            return Flaw(f"its file holds more than {MOST_BYTES} bytes")
        return Flaw("its file is not a regular file that can be read")
    except ValueError:
        return Flaw("its file is not strict JSON in UTF-8, or is nested too deeply")
    if not is_map(raw) or raw.get("id") != finding:
        return Flaw("its file names another finding, or none")
    return Explanation.of(raw)
