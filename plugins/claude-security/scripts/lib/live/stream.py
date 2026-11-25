"""Claude Code's stream-json rows, read into a Scan."""

from __future__ import annotations

import math
import os
import re
import shlex
from collections import Counter, defaultdict
from itertools import islice, takewhile
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Callable

from lib import absolute, display, last_report, plugin, strictjson
from lib.strictjson import JsonMap, as_int, as_map, clean, is_list, is_str, maps, strings

from .atlas import BYTES_PER_LINE, PATH_CHARS
from .scan import LENSES, Agent, Component, Scan, Stage, State, Vote

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

HOOKED_TOOLS = ("Read", "Grep", "Glob", "Bash", "StructuredOutput")
_STATES = {"progress": State.RUNNING, "done": State.DONE, "error": State.FAILED}
_RETRY = re.compile(r":retry\d+| \(retry \d+\)")
_PANEL = re.compile(r"panel:(C\d+):v([123])")
_PLACE = re.compile(r"^file: (.+)\nline: (\d+)$", re.MULTILINE)
_VERDICT = re.compile(r'"verdict"\s*:\s*"(\w+)"')
_SED_SPANS = re.compile(r"""(?<=[\s'";])(\d{1,9})(?:,(\d{1,9}|/?\$))?p(?=[\s'";]|$)""")
_DELIVERED = re.compile(r'\{\s*"success"\s*:\s*true\b')
_END_LINES = re.compile(r"\b(head|tail)\s+-([nc]?)\s*(\+?)(\d{1,9})\b")
_ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
_PROGRAM = re.compile(r"(?!-)[\w./+-]*[\w+]")
_OUTSIDE = re.compile(r"/|~|[a-zA-Z]:|[a-zA-Z][a-zA-Z0-9+.-]*:/")
_REVISION = re.compile(r"^(:\(literal\)|.{2,}:)")
_COMMIT = re.compile(r"^revision: ([0-9a-f]{7,64})\r?$", re.MULTILINE)
_DIRTY = re.compile(r"^revision\.dirty: true\r?$", re.MULTILINE)
_NO_FILE = re.compile(r"^file_count: 0\r?$", re.MULTILINE)
_NOTHING_CHANGED = re.compile(
    rf"^write_scan_meta\.py: {re.escape(plugin.NO_CHANGED_FILE)}", re.MULTILINE
)
_GIT_BASH_DRIVE = re.compile(r"^/([a-zA-Z])/")
_UNFIT_NAME = re.compile(r"[\r\n\t]")
_NAME_CHARS = 400
_TRUE = "TRUE_POSITIVE"
_FALSE = "FALSE_POSITIVE"
_OLDER = "PREDATES_CHANGE"
_UNREAD = "COULD_NOT_READ"
_VOTES = {_TRUE: Vote.CONFIRM, _UNREAD: Vote.ABSTAIN}
_QUESTIONS = ("present", "ships", "reachable", "gain")
_ANSWER = re.compile(rf'"({"|".join(_QUESTIONS)})"\s*:\s*\{{[^{{}}]*?"answer"\s*:\s*"([^"\\]*)"')
_READERS = frozenset({"cat", "head", "tail", "sed", "nl", "awk", "less", "more"})
_SEARCHERS = frozenset({"grep", "egrep", "rg", "ugrep", "find", "bfs", "ls", "git", "wc", "tree"})
_COMMANDS = _READERS | _SEARCHERS
_WHOLE = "research:repository"
_FILTERS = re.compile(
    r"(^|[\s/|&(])(grep|egrep|rg|ugrep|wc|git(\s+-[Cc]\s+\S+|\s+--\S+){0,8}\s+(log|grep))"
    r"(\s(?!-E?vE?\s)|$)"
)
_PIPELINE = re.compile(
    r"""(?:'[^']*'|"(?:\\.|[^"\\])*"|\\.|[<>|]&|&>|(?<!\|)\|(?!\|)\s*|[^;&|\n])+""", re.DOTALL
)
_LOOP = re.compile(r"\b(?:for|read(?:\s+-r)?)\s+(\w+)")
_VARIABLE = re.compile(r"\$\{?(\w+)")
_MAX_READS = 200
# These agents start ahead of the stage whose title they bear, or after it: by the label's start.
_OUT_OF_TURN = {
    f"load:{last_report.RESEARCH_RUN}:": Stage.SETUP,
    "past-fixes": Stage.RESEARCH,
}
_CHANGE = "the change"
_ACTIVITY_CHARS = 160
_PLACE_CHARS = 400
_EARLY_CALLS = 64
_UNCHANGED = "file_unchanged"
_REDACTOR = f"{plugin.NAME}:scan-redactor"
_CLEAN = "finished"
_LAUNCHED = "Async agent launched"


