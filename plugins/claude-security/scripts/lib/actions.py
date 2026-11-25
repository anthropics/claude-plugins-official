"""The GitHub Actions job: what the runner's environment and event payload say, whether
anything can be posted from here, and the files the job's later steps read."""

from __future__ import annotations

import enum
import errno
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple

from . import console, gh, plain, plugin, sarif, strictjson, verdict
from .effort import ChangeScanEffort
from .gfm import one_line, plain_line
from .strictjson import as_map, is_int, is_list, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .strictjson import JsonMap

REPORT_POINTER = "claude-security-report-dir"
VERDICT_NAME = "claude-security-verdict"
# GitHub drops a job summary past 1 MiB; the review text added to it stops at about half that.
SUMMARY_LIMIT = 512_000
STOPPED = "**The Claude Security plugin stopped:**"
SARIF_LIMIT = plain.READ_LIMIT
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}/[A-Za-z0-9._-]{1,100}\Z")
_GITHUB_SHA_RE = re.compile(r"[0-9a-f]{40}")
_TRUE_OR_FALSE = {"false": False, "true": True}


EDITED = "edited"
# A model's name as the review prints it: an alias, a model ID, or a provider's or gateway's name.
_MODEL_RE = re.compile(r"[A-Za-z0-9._:/@\[\]-]{1,200}\Z")


class JobError(Exception):
    """A refusal about the job's environment; the message names what the caller must fix."""


_NOT_ACCEPTED = "is not accepted (this message does not show it)"


def true_or_false(word: str, named: str) -> bool:
    """`word` as the setting of the true-or-false input `named`; any other word is a refusal
    that names the input, and does not show the word."""
    if word not in _TRUE_OR_FALSE:
        msg = f"{named} {_NOT_ACCEPTED}; it must be true or false"
        raise JobError(msg)
    return _TRUE_OR_FALSE[word]


def sha(value: object) -> str | None:
    """`value` when it is a full lowercase commit id as GitHub spells one, else None."""
    return value if is_str(value) and _GITHUB_SHA_RE.fullmatch(value) else None


class BaseChange(NamedTuple):
    """The base branch's name before and after the edit that changed it."""

    was: str
    now: str


class PullRequest(NamedTuple):
    """The pull request this job runs for, as the event payload describes it."""

    repository: str
    number: int
    url: str
    head_sha: str
    base_sha: str
    base_ref: str
    base_change: BaseChange | None

    @classmethod
    def from_event(cls, path: Path) -> PullRequest | None:
        """The pull request named by the event payload at `path`; None when it names none."""
        try:
            event = strictjson.load(path)
        except (OSError, ValueError) as error:
            problem = plain_line(str(error))
            console.warn(f"the event payload at {path} could not be read: {problem}")
            return None
        if not is_map(event):
            return None
        pr, repository = event.get("pull_request"), event.get("repository")
        if not (is_map(pr) and is_map(repository)):
            return None
        head, base = pr.get("head"), pr.get("base")
        repo, number, url = repository.get("full_name"), pr.get("number"), pr.get("html_url")
        head_sha = sha(head.get("sha") if is_map(head) else None)
        base_sha = sha(base.get("sha") if is_map(base) else None)
        if not (is_str(repo) and _REPO_RE.match(repo) and is_int(number) and number > 0):
            return None
        ref = base.get("ref") if is_map(base) else None
        if head_sha is None or base_sha is None or not (is_str(ref) and ref):
            return None
        was: object = event.get("changes") if event.get("action") == EDITED else None
        for key in ("base", "ref", "from"):
            was = was.get(key) if is_map(was) else None
        return cls(
            repository=repo,
            number=number,
            url=url if is_str(url) else "",
            head_sha=head_sha,
            base_sha=base_sha,
            base_ref=ref,
            base_change=BaseChange(was=was, now=ref) if is_str(was) and was else None,
        )


