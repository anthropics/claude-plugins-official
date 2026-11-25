"""The state of a running scan."""

from __future__ import annotations

import enum
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple, TypedDict

from lib.finding import PANEL_KEEP_QUORUM, Severity

from . import words

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from .atlas import Atlas

from dataclasses import asdict

LENSES = ("reachability", "impact", "defenses")
SEVERITIES = tuple(Severity.__members__)
_RECENT_TOUCHES = 600
_RECENT_NOTES = 400


class Stage(str, enum.Enum):
    """The stages of a scan, in the order in which they begin."""

    SETUP = "Setup"
    INVENTORY = "Inventory"
    SWEEP = "Sweep"
    RESEARCH = "Research"
    PANEL = "Panel"
    REPORT = "Report"


_OPENINGS = {
    Stage.SETUP: "Starting Claude Code",
    Stage.INVENTORY: "Dividing the repository into components",
    Stage.SWEEP: "Sweeping the code that the components do not cover",
    Stage.RESEARCH: "Researchers are hunting through the code",
    Stage.PANEL: "Verifiers try to disprove each candidate",
    Stage.REPORT: "Writing the report",
}


class State(str, enum.Enum):
    """Where a stage, an agent or the scan itself stands."""

    WAITING = "waiting"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class Vote(str, enum.Enum):
    """A verifier's answer on a candidate."""

    PENDING = "pending"
    CONFIRM = "confirm"
    REFUTE = "refute"
    ABSTAIN = "abstain"


class Look(str, enum.Enum):
    """How an agent looked at the code."""

    SEARCH = "search"
    READ = "read"


class Outcome(str, enum.Enum):
    """What the panel made of a candidate."""

    TESTING = "testing"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    UNSETTLED = "unsettled"


@dataclass
class Target:
    """What is scanned, how, and inside which limits."""

    name: str
    mode: str
    effort: str
    scope: list[str] = field(default_factory=list)
    branch: str = ""
    commit: str = ""
    dirty: bool = False
    model: str = ""
    version: str = ""
    sandboxed: bool = False
    hosts: list[str] = field(default_factory=list)
    writable: list[str] = field(default_factory=list)


@dataclass
class Result:
    """How the scan ended."""

    state: State = State.RUNNING
    message: str = ""
    report_dir: str = ""
    files: list[str] = field(default_factory=list)
    verification: str = ""


@dataclass
class Phase:
    stage: Stage
    state: State = State.WAITING
    started: float | None = None
    ended: float | None = None


@dataclass
class Component:
    name: str
    language: str
    plots: Sequence[int]


@dataclass
class Agent:
    """One agent of the scan. `plot` is where it last read."""

    id: int
    label: str
    stage: Stage
    role: str
    component: str = ""
    lens: str = ""
    state: State = State.WAITING
    started: float | None = None
    ended: float | None = None
    tools: int = 0
    tokens: int = 0
    plot: int | None = None
    activity: str = ""
    rev: int = 0
    name: str = ""


@dataclass
class Lead:
    """A place that a researcher reported, before duplicates are joined."""

    plot: int
    plot_line: int
    agent: int
    at: float
    rev: int = 0


@dataclass
class Candidate:
    """A possible flaw before the panel. `path` is its file's path as a view may show it, and no
    key for a look-up. `line` is a line of that file."""

    id: str
    path: str = ""
    line: int = 0
    plot: int | None = None
    plot_line: int = 0
    votes: dict[str, Vote] = field(default_factory=lambda: dict.fromkeys(LENSES, Vote.PENDING))
    outcome: Outcome = Outcome.TESTING
    settled: float | None = None
    rev: int = 0


@dataclass
class Finding:
    """One record of the finished report."""

    id: str
    title: str
    severity: str
    confidence: str
    file: str
    line: int
    plot: int | None
    plot_line: int
    category: str
    cwe: str
    symbol: str
    snippet: str
    description: str
    impact: str
    exploit_scenario: str
    preconditions: list[str]
    recommendation: str