def _text(value: object, cap: int | None = 200) -> str:
    """Model-written text, made fit for one line of output."""
    return display.written_out(display.single_line(strictjson.well_formed(clean(value))))[:cap]


def _decoded(value: object) -> object:
    """The value, or what it says if it is JSON text: the workflow takes both."""
    try:
        return strictjson.loads(value) if is_str(value) else value
    except ValueError:
        return value


def _shown(response: object) -> JsonMap:
    """A tool_response without a file's text: which lines a Read returned, where it says."""
    said = as_map(response)
    file = as_map(said.get("file"))
    return {"type": said.get("type"), "file": {k: file.get(k) for k in ("startLine", "numLines")}}


def _cut_off(*, started: bool) -> State:
    """How an agent ends that a completed workflow cut off, one whose answer the workflow no longer
    awaited. It did not fail: one that started is done, and one still queued is skipped."""
    return State.DONE if started else State.SKIPPED


class Reader:
    """Feeds rows to a scan. `last_words` and `failed` are those of the newest result row.
    `redacted` says that the newest redaction agent cleaned all of the report's files,
    `nothing_to_scan` that the newest workflow ended well with no file and no agent, or that the
    change to scan touched no file, `underway` that a workflow or an agent has started,
    `left_auto` that the init row named no permission mode or another one than auto, or that a
    status row named another one, and `unloaded` that the init row listed the plugins without this
    one. `load_errors` are the messages of that row's plugin errors, less the empty ones."""

    def __init__(self, scan: Scan, root: Path) -> None:
        self.last_words: str = ""
        self.failed: bool = False
        self.redacted: bool = False
        self.nothing_to_scan: bool = False
        self.underway: bool = False
        self.left_auto: bool = False
        self.unloaded: bool = False
        self.load_errors: list[str] = []
        self._scan: Scan = scan
        self._root: Path = root
        self._tasks: dict[str, JsonMap] = {}
        self._agents: dict[str, Agent] = {}
        self._by_agent_id: dict[str, Agent] = {}
        self._early_calls: dict[str, list[JsonMap]] = defaultdict(list)
        self._calls: Counter[int] = Counter()
        self._handbacks: dict[str, str] = {}
        self._redactor: Agent | None = None
        self._hooked: bool = False
        self._older_counts: bool = False
        self._change_listed: bool = False
        self._of_change: bool = False
        self._no_file: bool = False
        self._meta_call: str = ""
        self._told: set[str] = set()
        self._rows: dict[str, Callable[[JsonMap], None]] = {
            "system/init": self._init,
            "system/status": self._status,
            "system/task_started": self._task_started,
            "system/task_progress": self._task_progress,
            "system/task_notification": self._task_ended,
            "system/permission_denied": self._denied,
            "assistant/": self._turn,
            "user/": self._tool_results,
            "control_request/": self._callback,
            "control_response/": self._setup_refused,
        }

    @property
    def busy(self) -> bool:
        """Whether a workflow or an agent of the session still runs."""
        return bool(self._tasks)

    def row(self, row: JsonMap) -> None:
        """Take one row of the stream."""
        if row.get("type") == "result":
            self.last_words = clean(row.get("result")) or "\n".join(strings(row.get("errors")))
            ended = clean(row.get("subtype"))
            self.failed = row.get("is_error") is True or ended not in {"", "success"}
        elif handler := self._rows.get(f"{clean(row.get('type'))}/{clean(row.get('subtype'))}"):
            handler(row)

    def _callback(self, row: JsonMap) -> None:
        request = as_map(row.get("request"))
        if request.get("subtype") == "hook_callback":
            self.tool_call(as_map(request.get("input")))

    def _setup_refused(self, row: JsonMap) -> None:
        answer = as_map(row.get("response"))
        if answer.get("subtype") == "error":
            said = _text(answer.get("error"))
            self.tell("refused", f"Claude Code refused the scan's setup: {said}")

    def tool_call(self, call: JsonMap) -> None:
        """Take the input of one PostToolUse callback."""
        self._hooked = True
        agent_id = clean(call.get("agent_id"))
        shown = _shown(call.get("tool_response"))
        if agent := self._by_agent_id.get(agent_id):
            self._calls[agent.id] += 1
            self._scan.update_agent(agent, tools=max(agent.tools, self._calls[agent.id]))
            self._called(agent, clean(call.get("tool_name")), as_map(call.get("tool_input")), shown)
        elif agent_id and len(self._early_calls[agent_id]) < _EARLY_CALLS:
            self._early_calls[agent_id].append({**call, "tool_response": shown})

    def tell(self, key: str, text: str) -> None:
        """Add a note, once for each key."""
        with self._scan.changed:
            if key not in self._told:
                self._told.add(key)
                self._scan.note(text)

    def _init(self, row: JsonMap) -> None:
        self._scan.use_model(_text(row.get("model")))
        self.tell("init", "Claude Code is ready and prepares the scan")
        self._mode(row.get("permissionMode"))
        if is_list(loaded := row.get("plugins")):
            self.unloaded = all(each.get("name") != plugin.NAME for each in maps(loaded))
            said = (clean(each.get("message")) for each in maps(row.get("plugin_errors")))
            self.load_errors = [*filter(None, said)]

    def _status(self, row: JsonMap) -> None:
        # Claude Code can leave auto mode after its init row, and says so in a status row.
        if "permissionMode" in row:
            self._mode(row["permissionMode"])

    def _mode(self, mode: object) -> None:
        if mode != "auto":
            self.left_auto = True
            self.tell(
                "mode", "Auto mode is not available. Commands that need approval are refused."
            )

    def _task_started(self, row: JsonMap) -> None:
        if clean(row.get("task_type")) in {"local_workflow", "local_agent"}:
            self.underway = True
            self._tasks[clean(row.get("task_id"))] = row

    def _task_ended(self, row: JsonMap) -> None:
        task = clean(row.get("task_id"))
        began = self._tasks.pop(task, {})
        done = row.get("status") == "completed"
        call_id = clean(began.get("tool_use_id"))
        if agent := self._agents.get(call_id):
            if not done or call_id in self._handbacks:
                self._redactor_said(agent, self._handbacks[call_id] if done else "")
            if agent.state is not State.FAILED:
                self._scan.update_agent(agent, state=State.DONE)
        elif done and began.get("task_type") == "local_workflow":
            for key, left in self._agents.items():
                if key.startswith(f"{task}/") and left.state in {State.RUNNING, State.WAITING}:
                    self._scan.update_agent(
                        left, state=_cut_off(started=left.state is State.RUNNING)
                    )
            self.nothing_to_scan = self._no_file and not self._scan.agents
            if self._scan.agents:
                self._enter(Stage.REPORT)

    def _task_progress(self, row: JsonMap) -> None:
        task = clean(row.get("task_id"))
        agent = self._agents.get(clean(row.get("tool_use_id")))
        if agent and (usage := as_map(row.get("usage"))):
            tools, tokens = as_int(usage.get("tool_uses")), as_int(usage.get("total_tokens"))
            self._scan.update_agent(agent, tools=tools, tokens=tokens)
        if wait := as_map(row.get("usage_limit_wait")):
            self.tell(f"wait {wait.get('resets_at')}", "Waiting for the usage limit to reset")
        # The agents come first: one that waits keeps its stage open when a later stage begins.
        for entry in maps(row.get("workflow_progress")):
            if entry.get("type") == "workflow_agent":
                self._agent_row(f"{task}/{entry.get('index')}", entry)
        title, _, label = clean(row.get("description")).partition(": ")
        if stage := _stage(title, label):
            self._enter(stage)

    def _enter(self, stage: Stage) -> None:
        if self._scan.phases[stage].started is None:
            self._scan.enter(stage)

    def _agent_row(self, key: str, entry: JsonMap) -> None:
        agent = self._agents.get(key) or self._new_agent(key, entry)
        if agent.ended is not None:
            return
        begun = State.RUNNING if entry.get("startedAt") else State.WAITING
        state = _STATES.get(clean(entry.get("state")), begun)
        if entry.get("endedWithRun") == "completed":
            state = _cut_off(started=agent.started is not None or begun is State.RUNNING)
        if agent_id := clean(entry.get("agentId")):
            self._by_agent_id[agent_id] = agent
        for call in self._early_calls.pop(agent_id, ()):
            self.tool_call(call)
        tools = max(as_int(entry.get("toolCalls")), self._calls[agent.id])
        tokens = as_int(entry.get("tokens"))
        if (state, tools, tokens) != (agent.state, agent.tools, agent.tokens):
            self._preview(agent, entry)
            self._scan.update_agent(agent, state=state, tools=tools, tokens=tokens)

    def _new_agent(self, key: str, entry: JsonMap) -> Agent:
        label = _text(_RETRY.sub("", clean(entry.get("label"))))
        role, _, rest = label.partition(":")
        where = lens = ""
        if panel := _PANEL.fullmatch(label):
            where, lens = panel[1], LENSES[int(panel[2]) - 1]
            place = _PLACE.search(clean(entry.get("promptPreview")))
            path, line = (self._relative(place[1]), int(place[2])) if place else ("", 0)
            self._scan.admit(where, path, line, _text(path, None)[-_PLACE_CHARS:])
            self._scan.ask(where, lens)
        elif role == "research":
            where, lens = self._researched(rest)
            where = _CHANGE if self._change_listed else where
            parts = self._scan.components
            if all(part.name != where for part in parts):
                kept = [] if label == _WHOLE else parts
                self._scan.map_components([*kept, Component(where, "", [])])
        stage = _stage(clean(entry.get("phaseTitle")), label) or Stage.RESEARCH
        agent = self._agents[key] = Agent(len(self._agents), label, stage, role, where, lens)
        self._scan.update_agent(agent)
        return agent

    def _researched(self, rest: str) -> tuple[str, str]:
        """The component and lens that a researcher's label names after `research:`."""
        if self._of_change:
            where, colon, lens = rest.rpartition(":")
            return (where, lens) if colon else (rest, "")
        if any(part.name == rest for part in self._scan.components):
            return rest, ""
        if rest.endswith(":all"):
            return rest.removesuffix(":all"), "all"
        return rest.removesuffix(":2"), ""

    def _preview(self, agent: Agent, entry: JsonMap) -> None:
        """What a snapshot's short fields give where no callback has."""
        said = clean(entry.get("resultPreview"))
        if agent.role == "panel" and (verdict := _VERDICT.search(said)):
            try:
                self._vote(agent, as_map(strictjson.loads(said)))
            except ValueError:
                seen: dict[str, str] = dict(_ANSWER.findall(said))
                told = len(seen) == len(_QUESTIONS) or any(word != "YES" for word in seen.values())
                held = {_TRUE, _OLDER, _UNREAD} if self._older_counts else {_TRUE, _UNREAD}
                if verdict[1] not in held or (verdict[1] != _UNREAD and told):
                    answers = {question: {"answer": word} for question, word in seen.items()}
                    self._vote(agent, {**answers, "verdict": verdict[1]})
        tool = clean(entry.get("lastToolName"))
        if not self._hooked and tool != "StructuredOutput":
            summary = clean(entry.get("lastToolSummary"))
            given = {"file_path": summary, "path": summary, "command": summary}
            self._called(agent, tool, given, {})

    def _vote(self, agent: Agent, answer: JsonMap) -> None:
        candidate = self._scan.candidates.get(agent.component)
        if candidate is None or candidate.votes[agent.lens] is not Vote.PENDING:
            return
        verdict = clean(answer.get("verdict"))
        if self._turned(verdict, answer):
            verdict = _FALSE
        older = Vote.CONFIRM if self._older_counts else Vote.REFUTE
        vote = older if verdict == _OLDER else _VOTES.get(verdict, Vote.REFUTE)
        self._scan.vote(agent.component, agent.lens, vote)

    def _called(self, agent: Agent, tool: str, given: JsonMap, shown: JsonMap) -> None:
        if tool not in HOOKED_TOOLS:
            return
        if tool == "StructuredOutput":
            self._answered(agent, given)
            return
        if tool == "Read":
            path = self._relative(clean(given.get("file_path")))
            file = as_map(shown.get("file"))
            first = as_int(file.get("startLine")) or as_int(given.get("offset")) or 1
            count = as_int(file.get("numLines")) or as_int(given.get("limit")) or None
            past_end = first > 1 and file.get("numLines") == 0
            if shown.get("type") != _UNCHANGED and not past_end:
                self._scan.read(agent, path, first, count)
            activity = f"Read {path}"
        elif tool == "Bash":
            activity = self._shell(agent, clean(given.get("command")))
        else:
            path = self._relative(clean(given.get("path")) or ".")
            self._scan.search(agent, path)
            activity = _searched(path)
        self._scan.update_agent(agent, activity=_text(activity, _ACTIVITY_CHARS))

    def _shell(self, agent: Agent, command: str) -> str:
        """Record the files that a shell command names, and say in a few words what it did."""
        argv, whole = _words(command)
        assigned = list(takewhile(_ASSIGNMENT.match, argv))
        argv = argv[len(assigned) :]
        whole = whole and not set("".join(assigned)) & set("({`")
        shown = whole and argv and _PROGRAM.fullmatch(argv[0])
        ran = f"Run {argv[0].rpartition('/')[2] if shown else 'a command'}"
        if reads := [*islice(self._reads(command), _MAX_READS)]:
            for path, first, count in reads:
                self._scan.read(agent, path, first, count)
            return f"Read {reads[-1][0]}"
        if _verbs(argv) & _SEARCHERS:
            paths = self._named(argv)
            for path in paths or ["."]:
                self._scan.search(agent, path)
            if paths:
                return _searched(paths[0].partition("*")[0].rstrip("/") or ".")
        return ran

    def _named(self, argv: list[str]) -> list[str]:
        """The words that name a place on the map, each as a path from the scan root."""
        named = (
            self._relative(_REVISION.sub("", word))
            for word in argv
            if word[:1] not in {"", "-", "*"} and "=" not in word
        )
        return [path for path in named if path not in _COMMANDS and self._scan.atlas.under(path)]

    def _reads(self, command: str) -> Iterator[tuple[str, int, int]]:
        """The spans of known files that the pipelines of a command show. The variable of a loop
        stands for the files that its head names."""
        files = self._scan.atlas.files
        loops: dict[str, list[str]] = {}
        for pipeline in _PIPELINE.finditer(command):
            argv, spelled = _words(pipeline[0])[0], pipeline[0].replace("\\", "/")
            if head := _LOOP.search(spelled):
                loops[head[1]] = self._named(argv)
            if not _verbs(argv) & _READERS or _FILTERS.search(spelled):
                continue
            used = dict.fromkeys(name[1] for name in _VARIABLE.finditer(spelled))
            looped = [path for name in used for path in loops.get(name, ())]
            for path in filter(files.__contains__, looped + self._named(argv)):
                yield from ((path, *span) for span in _lines_shown(spelled, len(files[path])))

    def _answered(self, agent: Agent, answer: JsonMap) -> None:
        if agent.role == "panel":
            self._vote(agent, answer)
        elif agent.role == "inventory":
            if not (parts := maps(answer.get("components"))):
                return
            self._scan.map_components([
                self._component(part.get("name"), part.get("paths")) for part in parts
            ])
            self._scan.note(f"The code is divided into {display.counted(len(parts), 'component')}")
        else:
            found = maps(answer.get("findings"))
            for lead in found:
                path = self._relative(clean(lead.get("file")))
                self._scan.lead(agent, path, as_int(lead.get("line")))
            if found:
                said = display.counted(len(found), "lead")
                self._scan.note(f"{agent.name} reports {said}")

    def _turned(self, verdict: str, answer: JsonMap) -> bool:
        """Whether the workflow reads the answer as a refutation, whatever its verdict says."""
        if verdict == _UNREAD:
            return self._names_no_file(answer.get("unopenedFile"))
        asked = (as_map(answer.get(question)).get("answer") for question in _QUESTIONS)
        return verdict in {_TRUE, _OLDER} and any(said != "YES" for said in asked)

    def _names_no_file(self, name: object) -> bool:
        """Whether a COULD_NOT_READ vote names no repository file: the workflow refutes it."""
        written = clean(name)
        path = self._relative(written)
        unfit = _UNFIT_NAME.search(written) or len(written) > _NAME_CHARS
        climbs = any(part.strip() == ".." for part in re.split(r"[\\/]", written))
        driveless = self._root.drive.endswith(":") and written.startswith(("/", "\\"))
        return path in {"", "."} or bool(unfit or climbs or driveless or _OUTSIDE.match(path))

    def _plots(self, paths: object) -> list[int]:
        matching = self._scan.atlas.matching
        return sorted({plot for path in strings(paths) for plot in matching(self._relative(path))})

    def _component(self, name: object, paths: object) -> Component:
        atlas = self._scan.atlas
        plots = self._plots(paths)
        shown = [atlas.plots[i].path for i in plots]
        files = shown if all(path in atlas.files for path in shown) else []
        suffixes = (PurePosixPath(path).suffix[1:].lower() for path in files if atlas.files[path])
        kinds = Counter(filter(None, suffixes))
        return Component(_text(name), _text(kinds.most_common(1)[0][0] if kinds else ""), plots)

    def _denied(self, row: JsonMap) -> None:
        if agent := self._by_agent_id.get(clean(row.get("agent_id"))):
            self._scan.update_agent(agent, activity=f"Refused: {_text(row.get('tool_name'))}")

    def _turn(self, row: JsonMap) -> None:
        for block in maps(as_map(row.get("message")).get("content")):
            if block.get("type") != "tool_use":
                continue
            call_id, tool = clean(block.get("id")), block.get("name")
            given = as_map(block.get("input"))
            if not (parent := clean(row.get("parent_tool_use_id"))):
                self._lead_call(call_id, tool, given)
            elif tool == "SubagentHandback" and parent in self._agents:
                self._handbacks[call_id] = clean(given.get("message"))

    def _lead_call(self, call_id: str, tool: object, given: JsonMap) -> None:
        command = clean(given.get("command"))
        if tool == "Workflow":
            self._scan.reopen()
            self.nothing_to_scan = False
            self._workflow_args(given.get("args"))
        elif "write_scan_meta.py" in command:
            self._meta_call = call_id
            self.tell("meta", "Recording the revision and sizing the scan")
        elif "render_report.py" in command:
            if command.startswith("python3"):
                self._enter(Stage.REPORT)
            self.tell("render", "Rendering the report's files")
        elif given.get("subagent_type") == _REDACTOR:
            agent = Agent(len(self._agents), "redactor", Stage.REPORT, "redactor")
            self._agents[call_id] = self._redactor = agent
            self.redacted = False
            self._scan.update_agent(agent, state=State.RUNNING, activity="Redact credentials")
            self.tell("redact", "Looking for credential values in the report")

    def _tool_results(self, row: JsonMap) -> None:
        for block in maps(as_map(row.get("message")).get("content")):
            call_id, content = clean(block.get("tool_use_id")), block.get("content")
            said = clean(content) or next((clean(part.get("text")) for part in maps(content)), "")
            agent = self._agents.get(call_id)
            if agent and agent.role == "redactor":
                if not said.startswith(_LAUNCHED):
                    word = self._handbacks.get(call_id, said)
                    self._redactor_said(agent, "" if block.get("is_error") is True else word)
            elif call_id == self._meta_call:
                self._no_file = bool(_NO_FILE.search(said))
                self.nothing_to_scan = bool(_NOTHING_CHANGED.search(said))
                if found := _COMMIT.search(said):
                    commit = found[1][: plugin.SHORT_ID_CHARS]
                    self._scan.describe(commit=commit, dirty=bool(_DIRTY.search(said)))
            elif call_id in self._handbacks and _DELIVERED.match(said):
                self._handbacks[clean(row.get("parent_tool_use_id"))] = self._handbacks[call_id]

    def _redactor_said(self, agent: Agent, word: str) -> None:
        """Take a redactor's word, which is empty if its call or task failed. A failure stays."""
        if word != _CLEAN:
            self._scan.update_agent(agent, state=State.FAILED)
        if agent is self._redactor:
            self.redacted = agent.state is not State.FAILED

    def _workflow_args(self, given: object) -> None:
        args = as_map(_decoded(given))
        setting = clean(args.get(plugin.CHANGE_SCAN_EFFORT_KEY)).lower()
        if clean(args.get("range")) and setting == plugin.CHANGE_SCAN_EFFORT_HIGH:
            self._older_counts = True
        changed = strings(_decoded(args.get("changedFiles")))
        self._of_change = clean(args.get("mode")) not in {"", "scan"}
        # The workflow reads the list for a change or a commit alone.
        if changed and self._of_change:
            self._change_listed = True
            found = (self._scan.atlas.find(self._relative(path)) for path in changed)
            plots = sorted({plot for plot in found if plot is not None})
            self._scan.map_components([Component(_CHANGE, "", plots)])

    def _relative(self, path: str) -> str:
        """`path` with forward slashes, from the scan root if it lies below it and is not very
        long."""
        spelled = path.replace("\\", "/")
        if len(spelled) > len(str(self._root)) + PATH_CHARS:
            return spelled
        if self._root.drive:
            spelled = _GIT_BASH_DRIVE.sub(r"\1:/", spelled)
        return absolute.relative(os.path.normpath(self._root / spelled), str(self._root)) or spelled