def _sarif_flaw(log: Path, total: int | None) -> str:
    """Why the SARIF log at `log` must not go to code scanning, worded to follow the file's name;
    empty when nothing is wrong. `total` is the stamp's count of findings."""
    names: set[str] = set()
    alike = False

    def noted(members: list[tuple[str, object]]) -> object:
        nonlocal alike
        folded = {name.casefold() for name, _ in members}
        names.update(folded)
        alike = alike or len(folded) < len(members)
        return dict(members)

    try:
        document = strictjson.loads(plain.read_text(log, SARIF_LIMIT), noted)
    except FileNotFoundError:
        return "is missing"
    except OSError as error:
        if error.errno == errno.EFBIG:
            return f"is larger than {SARIF_LIMIT >> 20} MiB"
        return f"cannot be read ({error.strerror})"
    except ValueError:
        return "is not JSON in UTF-8, or is nested too deeply"
    if "markdown" in names:
        return 'holds a "markdown" property, which GitHub code scanning can show as Markdown'
    if alike:
        return "holds an object with two members of one name, in any case of letters"
    runs = document.get("runs") if is_map(document) else None
    only: JsonMap = runs[0] if is_list(runs) and len(runs) == 1 and is_map(runs[0]) else {}
    results = only.get("results")
    if not is_list(results) or len(results) != total:
        return "does not hold one result for each finding that the revision stamp counts"
    if as_map(as_map(only.get("tool")).get("driver")).get("name") != sarif.TOOL_NAME:
        return "does not name the plugin as its tool"
    automation_id = as_map(only.get("automationDetails")).get("id")
    if not (is_str(automation_id) and automation_id.startswith(f"{sarif.ID_PREFIX}/")):
        return "does not name a category of the plugin's"
    return ""


class Runner(NamedTuple):
    """The runner's temp folder, and the files for a step's outputs and for the job summary; each
    None when its variable is unset or empty."""

    temp: Path | None
    output: Path | None
    summary: Path | None

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> Runner:
        """RUNNER_TEMP, GITHUB_OUTPUT and GITHUB_STEP_SUMMARY as the runner sets them."""

        def named(variable: str) -> Path | None:
            value = environ.get(variable)
            return Path(value) if value else None

        return cls(
            temp=named("RUNNER_TEMP"),
            output=named("GITHUB_OUTPUT"),
            summary=named("GITHUB_STEP_SUMMARY"),
        )

    def set_outputs(self, outputs: Mapping[str, str]) -> None:
        """Add each name and value in `outputs` to this step's outputs; JobError when
        GITHUB_OUTPUT is unset or empty, OSError when it cannot be written."""
        if self.output is None:
            msg = "GITHUB_OUTPUT is unset or empty, so this step's outputs cannot be set"
            raise JobError(msg)
        with self.output.open("a", encoding="utf-8", newline="\n") as out:
            out.writelines(f"{name}={value}\n" for name, value in outputs.items())

    def write_verdict(self, lines: Sequence[str]) -> bool:
        """Write the verdict lines to the file VERDICT_NAME names under RUNNER_TEMP, where later
        workflow steps read them; True when it wrote them."""
        if self.temp is None:
            return False
        try:
            (self.temp / VERDICT_NAME).write_bytes(("\n".join(lines) + "\n").encode())
        except OSError as error:
            console.warn(f"could not write the verdict file: {error}")
            return False
        return True

    def clear_verdict(self) -> None:
        """Remove the verdict file, if there is one; OSError when it cannot be removed."""
        if self.temp is not None:
            (self.temp / VERDICT_NAME).unlink(missing_ok=True)

    def append_summary(self, text: str) -> bool:
        """Add `text` to the job summary that GitHub shows on the run's page; True when it was
        written."""
        return self._write_summary(text, "a")

    def replace_summary(self, text: str) -> bool:
        """Put `text` in place of all that this step has written to the job summary; True when it
        was written."""
        return self._write_summary(text, "w")

    def _write_summary(self, text: str, mode: Literal["a", "w"]) -> bool:
        """Write `text`, clipped to SUMMARY_LIMIT bytes at a line break, with each open <details>
        closed and a line that says it was clipped. False when there is no summary file, or the
        write fails."""
        if self.summary is None:
            return False
        data = text.encode("utf-8", "backslashreplace")
        if len(data) > SUMMARY_LIMIT:
            kept = data[:SUMMARY_LIMIT].decode("utf-8", "ignore")
            text = kept.rpartition("\n")[0] or kept
            text += "\n\n</details>" * (text.count("<details>") - text.count("</details>"))
            text += "\n\n_[clipped: the rest did not fit here]_\n"
        try:
            with self.summary.open(
                mode, encoding="utf-8", errors="backslashreplace", newline="\n"
            ) as out:
                out.write(text)
        except OSError as error:
            console.warn(f"could not write to the job summary: {error}")
            return False
        return True

    def say_stopped(self, script: str, error: str) -> None:
        """Say why the job stopped, in one line: on stderr under `script`'s name, and on the job
        summary."""
        sys.stderr.write(plain_line(f"{script}: {error}") + "\n")
        self.append_summary(f"\n{one_line(f'{STOPPED} {error}')}\n")

    def record_report_dir(self, report_dir: Path, total: int | None) -> bool:
        """Leave the report directory's path in RUNNER_TEMP for later steps; True when it is there.
        A directory that plain.all_plain refuses, or whose SARIF log _sarif_flaw() faults against
        the stamp's `total` findings, is not left, and the job summary says so too."""
        path = os.path.realpath(report_dir)
        if self.temp is None:
            console.warn("could not record the report directory: RUNNER_TEMP is unset or empty")
            return False
        why = ""
        if not plain.all_plain(report_dir):
            why = (
                "it contains a link, something else that is neither a regular file nor a folder, "
                "or a folder that cannot be listed"
            )
        elif flaw := _sarif_flaw(report_dir / plugin.SARIF_NAME, total):
            why = f"{plugin.SARIF_NAME} {flaw}. The verdict, and any review, are not affected."
        if why:
            fault = f"could not record the report directory, so later steps find no report: {why}"
            console.warn(fault)
            self.append_summary(f"\n**Claude Security plugin warning:** {fault}\n")
            return False
        line = (path + "\n").encode("utf-8", "surrogateescape")
        try:
            (self.temp / REPORT_POINTER).write_bytes(line)
        except OSError as error:
            console.warn(f"could not record the report directory in RUNNER_TEMP: {error}")
            return False
        return True


