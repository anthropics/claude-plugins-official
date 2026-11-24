#!/usr/bin/env python3
"""Before the scan, decide what a pull request event gets: no scan, the job's last verdict again,
or the scan.

Usage:
  repeat_verdict.py

Runs under GitHub Actions on a pull_request event. It takes from the event's payload whether the
pull request is merged, closed or a draft, and who its author is. The author is a stranger unless
GitHub says that they can write to the repository. The step asks that only on a closed pull request,
a draft that would not be scanned, or an edit.

1. It turns away a merged pull request: it sets the step outputs `scan` and `enforce` to false, and
   says why in the log and on the job summary.
2. On any event, a stranger's closed pull request gets no pass: the step sets `scan` alone to
   false, says why in the same two places and stops. With no verdict, the job then fails.
3. On any event but `edited`, it also turns away a closed pull request and, unless
   CLAUDE_SECURITY_SCAN_DRAFTS is true, a draft that is not a stranger's. Any other pull request
   goes on to the scan.
4. On `edited`, for an author who is no stranger, it asks GitHub for the head commit and the base
   branch as they are now. It takes the newest review of the head commit that a workflow posted
   with a verdict line. Where that review was made against the base branch, under the policy that
   CLAUDE_SECURITY_FAIL_ON names and at the Change Scan Effort that
   CLAUDE_SECURITY_CHANGE_SCAN_EFFORT names, and has its receipt (lib/receipt.py), it writes the
   review's verdict to the verdict file, links the review on the job summary and sets `scan` to
   false. It repeats a pass only where each newer review of that commit by a workflow has its
   receipt too. It also repeats none where a step of this workflow names the receipt of a review
   other than these, in a job that did not end before the passing review. It reads this workflow's
   runs at that commit, except those that ran once and passed.
5. Otherwise it writes no verdict and prints why, and the scan runs. But a closed pull request, or
   a draft that is not scanned, gets no scan. If the reason is that GitHub lists no review of the
   head commit by a workflow, the step turns the pull request away. For any other reason it sets
   `scan` alone to false, and says why on the job summary too: with no verdict, the job then fails.
6. Before step 3 or 5 turns a pull request away, the step asks GitHub for its state and draft
   flag. Unless GitHub says that it is closed, or a draft that is not scanned, the step sets `scan`
   alone to false and says why: with no verdict, the job then fails.

Exits 1, with one line on stderr and on the job summary, where it cannot write a step output or
remove a stale verdict file, or where it reads a word that it does not accept. It reads
CLAUDE_SECURITY_SCAN_DRAFTS on every event, and the other two variables only on `edited`.
Otherwise it exits 0.

To ask GitHub, it needs `gh` on PATH, outside the checkout, and the workflow's token in GH_TOKEN
or GITHUB_TOKEN. Python 3.9, stdlib only.
"""

from __future__ import annotations

import enum
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, final
from urllib.parse import quote

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import actions, console, marker, review, strictjson
from lib.receipt import Receipts
from lib.strictjson import is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lib.effort import ChangeScanEffort
    from lib.gh import Gh
    from lib.strictjson import JsonMap
    from lib.verdict import FailOn


PASSES = "This pull request is {}: nothing was scanned, and this run passes without a review."
WRITES = ("admin", "write")


class Shut(NamedTuple):
    """The step's words for a pull request the job does not scan: what it is, the start of the
    sentence that says it is not scanned, and what gets one scanned."""

    what: str
    clause: str
    remedy: str

    def turned_away(self) -> str:
        """The line that turns such a pull request away."""
        return f"{PASSES.format(self.what)} {self.remedy}"

    def unconfirmed(self) -> str:
        """The line that says that the job fails, since GitHub does not confirm the payload."""
        return (
            f"This run's event says that the pull request is {self.what}, and GitHub does not "
            "confirm it. Nothing was scanned, and this job fails. If the call to GitHub failed, "
            "this step's other lines in the job's log say why. If the pull request is still "
            f"{self.what}, run the job again. Otherwise, unless a run has started since this one, "
            "push a commit or edit the title."
        )

    def failing(self, why: Unrepeated) -> str:
        """The line that says that the job fails, since nothing is repeated for `why`."""
        again = (
            " This step's other lines in the job's log say why. If the reason is temporary, "
            "run the job again."
            if why in {Unrepeated.UNREAD, Unrepeated.UNWRITTEN}
            else ""
        )
        return (
            f"{why.value}. {self.clause}, so no verdict is written, and this job fails.{again} "
            f"{self.remedy} If it is no longer {self.what}, and no run has started since this "
            "one, push a commit."
        )