@dataclass
class Visit:
    """What the agents read of one plot: merged spans of lines, first and last included."""

    plot: int
    reads: int = 0
    last: float = 0.0
    spans: list[tuple[int, int]] = field(default_factory=list)
    rev: int = 0

    def cover(self, first: int, last: int) -> int:
        """Add the span from `first` to `last`, and return how many new lines it adds."""
        merged: list[tuple[int, int]] = []
        for low, high in sorted([*self.spans, (first, last)]):
            if merged and low <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], high))
            else:
                merged.append((low, high))
        added = _lines_in(merged) - _lines_in(self.spans)
        self.spans = merged
        return added


def _lines_in(spans: Iterable[tuple[int, int]]) -> int:
    return sum(high - low + 1 for low, high in spans)


class Touch(NamedTuple):
    """One look at the code: kind is "read" for lines of one plot, "search" for a run of plots.
    `plots` holds the first plot of the run and the plot after its last."""

    rev: int
    at: float
    agent: int
    kind: Look
    plots: tuple[int, int]
    first: int
    last: int


class Note(NamedTuple):
    """A line of the scan's own narration."""

    rev: int
    at: float
    text: str


class Totals(TypedDict):
    """What a scan has counted so far. Each attempt of a retried agent counts as an agent."""

    agents: int
    running: int
    done: int
    failed: int
    tools: int
    tokens: int
    files: int
    files_read: int
    lines: int
    lines_read: int
    leads: int
    candidates: int
    confirmed: int
    refuted: int
    findings: int


def _outcome(votes: list[Vote]) -> Outcome:
    if votes.count(Vote.CONFIRM) >= PANEL_KEEP_QUORUM:
        return Outcome.CONFIRMED
    if votes.count(Vote.REFUTE) >= PANEL_KEEP_QUORUM:
        return Outcome.REFUTED
    return Outcome.UNSETTLED