class Job(NamedTuple):
    """The GitHub Actions job this runs in, read once from the runner's environment."""

    event: str
    pull_request: PullRequest | None
    # The commit that the job is for: the pull request's head, or GITHUB_SHA where there is none.
    commit: str
    # The pull request's merge base, which the probe step leaves for the post step; else empty.
    merge_base: str
    run_id: str
    rerun: bool
    server_url: str
    has_token: bool
    runner: Runner

    @property
    def reviews(self) -> bool:
        """Whether the job reviews a pull request; any other job scans the checked-out ref."""
        return self.pull_request is not None

    def refuse_stale(self, commit: str | None) -> None:
        """Refuse to send anything when a report describes a commit other than this job's."""
        if commit != self.commit:
            width = plugin.SHORT_ID_CHARS
            msg = (
                f"the report describes commit {(commit or 'none')[:width]} but this job is for "
                f"{self.commit[:width]}, so nothing is sent: check that the workflow checks out "
                "the commit that this job is for, then start a new run"
            )
            raise JobError(msg)

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> Job | None:
        """The GitHub Actions job that the runner's environment describes, None where it describes
        none; JobError for a pull request event whose payload describes no pull request, and for
        any other event whose GITHUB_SHA is no commit id."""
        event, path = environ.get("GITHUB_EVENT_NAME"), environ.get("GITHUB_EVENT_PATH")
        if not (environ.get("GITHUB_ACTIONS") == "true" and event and path):
            return None
        pr = None
        if event.startswith("pull_request"):
            pr = PullRequest.from_event(Path(path))
            if pr is None:
                msg = f"the {event} event payload at {path} does not describe a pull request"
                raise JobError(msg)
        commit = pr.head_sha if pr else sha(environ.get("GITHUB_SHA"))
        if commit is None:
            msg = "GITHUB_SHA holds no commit id, so this run's commit is not known"
            raise JobError(msg)
        return cls(
            event=event,
            pull_request=pr,
            commit=commit,
            merge_base=environ.get("CLAUDE_SECURITY_MERGE_BASE", ""),
            run_id=environ.get("GITHUB_RUN_ID", ""),
            rerun=environ.get("GITHUB_RUN_ATTEMPT") != "1",
            server_url=environ.get("GITHUB_SERVER_URL") or "https://github.com",
            has_token=bool(environ.get("GH_TOKEN") or environ.get("GITHUB_TOKEN")),
            runner=Runner.from_environment(environ),
        )