@final
class Unscanned:
    """What the step says of a pull request the job does not scan."""

    MERGED = PASSES.format("merged")
    STRANGER = (
        "This run's event says that the pull request is closed, and GitHub does not say that its "
        "author can write to the repository. Nothing was scanned, and this job fails. A re-run "
        "makes the same check. To start a new run, reopen the pull request. If it is no longer "
        "closed, and no run has started since this one, push a commit."
    )
    CLOSED_OR_DRAFT = Shut(
        "closed or a draft",
        "A closed or draft pull request is not scanned",
        "The job scans the pull request once it is open and ready for review.",
    )
    CLOSED = Shut(
        "closed",
        "A closed pull request is not scanned",
        "Reopening the pull request gets it scanned.",
    )

    @classmethod
    def shut(cls, drafts: bool) -> Shut:
        """A closed pull request's words, or where `drafts` are not scanned a draft's too."""
        return cls.CLOSED if drafts else cls.CLOSED_OR_DRAFT


class Output(enum.Enum):
    """A step output the job's later steps read."""

    SCAN = "scan"
    ENFORCE = "enforce"


class Unrepeated(enum.Enum):
    """Why the step repeats no verdict."""

    NO_REVIEW = "This job has no review of the pull request's head commit"
    UNREAD = "This job could not read the pull request, its reviews or their receipts from GitHub"
    UNUSABLE = (
        "The newest review of the head commit gives no verdict for that commit, the base branch, "
        "fail_on and change_scan_effort"
    )
    NO_RECEIPT = (
        "The newest review of the head commit with a verdict has no receipt from this workflow: "
        "none was uploaded for it, it is gone, or the review or one of its comments changed"
    )
    NEWER_NO_RECEIPT = (
        "A review of the head commit after the passing review has no receipt from this workflow"
    )
    UNLISTED = (
        "A step of this workflow names a newer review of the head commit, or one of a run that "
        "overlapped, and GitHub does not list it after the passing review"
    )
    UNWRITTEN = "This job could not write down its newest verdict on the head commit"
    NO_WRITE = "GitHub does not say that this pull request's author can write to the repository"


def answered(
    cli: Gh, endpoint: str, *flags: str, fields: str, about: str | None = None
) -> list[JsonMap] | None:
    """What GitHub answers for `endpoint`: the objects the --jq filter `fields` prints, one to a
    line. None, with a warning, when the call fails or a line is anything else. The warning names
    `about` and the HTTP status alone, where the endpoint holds text that an author chose."""
    named = about or endpoint
    run = cli.run("api", *flags, endpoint, "--jq", fields)
    if run.code != 0:
        status = f" (HTTP {run.status})" if run.status else ""
        why = status if about else f": {run.complaint()}"
        console.warn(f"could not read {named}{why}")
        return None
    rows = run.all_records()
    if rows is None:
        console.warn(f"could not read {named}: gh printed a line that is not a JSON object")
    return rows


def asker(environ: Mapping[str, str]) -> tuple[actions.Job, actions.PullRequest, Gh] | None:
    """The job that `environ` describes, its pull request, and the gh that asks GitHub about it.
    None, with a warning, where GitHub cannot be asked."""
    try:
        job = actions.Job.from_environment(environ)
        if job and job.pull_request:
            return job, job.pull_request, actions.poster(job)
    except actions.JobError as error:
        console.warn(str(error))
        return None
    console.warn("this event describes no pull request, so GitHub cannot be asked about one")
    return None


def is_shut(pr: JsonMap, drafts: bool) -> bool:
    """Whether `pr`, a record of a pull request, says that it is closed or, unless `drafts` are
    scanned, a draft."""
    return pr.get("state") == "closed" or (pr.get("draft") is True and not drafts)


