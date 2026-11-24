"""Which reviews on a pull request the Actions job posted. Every workflow posts under one account,
so the job leaves a receipt for each review: a hash of the review, as the name of an artifact and,
behind the run's ID, in the name of a step."""

from __future__ import annotations

import functools
import hashlib
from typing import TYPE_CHECKING, NamedTuple, Protocol

from . import actions, strictjson
from .gh import in_carets
from .strictjson import as_int, is_int, is_str, maps

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .gh import GhRun
    from .marker import Comment, Recorded
    from .strictjson import JsonMap

CANNOT_READ = "could not read which reviews this workflow posted"
# Opens the name of a step in CI.md's sample, and so in each workflow that was copied from it.
_STEP = "Receipt "
# GitHub lists no more runs than this for one commit.
_MOST_RUNS = 1000


def name(review: Recorded, comments: Iterable[Comment]) -> str:
    """The name of the receipt for `review`, which holds `comments`."""
    placed = [
        (in_carets(one.path), one.start, one.end, in_carets(one.body).strip()) for one in comments
    ]
    posted = [review.number, review.body.strip(), sorted(placed)]
    digest = hashlib.sha256(strictjson.text(posted).encode()).hexdigest()
    return f"claude-security-review-{digest}"


def in_run(run: int | str, named: str) -> str:
    """What the step of run `run` for the receipt `named` has in its name, behind its first word:
    the run's ID and the receipt's hash."""
    return f"{run} {named.rpartition('-')[2]}"


class Call(Protocol):
    """Runs gh with these arguments."""

    def __call__(self, *args: str) -> GhRun: ...


class _Origin(NamedTuple):
    """The workflow that a run belongs to, and the commit that it ran at."""

    workflow: int
    commit: str

    @classmethod
    def of(cls, run: JsonMap) -> _Origin | None:
        """The origin that GitHub's record of a run names; None where a part is missing."""
        workflow, commit = run.get("workflow_id"), actions.sha(run.get("head_sha"))
        return cls(workflow, commit) if is_int(workflow) and commit else None


def _rows(call: Call, endpoint: str, fields: str, *flags: str) -> list[JsonMap]:
    run = call("api", *flags, endpoint, "--jq", fields)
    return actions.records(run, f"{CANNOT_READ} ({endpoint})", "actions: read")


def _origin(call: Call, repository: str, run: int | str) -> _Origin | None:
    rows = _rows(call, f"repos/{repository}/actions/runs/{run}", "{workflow_id, head_sha}")
    return _Origin.of(rows[0]) if rows else None


@functools.cache
def _runs_at(call: Call, repository: str, commit: str) -> list[JsonMap]:
    """The runs at `commit`, of every workflow."""
    return _rows(
        call,
        f"repos/{repository}/actions/runs?head_sha={commit}",
        ".workflow_runs[] | {id, run_attempt, workflow_id, head_sha, conclusion}",
        "--paginate",
    )


@functools.cache
def _steps(call: Call, repository: str, run: int) -> list[tuple[str, str]]:
    """Each step, in every attempt of `run`: when its job ended, empty until then, and its name."""
    jobs = _rows(
        call,
        f"repos/{repository}/actions/runs/{run}/jobs?filter=all",
        ".jobs[] | {steps, completed_at}",
        "--paginate",
    )
    return [
        (strictjson.clean(job.get("completed_at")), named)
        for job in jobs
        for step in maps(job.get("steps"))
        if is_str(named := step.get("name"))
    ]


class Receipts(NamedTuple):
    """The receipts that the runs of one workflow left. Each lookup raises actions.JobError
    where gh fails, or prints what cannot be read."""

    call: Call
    repository: str
    workflow: int

    @classmethod
    def of_run(cls, call: Call, repository: str, run_id: str) -> Receipts:
        """The receipts of the workflow that run `run_id` belongs to; actions.JobError also where
        GitHub names no workflow or no commit for it."""
        own = _origin(call, repository, run_id)
        if own is None:
            msg = f"{CANNOT_READ}: GitHub names no workflow or no commit for this run"
            raise actions.JobError(msg)
        return cls(call, repository, own.workflow)

    def left_for(self, review: Recorded, comments: Iterable[JsonMap]) -> bool:
        """Whether a run of the workflow, at the commit of `review`, left its receipt: as an
        artifact or, in a run that ran again, as a step's name. `comments` are all the pull
        request's review comments (marker.COMMENT_FIELDS)."""
        commit = actions.sha(review.commit)
        if commit is None:
            return False
        named = name(review, review.comments_among(comments))
        uploads = _rows(
            self.call,
            f"repos/{self.repository}/actions/artifacts?name={named}",
            ".artifacts[] | {run: .workflow_run.id}",
            "--paginate",
        )
        ours = _Origin(self.workflow, commit)
        return any(
            is_int(run := upload.get("run")) and _origin(self.call, self.repository, run) == ours
            for upload in uploads
        ) or any(
            step == _STEP + in_run(number, named)
            for run in _runs_at(self.call, self.repository, commit)
            if _Origin.of(run) == ours
            and is_int(number := run.get("id"))
            and as_int(run.get("run_attempt")) > 1
            for _ended, step in _steps(self.call, self.repository, number)
        )

    def left_after(
        self, review: Recorded, newer: Iterable[Recorded], comments: Sequence[JsonMap]
    ) -> bool:
        """Whether a step names the receipt of a review other than `review` and those in `newer`,
        in a job that did not end before `review` was submitted. It reads the workflow's runs at
        the commit of `review`, except those that ran once and passed. `comments` are as for
        left_for(). actions.JobError also where the list of runs may be cut short."""
        runs = _runs_at(self.call, self.repository, review.commit)
        if len(runs) >= _MOST_RUNS:
            msg = f"{CANNOT_READ}: GitHub lists {_MOST_RUNS} runs of this commit, and never more"
            raise actions.JobError(msg)
        known = [name(one, one.comments_among(comments)) for one in (review, *newer)]
        return any(
            step.startswith(_STEP + in_run(number, ""))
            and step not in {_STEP + in_run(number, named) for named in known}
            for run in runs
            if _Origin.of(run) == _Origin(self.workflow, review.commit)
            and (run.get("conclusion"), run.get("run_attempt")) != ("success", 1)
            and is_int(number := run.get("id"))
            for ended, step in _steps(self.call, self.repository, number)
            if not ended or ended >= review.submitted
        )