def poster(job: Job) -> gh.Gh:
    """The gh that a job which reviews a pull request posts with; a refusal that gives the reason
    where nothing can be posted from the job."""
    if job.event == "pull_request_target":
        why = (
            "the pull_request_target event runs this job with a write token against code "
            "from outside the repository; use the pull_request event"
        )
    elif job.event != "pull_request":
        why = (
            f"the {job.event} event does not describe a reviewable head; use the pull_request event"
        )
    elif isinstance(cli := gh.locate(), str):
        why = cli
    elif not job.has_token:
        why = "no GH_TOKEN or GITHUB_TOKEN in the environment"
    else:
        return cli
    raise JobError(why)


def records(run: gh.GhRun, cannot: str, permission: str) -> list[JsonMap]:
    """The JSON objects that gh printed. Raises JobError, with a message that opens with `cannot`,
    where gh failed or printed a line that cannot be read. `permission` is what the call needs."""
    again = "If the reason is temporary, run the job again."
    if run.code:
        msg = (
            f"{cannot}: {run.complaint()}. {again} Otherwise, check that the workflow grants "
            f"`{permission}` under `permissions:`."
        )
        raise JobError(msg)
    rows = run.all_records()
    if rows is None:
        msg = f"{cannot}: gh printed a line that is not a JSON object. {again}"
        raise JobError(msg)
    return rows


def policy_of(environ: Mapping[str, str]) -> verdict.FailOn:
    """The verdict's policy: the one that CLAUDE_SECURITY_FAIL_ON names, or the default where it is
    empty or unset. A word that names none is a refusal, which does not show the word."""
    policy = environ.get("CLAUDE_SECURITY_FAIL_ON") or verdict.DEFAULT_POLICY.value
    try:
        return verdict.FailOn(policy)
    except ValueError:
        names = ", ".join(choice.value for choice in verdict.FailOn)
        msg = f"fail_on or scheduled_fail_on {_NOT_ACCEPTED}; it must be one of {names}"
        raise JobError(msg) from None


def change_scan_effort_of(environ: Mapping[str, str]) -> ChangeScanEffort:
    """The Change Scan Effort that CLAUDE_SECURITY_CHANGE_SCAN_EFFORT names, or low where it is
    empty or unset. A word that names none is a refusal, which does not show the word."""
    word = environ.get("CLAUDE_SECURITY_CHANGE_SCAN_EFFORT") or ChangeScanEffort.LOW.value
    try:
        return ChangeScanEffort(word)
    except ValueError:
        names = " or ".join(choice.value for choice in ChangeScanEffort)
        msg = f"change_scan_effort {_NOT_ACCEPTED}; it must be {names}, in lower case"
        raise JobError(msg) from None


class SuggestPatches(enum.Enum):
    """Whether a job drafts fixes: no, in the same job, or in a later job of the same run."""

    FALSE = "false"
    TRUE = "true"
    LATER = "later"


def suggest_patches_of(environ: Mapping[str, str]) -> SuggestPatches:
    """Where CLAUDE_SECURITY_SUGGEST_PATCHES has a review's fixes drafted: in the same job where it
    is empty or unset. A word that it does not define is a refusal, which does not show the word."""
    word = environ.get("CLAUDE_SECURITY_SUGGEST_PATCHES") or SuggestPatches.TRUE.value
    try:
        return SuggestPatches(word)
    except ValueError:
        names = ", ".join(choice.value for choice in SuggestPatches)
        msg = f"suggest_patches {_NOT_ACCEPTED}; it must be one of {names}"
        raise JobError(msg) from None


class Settings(NamedTuple):
    """What three of the variables the action hands the job ask of it: the verdict's policy, where
    fixes are drafted, and the Change Scan Effort."""

    fail_on: verdict.FailOn
    suggest_patches: SuggestPatches
    change_scan_effort: ChangeScanEffort

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> Settings:
        """The three variables read and checked; a value that one does not define is a refusal."""
        return cls(policy_of(environ), suggest_patches_of(environ), change_scan_effort_of(environ))


def model_setting(environ: Mapping[str, str]) -> str | None:
    """The model that the job asks Claude Code for, as the action hands it over in
    CLAUDE_SECURITY_MODEL; None where it hands over none, or the name does not read as a model's
    name. It is the setting, never the model that answered."""
    named = environ.get("CLAUDE_SECURITY_MODEL", "")
    return named if _MODEL_RE.match(named) else None