class Scan:
    """Everything that is known of a running scan. Hold `changed` to read one state of it."""

    def __init__(
        self, target: Target, atlas: Atlas, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.target: Target = target
        self.atlas: Atlas = atlas
        self.changed: threading.Condition = threading.Condition()
        self.rev: int = 1
        self.result: Result = Result()
        self.phases: dict[Stage, Phase] = {stage: Phase(stage) for stage in Stage}
        self.components: list[Component] = []
        self.agents: dict[int, Agent] = {}
        self.leads: list[Lead] = []
        self.candidates: dict[str, Candidate] = {}
        self.findings: list[Finding] = []
        self.visits: dict[int, Visit] = {}
        self._read: set[str] = set()
        self._lines_read: int = 0
        self.touches: deque[Touch] = deque(maxlen=_RECENT_TOUCHES)
        self.notes: deque[Note] = deque(maxlen=_RECENT_NOTES)
        self._clock: Callable[[], float] = clock
        self._began: float = clock()
        self._ended: float | None = None
        self._components_rev: int = 0
        self._findings_rev: int = 0
        self._asked_at_once: set[str] = set()

    def now(self) -> float:
        """Seconds since the scan began. The clock stops when the scan ends."""
        return self._clock() - self._began if self._ended is None else self._ended

    @property
    def running(self) -> bool:
        return self.result.state is State.RUNNING

    def totals(self) -> Totals:
        agents = self.agents.values()
        outcomes = [candidate.outcome for candidate in self.candidates.values()]
        return {
            "agents": len(agents),
            "running": sum(agent.state is State.RUNNING for agent in agents),
            "done": sum(agent.state is State.DONE for agent in agents),
            "failed": sum(agent.state is State.FAILED for agent in agents),
            "tools": sum(agent.tools for agent in agents),
            "tokens": sum(agent.tokens for agent in agents),
            "files": len(self.atlas.files),
            "files_read": len(self._read),
            "lines": self.atlas.lines,
            "lines_read": self._lines_read,
            "leads": len(self.leads),
            "candidates": len(outcomes),
            "confirmed": outcomes.count(Outcome.CONFIRMED),
            "refuted": outcomes.count(Outcome.REFUTED),
            "findings": len(self.findings),
        }

    def delta(self, since: int = 0) -> dict[str, object]:
        """What changed after revision `since`, as JSON values. Revision 0 gives everything."""

        def newer(items: Iterable[Agent | Lead | Candidate | Visit]) -> list[dict[str, object]]:
            return [asdict(item) for item in items if item.rev > since]

        with self.changed:
            out: dict[str, object] = {
                "rev": self.rev,
                "now": round(self.now(), 2),
                "target": asdict(self.target),
                "result": asdict(self.result),
                "phases": [asdict(phase) for phase in self.phases.values()],
                "totals": self.totals(),
                "agents": newer(self.agents.values()),
                "leads": newer(self.leads),
                "candidates": newer(self.candidates.values()),
                "visits": newer(self.visits.values()),
                "touches": [touch._asdict() for touch in self.touches if touch.rev > since],
                "notes": [note._asdict() for note in self.notes if note.rev > since],
            }
            if self._components_rev > since:
                out["components"] = [asdict(component) for component in self.components]
            if self._findings_rev > since:
                out["findings"] = [asdict(finding) for finding in self.findings]
            return out

    def use_model(self, model: str) -> None:
        with self.changed:
            self.target.model = model
            self._next()

    def describe(self, *, commit: str, dirty: bool) -> None:
        with self.changed:
            self.target.commit, self.target.dirty = commit, dirty
            self._next()

    def enter(self, stage: Stage) -> None:
        """Start a stage. Once no agent of an earlier one runs or waits, that one ends, or is
        skipped if it never began."""
        with self.changed:
            phase = self.phases[stage]
            if phase.started is None:
                phase.started = self.now()
                self.note(_OPENINGS[stage])
            phase.state, phase.ended = State.RUNNING, None
            self._settle_phases()
            self._next()

    def note(self, text: str) -> None:
        with self.changed:
            self.notes.append(Note(self._next(), self.now(), text))

    def map_components(self, components: Sequence[Component]) -> None:
        with self.changed:
            self.components = list(components)
            self._components_rev = self._next()

    def update_agent(
        self,
        agent: Agent,
        *,
        state: State | None = None,
        tools: int | None = None,
        tokens: int | None = None,
        activity: str | None = None,
    ) -> None:
        """Add the agent if it is new, set the fields given, and time its start and its end."""
        with self.changed:
            self.agents[agent.id] = agent
            agent.state = agent.state if state is None else state
            agent.tools = agent.tools if tools is None else tools
            agent.tokens = agent.tokens if tokens is None else tokens
            agent.activity = agent.activity if activity is None else activity
            if agent.state in {State.RUNNING, State.DONE} and agent.started is None:
                agent.started = self.now()
                self.enter(agent.stage)
            if agent.state in {State.DONE, State.FAILED} and agent.ended is None:
                agent.ended, agent.activity = self.now(), ""
                self._settle_phases()
            agent.name = words.agent(agent)
            agent.rev = self._next()

    def read(self, agent: Agent, path: str, first: int = 1, count: int | None = None) -> None:
        """Record that the agent read `count` lines of a file from line `first`, or the rest."""
        plot, lines = self.atlas.find(path), self.atlas.files.get(path)
        if plot is None or lines is None:
            return
        with self.changed:
            start = min(max(first, 1), len(lines)) - 1
            seen = lines[start : None if count is None else start + max(count, 1)]
            first, last = seen.start + 1, seen.stop
            self._read.add(path)
            visit = self.visits.setdefault(plot, Visit(plot))
            if seen:
                self._lines_read += visit.cover(first, last)
            visit.reads, visit.last = visit.reads + 1, self.now()
            visit.rev = agent.rev = self._next()
            agent.plot = plot
            run = (plot, plot + 1)
            self.touches.append(Touch(self.rev, visit.last, agent.id, Look.READ, run, first, last))

    def search(self, agent: Agent, path: str) -> None:
        """Record that the agent searched a file or a folder."""
        plots = self.atlas.under(path)
        if not plots:
            return
        # The plots under a path are adjacent, since the atlas is in path order.
        run = (plots[0], plots[-1] + 1)
        with self.changed:
            self.touches.append(Touch(self._next(), self.now(), agent.id, Look.SEARCH, run, 0, 0))

    def lead(self, agent: Agent, path: str, line: int) -> None:
        plot = self.atlas.find(path)
        if plot is None:
            return
        with self.changed:
            on_plot = self.atlas.plot_line(path, line)
            self.leads.append(Lead(plot, on_plot, agent.id, self.now(), self._next()))

    def admit(self, cid: str, path: str = "", line: int = 0, shown: str | None = None) -> Candidate:
        """The candidate of that id, added if new and placed if a path is given. A view shows
        `shown`, if given, in place of the path."""
        with self.changed:
            candidate = self.candidates.setdefault(cid, Candidate(cid))
            if path:
                candidate.path, candidate.line = path if shown is None else shown, line
                candidate.plot = self.atlas.find(path)
                candidate.plot_line = self.atlas.plot_line(path, line)
            candidate.rev = self._next()
            return candidate

    def vote(self, cid: str, lens: str, vote: Vote) -> None:
        """Record a vote. Two votes settle the candidate if both confirm or both refute it, and
        else the third does. The two are the first verifiers', or any where all were asked
        at once. A third verifier can be asked after two that settle it: see ask()."""
        with self.changed:
            candidate = self.admit(cid)
            candidate.votes[lens] = vote
            if cid in self._asked_at_once and candidate.outcome is not Outcome.TESTING:
                return
            votes = list(candidate.votes.values())
            deciding = votes if cid in self._asked_at_once else votes[:-1]
            if Vote.PENDING not in votes or _outcome(deciding) is not Outcome.UNSETTLED:
                candidate.settled, candidate.outcome = self.now(), _outcome(votes)
                cast = len(votes) - votes.count(Vote.PENDING)
                agree = f"{votes.count(Vote.CONFIRM)} of {cast} verifiers confirm it"
                self.note(f"{cid} is {candidate.outcome.value}: {agree}")

    def ask(self, cid: str, lens: str) -> None:
        """Put the candidate back under test, with this lens's vote pending, and the last lens's
        where that is asked after the others."""
        with self.changed:
            candidate = self.admit(cid)
            if lens == LENSES[-1] and set(candidate.votes.values()) == {Vote.PENDING}:
                self._asked_at_once.add(cid)
            elif cid not in self._asked_at_once:
                candidate.votes[LENSES[-1]] = Vote.PENDING
            candidate.votes[lens] = Vote.PENDING
            candidate.settled, candidate.outcome = None, Outcome.TESTING

    def reopen(self) -> None:
        """Clear the votes of each candidate that no whole panel settled: a further run has it.
        The report waits for that run."""
        with self.changed:
            if self.phases[Stage.REPORT].started is not None:
                self.phases[Stage.REPORT] = Phase(Stage.REPORT)
                self.note("Verification goes on before the report")
            for candidate in self.candidates.values():
                if candidate.outcome is Outcome.TESTING:
                    candidate.votes = dict.fromkeys(LENSES, Vote.PENDING)
                    candidate.rev = self._next()
            self._asked_at_once.clear()

    def finish(self, result: Result, findings: Sequence[Finding] = ()) -> None:
        with self.changed:
            self._ended = self.now()
            self.result, self.findings = result, list(findings)
            # A verification comes from a report that was read, so its stage did not fail.
            cut = result.state is State.FAILED and not result.verification
            # The stages end first: an agent that fails would end its stage as done.
            for phase in self.phases.values():
                if phase.state is State.RUNNING:
                    phase.state, phase.ended = State.FAILED if cut else State.DONE, self._ended
                elif phase.state is State.WAITING:
                    phase.state = State.SKIPPED
            for agent in self.agents.values():
                if agent.state in {State.WAITING, State.RUNNING}:
                    self.update_agent(agent, state=State.FAILED)
            for candidate in self.candidates.values():
                if candidate.outcome is Outcome.TESTING:
                    candidate.outcome, candidate.settled = Outcome.UNSETTLED, self._ended
                    candidate.rev = self._next()
            self._findings_rev = self._next()

    def _settle_phases(self) -> None:
        begun = [phase.stage for phase in self.phases.values() if phase.started is not None]
        busy = {a.stage for a in self.agents.values() if a.state in {State.WAITING, State.RUNNING}}
        for phase in self.phases.values():
            if phase.stage is begun[-1]:
                break
            if phase.stage in busy:
                continue
            if phase.started is None:
                phase.state = State.SKIPPED
            elif phase.state is State.RUNNING:
                phase.state, phase.ended = State.DONE, self.now()

    def _next(self) -> int:
        self.rev += 1
        self.changed.notify_all()
        return self.rev