def still_shut(environ: Mapping[str, str], drafts: bool) -> bool:
    """is_shut() for the job's pull request as GitHub has it now. False, with a warning, where
    GitHub cannot be asked or gives no answer."""
    found = asker(environ)
    if found is None:
        return False
    _job, pr, cli = found
    pulls = f"repos/{pr.repository}/pulls/{pr.number}"
    now = answered(cli, pulls, fields="{state, draft}")
    if now == []:
        console.warn(f"could not read {pulls}: it gives no answer")
    return bool(now) and is_shut(now[0], drafts)


def can_write(pr: JsonMap, environ: Mapping[str, str]) -> bool:
    """Whether GitHub says that the author of `pr`, a pull request as the payload describes it, can
    write to the repository, for the job that `environ` describes. False, with a warning, where
    GitHub cannot be asked or gives no answer."""
    found = asker(environ)
    if found is None:
        return False
    _job, asked, cli = found
    user = pr.get("user")
    login = user.get("login") if is_map(user) else None
    if not (is_str(login) and login):
        console.warn("GitHub cannot be asked whether this pull request's author can write")
        return False
    name = quote(login, safe="", errors="replace")
    rows = answered(
        cli,
        f"repos/{asked.repository}/collaborators/{name}/permission",
        fields="{permission}",
        about="the author's write access",
    )
    if rows is None:
        return False
    permission = rows[0].get("permission") if rows else None
    if not permission:
        console.warn("GitHub's answer names no permission for this pull request's author")
    return permission in WRITES


def repeat(
    environ: Mapping[str, str],
    policy: FailOn,
    change_scan_effort: ChangeScanEffort,
    runner: actions.Runner,
    author: JsonMap | None,
) -> Unrepeated | None:
    """Repeat a verdict by step 4 of the module's docstring, under `policy` and at
    `change_scan_effort`; otherwise the reason nothing is repeated. `author` is the pull request as
    the payload describes it, to ask whether its author can write, or None where decide() knows
    that. After Unrepeated.UNWRITTEN the verdict file can still be there: decide() removes it, as
    it removes any file left earlier."""
    found = asker(environ)
    if found is None:
        return Unrepeated.UNREAD
    job, pr, cli = found
    if author is not None and not can_write(author, environ):
        return Unrepeated.NO_WRITE
    pulls = f"repos/{pr.repository}/pulls/{pr.number}"
    now = answered(cli, pulls, fields="{head: .head.sha, base: .base.ref}")
    if now is None:
        return Unrepeated.UNREAD
    head, base = (now[0].get("head"), now[0].get("base")) if now else ("", "")
    if not (is_str(head) and head and is_str(base) and base):
        console.warn(f"could not read {pulls}: it answers no head commit or no base branch")
        return Unrepeated.UNREAD
    listed = answered(
        cli, f"{pulls}/reviews?per_page=100", "--paginate", fields=marker.REVIEW_FIELDS
    )
    if listed is None:
        return Unrepeated.UNREAD
    posted = [one for one in map(marker.Recorded.of, listed) if one and one.commit == head]
    if not posted:
        return Unrepeated.NO_REVIEW
    newest = max([one for one in posted if one.has_a_line()] or posted)
    tokens = newest.tokens(
        marker.Terms(policy=policy, change_scan_effort=change_scan_effort, head=head, base=base)
    )
    if tokens is None:
        print(
            f"The review {newest.url} gives no verdict for this head commit, base branch, "
            "fail_on and change_scan_effort."
        )
        return Unrepeated.UNUSABLE
    comments = answered(
        cli, f"{pulls}/comments?per_page=100", "--paginate", fields=marker.COMMENT_FIELDS
    )
    if comments is None:
        return Unrepeated.UNREAD
    newer = [one for one in posted if one > newest] if marker.passes(tokens) else []
    try:
        receipts = Receipts.of_run(cli.run, pr.repository, job.run_id)
        for one in (newest, *newer):
            if not receipts.left_for(one, comments):
                print(f"The review with no receipt is {one.url}.")
                return Unrepeated.NEWER_NO_RECEIPT if one > newest else Unrepeated.NO_RECEIPT
        if marker.passes(tokens) and receipts.left_after(newest, newer, comments):
            return Unrepeated.UNLISTED
    except actions.JobError as error:
        console.warn(str(error))
        return Unrepeated.UNREAD
    said = (
        f"{review.REVIEW_HEADING}\n\nThe job's newest verdict on this pull request's head commit, "
        f"in [this review]({newest.url}), was made against its base branch and under this run's "
        f"`fail_on` and `change_scan_effort`. Its result is repeated ({' '.join(tokens[:2])}), and "
        "nothing was scanned.\n"
    )
    if not (runner.write_verdict(tokens) and runner.append_summary(said)):
        console.warn(
            f"the verdict of {newest.url} is not repeated: the verdict file or the job summary "
            "could not be written"
        )
        return Unrepeated.UNWRITTEN
    return None