def _words(command: str) -> tuple[list[str], bool]:
    """The words of a shell command, and whether it could be read as shell words."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";|&")
    lexer.whitespace_split, lexer.commenters = True, ""
    try:
        return list(lexer), True
    except ValueError:
        return command.split(), False


def _verbs(argv: list[str]) -> set[str]:
    return {word.rpartition("/")[2].lstrip("(") for word in argv if not _ASSIGNMENT.match(word)}


def _lines_shown(pipeline: str, lines: int) -> Iterator[tuple[int, int]]:
    """The first line of each span that a pipeline shows of a file of `lines` lines, and how many.
    A span of sed can lie outside the file: Scan.read cuts it to the file. An estimate: a head or
    tail cuts each span of sed alone, and one ahead of sed is not read."""
    found = [*_SED_SPANS.finditer(pipeline)]
    ends = [*_END_LINES.finditer(pipeline, found[-1].start() if found else 0)]
    spans = [(int(span[1]), span[2] or span[1]) for span in found] or [(1, "$")]
    return (
        _cut(first, lines if last.endswith("$") else min(int(last), lines), ends)
        for first, last in spans
    )


def _cut(first: int, last: int, ends: list[re.Match[str]]) -> tuple[int, int]:
    for end in ends:
        program, unit, plus, digits = end.groups()
        count = max(math.ceil(int(digits) / BYTES_PER_LINE) if unit == "c" else int(digits), 1)
        if program == "head":
            last = min(first + count - 1, last)
        else:
            first = min(first + count - 1, last) if plus else max(last - count + 1, first)
    return first, last - first + 1


def _searched(path: str) -> str:
    return f"Search {'the repository' if path == '.' else path}"


def _stage(title: str, label: str) -> Stage | None:
    """The stage in which an agent counts."""
    moved = next((stage for start, stage in _OUT_OF_TURN.items() if label.startswith(start)), None)
    return moved or next((stage for stage in Stage if stage.value == title), None)