def payload(environ: Mapping[str, str]) -> JsonMap:
    """The event payload the runner hands the job; empty when it cannot be read."""
    try:
        event = strictjson.load(Path(environ["GITHUB_EVENT_PATH"]))
    except (KeyError, OSError, ValueError):
        return {}
    return event if is_map(event) else {}


def scans_drafts(environ: Mapping[str, str]) -> bool:
    """Whether the workflow has draft pull requests scanned: CLAUDE_SECURITY_SCAN_DRAFTS, which
    carries the scan_drafts input, is true. Empty or unset is false; any other word is a
    refusal."""
    word = environ.get("CLAUDE_SECURITY_SCAN_DRAFTS") or "false"
    return actions.true_or_false(word, "scan_drafts")


def switch_off(runner: actions.Runner, *outputs: Output) -> None:
    """Set each of the named step outputs to false, for the conditions of the job's later steps."""
    runner.set_outputs({output.value: "false" for output in outputs})


def say(runner: actions.Runner, line: str) -> None:
    """Print `line`, and add it to the job summary under the review's heading."""
    print(line)
    runner.append_summary(f"{review.REVIEW_HEADING}\n\n{line}\n")


def turn_away(runner: actions.Runner, away: str) -> None:
    """Give the pull request no scan and no verdict, and say `away` in the log and on the job
    summary."""
    switch_off(runner, Output.SCAN, Output.ENFORCE)
    say(runner, away)


def turn_away_or_fail(runner: actions.Runner, drafts: bool) -> None:
    """Do step 6 of the module's docstring."""
    words = Unscanned.shut(drafts)
    if still_shut(os.environ, drafts):
        turn_away(runner, words.turned_away())
    else:
        switch_off(runner, Output.SCAN)
        say(runner, words.unconfirmed())


def decide(runner: actions.Runner) -> None:
    """Do what the module's docstring says. Raises JobError or OSError where the step must fail."""
    drafts = scans_drafts(os.environ)
    event = payload(os.environ)
    described = event.get("pull_request")
    pr: JsonMap = described if is_map(described) else {}
    if pr.get("merged") is True:
        turn_away(runner, Unscanned.MERGED)
        return
    closed = is_shut(pr, drafts=True)
    asked = is_shut(pr, drafts)
    writer = asked and can_write(pr, os.environ)
    scanned = not closed and not writer
    if closed and not writer:
        switch_off(runner, Output.SCAN)
        say(runner, Unscanned.STRANGER)
        return
    if event.get("action") != actions.EDITED:
        if not scanned:
            turn_away_or_fail(runner, drafts)
        return
    policy = actions.policy_of(os.environ)
    change_scan_effort = actions.change_scan_effort_of(os.environ)
    author = None if writer else pr
    why = (
        Unrepeated.NO_WRITE
        if asked and not writer
        else repeat(os.environ, policy, change_scan_effort, runner, author)
    )
    if why is None:
        switch_off(runner, Output.SCAN)
        return
    runner.clear_verdict()
    if scanned:
        print(f"{why.value}, so the scan runs.")
    elif why is Unrepeated.NO_REVIEW:
        turn_away_or_fail(runner, drafts)
    else:
        switch_off(runner, Output.SCAN)
        say(runner, Unscanned.shut(drafts).failing(why))


def main() -> int:
    runner = actions.Runner.from_environment(os.environ)
    try:
        decide(runner)
    except (actions.JobError, OSError) as error:
        files = "could not write this step's outputs, or remove the earlier verdict file: "
        about = files if isinstance(error, OSError) else ""
        runner.say_stopped("repeat_verdict.py", f"{about}{error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
