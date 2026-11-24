#!/usr/bin/env python3
"""Turn a scan run in CI into a pull request review, or record a branch scan for the job.

Usage:
  post_review.py --probe EFFORT --reports DIR [--handed-over SCANNED] [<scan_root>]
  post_review.py --finished --reports DIR [--handed-over SCANNED] [<scan_root>]

DIR is the folder of the report directory: with --probe, the one the scan makes it in; with
--finished, the one that holds it after the scan. In a pull request's job, --probe leaves the merge
base as the step output merge_base, and --finished reads it from CLAUDE_SECURITY_MERGE_BASE.
--finished leaves the name of the posted review's receipt as the step output receipt, the run's ID
and that name's hash as in_run, and the step output hand_over, which is true where a later job is to
draft fixes for the report.

That later job names the folder that the report was handed over in: SCANNED. Its session only drafts
fixes, --finished takes nothing but the patches from DIR, and the review adds the fixes to the
first, with no verdict line. In a re-run, that review is not posted where the newest live comment
with a receipt at a place of a finding names a higher severity or confidence than the report.

Exits 0 on success, 1 on a refusal naming what is wrong, and 2 on a usage error or an EFFORT that
names no tier. Python 3.9, stdlib only; a pull request's job needs `gh` on PATH (it and its folder
outside the checkout, once links are followed) and the workflow's token in GH_TOKEN or GITHUB_TOKEN.
"""

from __future__ import annotations

import argparse
import functools
import os
import sys
import tempfile
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, TypedDict, final

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (
    actions,
    console,
    cwe,
    gfm,
    git,
    history,
    link,
    marker,
    plain,
    plugin,
    products,
    receipt,
    review,
    sarif,
    source,
    strictjson,
    verdict,
)
from lib.actions import Job, PullRequest, SuggestPatches
from lib.effort import ChangeScanEffort, Effort, tier
from lib.finding import FINDING_ID
from lib.marker import Comment, Prior, Recorded, Tag
from lib.products import Report
from lib.receipt import Receipts
from lib.strictjson import as_int, as_map

if TYPE_CHECKING:
    from lib.gh import Gh, GhRun
    from lib.strictjson import JsonMap


class ReviewError(Exception):
    """A refusal; the message says what stopped the step."""


def asked(cli: Gh, cannot: str, *call: str) -> GhRun:
    """What gh answers to `call`. Where gh fails, the call is made once more, unless GitHub refused
    it with a 4xx status. A warning that opens with `cannot` comes before the second try."""
    run = cli.run(*call)
    if run.code and run.status not in REFUSED:
        console.warn(f"{cannot}: {run.complaint()}; trying once more")
        run = cli.run(*call)
    return run


def merge_base_of(pr: PullRequest, cli: Gh) -> str:
    """The merge base of the pull request's head and base as GitHub computes it; a refusal
    naming the compare call's complaint, or what it returned instead, when there is none."""
    endpoint = f"repos/{pr.repository}/compare/{pr.base_sha}...{pr.head_sha}"
    cannot_read = "could not read the pull request's merge base"
    run = asked(cli, cannot_read, "api", endpoint, "--jq", ".merge_base_commit.sha")
    if run.code != 0:
        msg = f"{cannot_read}: {run.complaint()}"
        raise ReviewError(msg)
    answer = run.out.strip()
    if actions.sha(answer) is None:
        got = repr(answer) if answer else "nothing"
        msg = f"GitHub returned {got} instead of the merge base's commit id"
        raise ReviewError(msg)
    return answer


class ProbedPullRequest(TypedDict):
    """The pull request in the --probe answer: the merge base, and the job's commit."""

    merge_base: str
    head: str


class ProbedFinding(TypedDict):
    """One place of an earlier finding in the --probe answer."""

    claudeSecurityPluginFindingId: str
    path: str
    line: int
    headline: str
    fix_offered: bool
    severity: str | None
    confidence: str | None


# The most places of one id that a session is asked to re-check. With more, no `fixed` settles it.
MOST_PLACES = 5


class Probe(TypedDict):
    """The --probe answer. The ci-review skill, patch_artifacts.py --prepare and the post step read
    it."""

    effort: str
    change_scan_effort: str | None
    pull_request: ProbedPullRequest | None
    previous_findings: list[ProbedFinding]
    suggest_patches: bool
    fixes_only: bool
    reports: str
    branch_scan: bool


def probe(
    scan_root: str,
    reports: Path,
    settings: actions.Settings,
    job: Job | None,
    cli: Gh | None,
    effort: Effort,
    *,
    fixes_only: bool,
) -> Probe:
    """The --probe answer for this job, which only drafts fixes where `fixes_only` says so. In a
    pull request's job, the merge base is also left as the step output merge_base. Raises
    ReviewError where the scan cannot go on: the checkout is not at the job's commit, or git cannot
    name its commit; a pull request's checkout is a partial clone; GitHub gives no merge base;
    lines_holding() cannot read a file; or the head has the code of an earlier finding, and git
    cannot diff the pull request. Raises actions.JobError where the earlier comments, their reviews
    or the receipts cannot be read."""
    pr = job.pull_request if job else None
    if job is not None:
        head = git.commit_id(scan_root, "HEAD")
        if head is None:
            msg = (
                "git could not read which commit is checked out. Nothing was scanned. To see why, "
                "run `git rev-parse HEAD` in the checkout, in a step before this action. If the "
                "reason is temporary, run the job again."
            )
            raise ReviewError(msg)
        if head != job.commit:
            width = plugin.SHORT_ID_CHARS
            msg = (
                f"the checkout is at {head[:width]}, not {job.commit[:width]}, the commit this job "
                "is for. Nothing was scanned. Check out that commit, as the actions/checkout step "
                "of the sample workflow in this action's CI.md does."
            )
            raise ReviewError(msg)
    pull_request: ProbedPullRequest | None = None
    earlier = marker.Earlier([], [], {})
    spans: review.Spans = {}
    if job is not None and pr is not None and cli is not None:
        if history.partial_clone(scan_root):
            msg = (
                "the checkout's git configuration marks it as a partial clone, in which git can "
                "lack a version of a changed file, and the review needs both versions. Nothing was "
                "scanned. Remove any `filter:` or `sparse-checkout:` input from the "
                "actions/checkout step that checks out this repository: either makes a partial "
                "clone."
            )
            raise ReviewError(msg)
        try:
            merge_base = merge_base_of(pr, cli)
        except ReviewError as error:
            msg = (
                f"{error}. Nothing was scanned. If the reason is temporary, run the job again. "
                "Otherwise, if GitHub refused the call, compare the workflow's `permissions:` with "
                "the sample workflow in this action's CI.md."
            )
            raise ReviewError(msg) from error
        job.runner.set_outputs({"merge_base": merge_base})
        pull_request = {"merge_base": merge_base, "head": job.commit}
        own_receipts(pr, job.run_id, cli)
        earlier = at_head(prior_findings(pr, job.run_id, cli, scan_root), scan_root, job.commit)
        if earlier.holding:
            spans = pull_request_spans(scan_root, merge_base, job.commit)
    previous = earlier.believed
    fullest = marker.fullest_by_key(previous)
    newest = earlier.answering()
    named = {one.place: one for one in previous if one.anchor and one.tag is not Tag.WITHHELD}
    places = {
        at: named.get(at, fullest[at.key])
        for held in review.to_read(earlier, spans).values()
        for at in held[:MOST_PLACES]
    }
    reviews = job is None or job.reviews
    high = reviews and settings.change_scan_effort is ChangeScanEffort.HIGH
    return {
        "effort": (Effort.HIGH if high else effort).value,
        "change_scan_effort": ChangeScanEffort.HIGH.value if high else None,
        "pull_request": pull_request,
        "previous_findings": [
            {
                FINDING_ID: p.key,
                "path": p.path,
                "line": at.line,
                "headline": p.headline,
                "fix_offered": (last := newest.get(at)) is not None and last.tag is Tag.FIX,
                "severity": last.graded.severity.name if last and last.graded else None,
                "confidence": last.graded.confidence.name if last and last.graded else None,
            }
            for at, p in places.items()
        ],
        "suggest_patches": (fixes_only or settings.suggest_patches is SuggestPatches.TRUE)
        and reviews,
        "fixes_only": fixes_only,
        "reports": os.path.abspath(reports),
        "branch_scan": not reviews,
    }


def last_line(pr: PullRequest, outcome: verdict.Verdict, settings: actions.Settings) -> str:
    """The last line of a review posted on the pull request. It records `outcome`, and the policy
    and the Change Scan Effort of `settings`, under which it was reached, when the base branch's
    name can be carried; otherwise it records no verdict, and a warning says why."""
    line = marker.Terms(
        policy=settings.fail_on,
        change_scan_effort=settings.change_scan_effort,
        head=pr.head_sha,
        base=pr.base_ref,
    ).line(outcome.lines())
    if line is None:
        console.warn(
            "the base branch's name is too long for the review's last line, or holds characters "
            "it does not carry, so the review records no verdict for a later run to repeat"
        )
    return line or marker.NO_VERDICT_LINE


def rows_of(pr: PullRequest, cli: Gh, kind: Literal["comments", "reviews"]) -> list[JsonMap]:
    """The pull request's review comments or reviews. Where gh fails, the listing is tried once
    more, unless GitHub refused it. actions.JobError when they cannot be listed."""
    fields = marker.COMMENT_FIELDS if kind == "comments" else marker.REVIEW_FIELDS
    endpoint = f"repos/{pr.repository}/pulls/{pr.number}/{kind}?per_page=100"
    cannot_list = f"could not list the pull request's earlier {kind}"
    run = asked(cli, cannot_list, "api", "--paginate", endpoint, "--jq", fields)
    return actions.records(run, cannot_list, "pull-requests: write")


@functools.cache
def own_receipts(pr: PullRequest, run_id: str, cli: Gh) -> Receipts:
    """The receipts of this job's workflow. A lookup is tried once more, as a listing is."""
    call = functools.partial(asked, cli, receipt.CANNOT_READ)
    return Receipts.of_run(call, pr.repository, run_id)


class Priors(NamedTuple):
    """The marked comments on a pull request: those in a review that has its receipt, and the
    others, each with GitHub's path in place of its marker's, and with no headline."""

    believed: list[Prior]
    doubted: list[Prior]


def prior_findings(pr: PullRequest, run_id: str, cli: Gh, scan_root: str) -> Priors:
    """The findings that earlier review comments on the pull request mark, the believed ones with
    `broken` set from the head commit under `scan_root`. A warning counts the comments whose review
    has no receipt. actions.JobError where a listing or a lookup fails."""
    comments = rows_of(pr, cli, "comments")
    rows = [(one, prior) for one in comments if (prior := Prior.of(one))]
    if not rows:
        return Priors([], [])
    reviews = map(Recorded.of, rows_of(pr, cli, "reviews"))
    receipts = own_receipts(pr, run_id, cli)
    marking = {prior.review for _one, prior in rows}
    ours = {
        one.number
        for one in reviews
        if one and one.number in marking and receipts.left_for(one, comments)
    }
    doubted = [
        prior._replace(path=Comment.of(one).path, headline="")
        for one, prior in rows
        if prior.review not in ours
    ]
    if doubted:
        console.warn(
            "earlier comments on findings that this run ignores, since their review has no "
            f"receipt: {len(doubted)}. Their grades can still count in the check, and the re-check "
            "can read their lines. The step Receipt of the sample workflow in this action's CI.md "
            "is for keeping receipts after a re-run"
        )
    believed = [prior for _one, prior in rows if prior.review in ours]
    changed = functools.partial(has_changed, scan_root, pr.head_sha)
    return Priors(marker.with_broken_fixes(believed, comments, changed), doubted)


NO_FETCH = {"GIT_NO_LAZY_FETCH": "1"}


def text_at(scan_root: str, head: str, path: str) -> str | None:
    """The head commit's text of the file at `path`; None where git gives none."""
    blob = git.argument(f"{head}:{path}")
    return git.run(scan_root, "cat-file", "blob", blob, env=NO_FETCH, exact=True)


def tree_row(scan_root: str, head: str, path: str) -> str | None:
    """git's row on `path` in the head commit's tree, empty where it holds nothing there; None
    where git gives no answer."""
    tree = ("--literal-pathspecs", "ls-tree", "-z", "--full-tree", head, "--")
    return git.run(scan_root, *tree, git.argument(path), env=NO_FETCH)


def lacks(scan_root: str, head: str, path: str) -> bool:
    """Whether git says that the head commit holds nothing at `path`."""
    row = tree_row(scan_root, head, path)
    return row is not None and not row


def has_changed(scan_root: str, head: str, lines: marker.Lines) -> bool:
    """Whether the head commit no longer holds the `lines` of a comment on several lines. False
    where git cannot read that commit or the file."""
    if not git.commit_id(scan_root, head):
        return False
    text = text_at(scan_root, head, lines.path)
    return lacks(scan_root, head, lines.path) if text is None else lines.at(text) != lines.made_on


def on_its_lines(prior: Prior, scan_root: str, head: str) -> Prior:
    """`prior`, outdated where its lines have changed at the head commit."""
    changed = prior.lines and has_changed(scan_root, head, prior.lines)
    return prior._replace(live=False) if changed else prior


def lines_holding(priors: list[Prior], scan_root: str, head: str) -> dict[str, list[int]]:
    """By id in `priors`, which have their receipts, the lines of the head's file whose code has
    that id. An id with none need not have lost its code: the search misses a blank line, an id that
    hashes a line number, and an id whose rule no comment in its file names. ReviewError where git
    cannot read a file on which a comment names a CWE entry, unless the head holds no file there."""
    found: dict[str, list[int]] = {}
    for path in dict.fromkeys(prior.path for prior in priors if prior.cwe):
        here = [prior for prior in priors if prior.path == path]
        rules = {sarif.rule_id(cwe.catalog.category(one.cwe)) for one in here if one.cwe}
        keys = {prior.key for prior in here}
        text = text_at(scan_root, head, path)
        if text is None:
            entry = tree_row(scan_root, head, path)
            if entry is None or " blob " in entry.partition("\t")[0]:
                msg = (
                    f"git could not read {path}, a file with an earlier finding, at the head "
                    "commit, or ran out of time. If the reason is temporary, run the job again."
                )
                raise ReviewError(msg)
            continue
        lines = source.normalized_lines(text)
        for row, line in enumerate(lines):
            if not line:
                continue
            code = sarif.code_at(lines, row)
            for key in keys.intersection(sarif.keyed(rule, path, code) for rule in rules):
                found.setdefault(key, []).append(row + 1)
    return found


def at_head(listed: Priors, scan_root: str, head: str) -> marker.Earlier:
    """The comments in `listed` after on_its_lines(), with lines_holding()'s answer."""
    believed = [on_its_lines(one, scan_root, head) for one in listed.believed]
    doubted = [on_its_lines(one, scan_root, head) for one in listed.doubted]
    return marker.Earlier(believed, doubted, lines_holding(believed, scan_root, head))


def as_at_head(top: str, head: str, path: str) -> bool:
    """Whether `path` below `top`, both as git spells them, is a regular file with the head commit's
    text, line ends aside, or the head commit holds nothing there. False where a read fails."""
    text = text_at(top, head, path)
    if text is None:
        return lacks(top, head, path)
    try:
        data = plain.read_bytes(Path(git.for_disk(top), git.for_disk(path)))
    except OSError:
        return False
    held = data.decode("utf-8", "surrogateescape")
    return held.replace("\r\n", "\n") == text.replace("\r\n", "\n")


def misread(
    rechecks: dict[marker.FindingLine, products.Recheck], priors: Priors, top: str, head: str
) -> set[str]:
    """The findings that a re-check calls fixed, but for those whose file, as a believed comment
    names it, passes as_at_head()."""
    paths = {prior.key: prior.path for prior in priors.believed}
    fixed = {at.key for at, recheck in rechecks.items() if recheck.fixed}
    return {key for key in fixed if not (key in paths and as_at_head(top, head, paths[key]))}


# The seconds that git gets to diff the pull request, and for each step that tries a fix's patch.
PATIENCE_S = 300
# A diff in the form that unidiff reads, with hunks as GitHub's diff of a pull request has them.
DIFF = (
    "-c",
    "diff.suppressBlankEmpty=false",
    "diff",
    *git.PLAIN_DIFF,
    "--src-prefix=a/",
    "--dst-prefix=b/",
    "-U3",
    "--inter-hunk-context=0",
    "--ignore-submodules=none",
    "--submodule=short",
    git.NO_ORDER_FILE,
)


def applied_patches(report: Report) -> dict[str, str]:
    """git's own diff of each finding's patch applied to this head, by finding id, for every
    patch a suggestion may be offered from; a patch git did not apply is left out."""
    found: dict[str, str] = {}
    for item in report.findings:
        patch = report.patches.get(item.id)
        file = patch.offerable(report.commit) if patch else None
        if file is None:
            continue
        diff = as_git_applies(report, file)
        if diff is None:
            console.warn(
                f"{item.id}: git did not apply {file.name} to this commit, or ran out of time "
                f"({PATIENCE_S} seconds), so the fix cannot be a one-click change"
            )
        else:
            found[item.id] = diff
    return found


def pull_request_spans(top: str, merge_base: str, head: str) -> review.Spans:
    """Per repository path, the new-side line ranges of the pull request's diff hunks."""
    text = git.run(top, *DIFF, merge_base, head, "--", env=NO_FETCH, timeout=PATIENCE_S)
    if text is None:
        width = plugin.SHORT_ID_CHARS
        msg = (
            f"git could not diff {merge_base[:width]}..{head[:width]}: this "
            "checkout does not hold all of both commits, or git ran out of time "
            f"({PATIENCE_S} seconds). Check out with `fetch-depth: 0`, as the sample workflow in "
            "this action's CI.md does, and run the job again."
        )
        raise ReviewError(msg)
    return review.spans_of(text)


def as_git_applies(report: Report, patch_file: Path) -> str | None:
    """The patch as git applies it to this head, as git's own diff of the result against the
    commit; None when git did not apply it there, or ran out of time. OSError where its scratch
    folder cannot be made. The repository's working tree, index, refs and object contents are left
    as they are."""
    objects = git.run(report.top, "rev-parse", "--git-path", "objects")
    if objects is None:
        return None
    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)
        (scratch / "objects").mkdir()
        env = {
            "GIT_INDEX_FILE": str(scratch / "index"),
            "GIT_OBJECT_DIRECTORY": str(scratch / "objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(Path(report.top, objects).resolve()),
        }
        run_git = functools.partial(git.run, report.top, env=env, timeout=PATIENCE_S)
        steps = (("read-tree", report.commit), ("apply", "--cached", str(patch_file.resolve())))
        if any(run_git(*step) is None for step in steps):
            return None
        return run_git(*DIFF, "--cached", report.commit, "--")


REFUSED = range(HTTPStatus.BAD_REQUEST, HTTPStatus.INTERNAL_SERVER_ERROR)
REFUSALS: dict[int, str] = {
    HTTPStatus.UNAUTHORIZED: "GitHub did not recognise the job's token",
    HTTPStatus.FORBIDDEN: (
        "most often this means the job's token is not allowed to write to pull requests, which "
        "the workflow grants with `pull-requests: write` under `permissions:`"
    ),
    HTTPStatus.NOT_FOUND: "the job's token cannot see this pull request",
    HTTPStatus.UNPROCESSABLE_ENTITY: (
        f"one cause is a pending review under {marker.POSTER_LOGIN}, which only that account can "
        "see. Run the job again after a workflow submits or deletes it, or open a new pull "
        "request. Another cause is a force-push that removed the scanned commit. In that case, "
        "see the run that the push started."
    ),
}


@final
class ReviewRejectedError(ReviewError):
    """GitHub did not accept the review; `complaint` is gh's one line and `status` the HTTP
    status it named, if any. The message says whether the review can be on the pull request:
    a 4xx is taken for a refusal, anything else may have posted it."""

    def __init__(self, complaint: str, status: int | None) -> None:
        if status is not None and status in REFUSED:
            why = REFUSALS.get(status)
            outcome = "nothing was posted" + (f": {why}" if why else "")
        else:
            outcome = (
                "it may be on the pull request already, so look there before running the job again"
            )
        super().__init__(f"GitHub did not accept the review: {complaint}; {outcome}")
        self.complaint = complaint
        self.status = status


def post(pr: PullRequest, request: review.Request, cli: Gh) -> Recorded | None:
    """Post the review and return its record, as GitHub answers; None where the answer does not read
    as one. ReviewRejectedError when GitHub does not accept the review."""
    endpoint = f"repos/{pr.repository}/pulls/{pr.number}/reviews"
    body = strictjson.text(request)
    fields = f"[.] | {marker.REVIEW_FIELDS}"
    run = cli.run("api", "--method", "POST", endpoint, "--input", "-", "--jq", fields, stdin=body)
    if run.code != 0:
        raise ReviewRejectedError(run.complaint(), run.status)
    answer = run.all_records()
    return Recorded.of(answer[0]) if answer else None


def announce(outcome: verdict.Verdict, runner: actions.Runner | None) -> None:
    """Print the verdict, and with a runner leave it where later workflow steps read it.
    actions.JobError when it cannot be left there."""
    print(f"verdict: {outcome.word} ({outcome.reason})")
    if runner is not None and not runner.write_verdict(outcome.lines()):
        msg = (
            "the verdict file could not be written, so the job's later steps read no verdict and "
            "the check fails: RUNNER_TEMP is unset or empty, or a warning in this step's log says "
            "why"
        )
        raise actions.JobError(msg)


def load_report(
    report_dir: Path,
    stamp: products.Stamp,
    scan_root: str,
    *,
    fixes: bool,
    drafted: Path | None = None,
) -> Report:
    """Everything the review is built from; refused when it is not a rendered changes scan whose
    merge base the checkout at `scan_root` holds, or when Report.load refuses its finding records.
    `fixes` says whether this job drafts fixes, and `drafted` is as in Report.load."""
    change = stamp.change()
    top = git.toplevel(scan_root)
    if not top:
        msg = f"git could not read a work tree at {scan_root}"
        raise ReviewError(msg)
    resolved = git.commit_id(top, change.merge_base)
    if not resolved:
        short = change.merge_base[: plugin.SHORT_ID_CHARS]
        msg = f"the merge base {short} is not a commit in this checkout, or git ran out of time"
        raise ReviewError(msg)
    return Report.load(
        report_dir, stamp, top=top, merge_base=resolved, fixes=fixes, drafted=drafted
    )


def write_review(report_dir: Path, text: str) -> None:
    """Write REVIEW.md into the report directory, in place of an earlier one, which stays as it was
    if the write fails. OSError if the write fails, or if anything but a regular file, including a
    link to one, has that name when the write starts."""
    plain.write_bytes(report_dir / review.REVIEW_NAME, text.encode("utf-8", "backslashreplace"))


def refuse_another_scan(
    stamp: products.Stamp, job: Job, change_scan_effort: ChangeScanEffort
) -> None:
    """Refuse a report that is not of the scan this job is for: of the pull request's changes, at
    the job's `change_scan_effort`, or, with no pull request, of the branch, and in both cases with
    no scope, from the repository's top folder."""
    wanted = "changes" if job.reviews else "scan"
    if stamp.mode not in {wanted, plugin.STAMP_MODES[wanted]} or stamp.scoped:
        whole = "the pull request's changes" if job.reviews else "the whole branch"
        msg = (
            f"the revision stamp does not record the scan that this job is for, a scan of {whole}, "
            "with no scope, from the repository's top folder. Nothing is posted or recorded. Run "
            "the job again."
        )
        raise ReviewError(msg)
    if job.reviews and stamp.change_scan_effort is not change_scan_effort:
        high = change_scan_effort is ChangeScanEffort.HIGH
        left_out, shows = ("", "does not show") if high else ("; low when left out", "shows")
        msg = (
            f"this job asks for Change Scan Effort {change_scan_effort.value} (the input "
            f"change_scan_effort{left_out}), but the scan's report {shows} a scan at "
            f"{ChangeScanEffort.HIGH.value}. This usually happens when the AI session that runs "
            "the scan does not follow the job's setting. No review is posted. Run the job again."
        )
        if high:
            msg += " If it fails this way again, set change_scan_effort to low."
        raise ReviewError(msg)


def refuse_a_lower_effort(stamp: products.Stamp, scan_root: str) -> None:
    """Refuse a report that records no effort tier, or a lower one than the probe's answer in
    `scan_root` names, and any report where the answer names no tier. With no answer there, nothing
    is refused. OSError where it cannot be read."""
    try:
        answer = strictjson.loads(plain.read_text(Path(scan_root, ".git", plugin.PROBE_NAME)))
        named = Effort(strictjson.as_map(answer).get("effort"))
    except FileNotFoundError:
        return
    except ValueError as error:
        msg = (
            f"could not read the effort tier in .git/{plugin.PROBE_NAME}. Nothing is posted or "
            "recorded. Run the job again."
        )
        raise ReviewError(msg) from error
    wanted = Effort.HIGH if named is Effort.MAX else named
    tiers = list(Effort)
    if stamp.effort is None or tiers.index(stamp.effort) < tiers.index(wanted):
        shown = stamp.effort.value if stamp.effort else "no effort tier"
        msg = (
            f"this job asks for a scan at {wanted.value} effort, but the scan's report shows "
            f"{shown}. This usually happens when the AI session that runs the scan does not follow "
            "the job's setting. Nothing is posted or recorded. Run the job again."
        )
        raise ReviewError(msg)


def run(
    report_dir: Path,
    scan_root: str,
    settings: actions.Settings,
    job: Job | None,
    cli: Gh | None,
    drafted: Path | None = None,
) -> None:
    """Write REVIEW.md, and under GitHub Actions post the review; for a job that reviews no pull
    request, run_for_ref() alone. A job first refuses a report of another scan, commit or merge
    base than it is for and, where it scanned, one below its effort tier. `drafted` is given
    where the report was handed over: the folder with the fixes for it. The review then brings
    the fixes, and has no verdict line. Where it offers none it is not posted. Where that folder
    holds no patch record, and earlier comments do not offer every fix, ReviewError. In a re-run
    of such a job, ReviewError also where review.lowers_a_grade() holds."""
    stamp = products.Stamp.read(report_dir)
    if job is not None:
        refuse_another_scan(stamp, job, settings.change_scan_effort)
        if drafted is None:
            refuse_a_lower_effort(stamp, scan_root)
        job.refuse_stale(stamp.commit)
        if not job.reviews:
            run_for_ref(report_dir, stamp, job, settings.fail_on)
            return
    fixes = drafted is not None or settings.suggest_patches is SuggestPatches.TRUE
    report = load_report(report_dir, stamp, scan_root, fixes=fixes, drafted=drafted)
    if job is not None and report.merge_base != job.merge_base:
        width = plugin.SHORT_ID_CHARS
        msg = (
            f"the scan started from {report.merge_base[:width]}, not the pull request's merge base "
            f"{job.merge_base[:width]}. No review is posted. Run the job again."
        )
        raise ReviewError(msg)
    spans = pull_request_spans(report.top, report.merge_base, report.commit)
    pr = job.pull_request if job else None
    home = f"{job.server_url}/{pr.repository}" if job and pr else None
    newest: dict[marker.FindingLine, Prior] = {}
    found = review.PreviousFindings([], [], [], [])
    if job is not None and pr is not None and cli is not None:
        listed = prior_findings(pr, job.run_id, cli, scan_root)
        may_be_old = drafted is not None and job.rerun
        if may_be_old and review.lowers_a_grade(report, listed.believed):
            msg = (
                "this job is a re-run, and its report can be out of date: a comment with a "
                "receipt on one of its findings gives a higher severity or confidence. No review "
                "is posted. To get new fixes, push a commit."
            )
            raise ReviewError(msg)
        earlier = at_head(listed, scan_root, pr.head_sha)
        newest = earlier.answering()
        rechecks = products.rechecks(report_dir)
        found = review.previous_findings_report(
            earlier,
            report,
            rechecks,
            spans=spans,
            misread=misread(rechecks, listed, report.top, pr.head_sha),
        )
    graded = [item.graded for item in report.findings] + found.graded
    outcome = verdict.Verdict.of(
        graded,
        status=stamp.status,
        lost=stamp.lost,
        policy=settings.fail_on,
        older=report.older_listed > 0,
    )
    if job is None:
        announce(outcome, None)
    inputs = review.Inputs(
        spans=spans,
        home=home,
        previous=found.bullets if drafted is None else [],
        applied=applied_patches(report),
        version=plugin.version(),
        base_change=pr.base_change if pr else None,
        verdict_line=last_line(pr, outcome, settings) if pr and drafted is None else None,
        model=actions.model_setting(os.environ),
        fixes_later=drafted is None and settings.suggest_patches is SuggestPatches.LATER,
        fixes_only=drafted is not None,
        newest=newest,
    )
    if inputs.fixes_later and review.all_fixes_offered(report, inputs):
        if report.findings:
            print("an earlier comment offers every fix, so the report is not handed over")
        inputs = inputs._replace(fixes_later=False)
    if report.fixes and not review.describes_fixes(report, inputs):
        if drafted is not None:
            msg = (
                "no patch record could be read from the session's output, so no fix was drafted. "
                "The review of the scan stands. If the reason is temporary, run this job again."
            )
            raise ReviewError(msg)
        console.warn("suggested fixes are on but no patch record was read, so none is offered")
    built = review.build_review(report, inputs, to_body=False)
    text = review.review_markdown(built)
    write_review(report_dir, text)
    print(f"wrote {review.REVIEW_NAME} into {report_dir}")
    for line in [*built.placements, *found.spoken]:
        print(gfm.plain_line(line))
    if job is None or pr is None or cli is None:
        print("not posted: not running under GitHub Actions")
        return
    job.runner.append_summary(text)
    if drafted is not None and not built.offers_fix:
        print("not posted: this review offers no fix")
        job.runner.append_summary("\n_Not posted: this review offers no fix._\n")
        return
    sent, posting = built, inputs
    if drafted is None:
        check_line = review.check_line(outcome, report, settings.fail_on, found)
        posting = inputs._replace(check_line=check_line)
        sent = review.build_review(report, posting, to_body=False)
    try:
        posted = post(pr, review.payload(sent, pr.head_sha), cli)
    except ReviewRejectedError as rejected:
        if not (sent.comments and rejected.status == HTTPStatus.UNPROCESSABLE_ENTITY):
            raise
        why = rejected.complaint
        print(f"GitHub rejected the inline comments ({why}); posting again with no inline comment")
        folded = review.review_markdown(review.build_review(report, inputs, to_body=True))
        write_review(report_dir, folded)
        job.runner.replace_summary(folded)
        sent = review.build_review(report, posting, to_body=True)
        posted = post(pr, review.payload(sent, pr.head_sha), cli)
    shown = (posted.url if posted else "") or pr.url or "the pull request"
    print(f"posted the review: {shown}")
    posted_line = f"\n_Posted as a review on the pull request: {shown}_\n"
    job.runner.append_summary(posted_line)
    announce(outcome, job.runner)
    job.runner.replace_summary(review.review_markdown(sent))
    job.runner.append_summary(posted_line)
    if drafted is None:
        record_report(job.runner, report_dir, stamp, withheld=report.withheld)
    if posted and (inputs.verdict_line is None or posted.has_a_line()):
        hand_over(job.runner, report_dir, report, inputs)
        named = receipt.name(posted, sent.comments)
        job.runner.set_outputs({"receipt": named, "in_run": receipt.in_run(job.run_id, named)})
    else:
        not_handed = (
            ", and the report is not handed over, so no fix is drafted"
            if inputs.fixes_later
            else ""
        )
        answer = "lacks the verdict line" if posted else "could not be read"
        console.warn(
            f"GitHub's answer to the review {answer}, so the review gets no receipt, and later "
            f"runs will only count its comments in the check{not_handed}"
        )


def hand_over(
    runner: actions.Runner, report_dir: Path, report: Report, inputs: review.Inputs
) -> None:
    """Set the step output hand_over where a later job drafts fixes: run() has left
    inputs.fixes_later false where there is no fix to draft. A report whose write-ups are withheld
    stays on the runner. So does one whose folder holds a link, anything else that is neither a
    regular file nor a folder, a folder that cannot be listed, or anything beside the report
    directory, and a warning says so."""
    if not inputs.fixes_later:
        return
    if report.withheld:
        print("the report withholds its write-ups, so it is not handed over, and no fix is drafted")
        return
    folder = report_dir.parent
    if not plain.all_plain(folder):
        why = (
            "holds a link, something that is neither a regular file nor a folder, or a folder that "
            "cannot be listed"
        )
    elif [entry.name for entry in folder.iterdir()] != [report_dir.name]:
        why = "holds something beside the report"
    else:
        runner.set_outputs({"hand_over": "true"})
        return
    console.warn(f"the report's folder {why}, so it is not handed over, and no fix is drafted")


def too_much_unread(report_dir: Path) -> str:
    """Why, by the stamp's run_shape, the scan's SARIF log should not replace an earlier scan's: a
    listed folder is in no component that the scan kept and in no skip, or the component
    researchers' accounts, with no list cut, name as read fewer than half of the files in the
    components. Empty otherwise."""
    path = next(filter(plugin.is_revision_stamp, report_dir.iterdir()))
    shape = as_map(as_map(strictjson.loads(plain.read_text(path))).get("run_shape"))
    if shape.get("completeness_check_outcome") == "partial":
        return (
            "the scan's records list a folder that is in no component that it kept and in no skip"
        )
    counts = as_map(shape.get("research_coverage"))
    read, not_reached, unaccounted = (
        as_int(counts.get(key)) for key in ("read", "not_reached", "unaccounted")
    )
    if counts.get("capped") is True or not_reached + unaccounted <= read:
        return ""
    return (
        "the component researchers' accounts name as read fewer than half of the files in the "
        f"components ({read} read, {not_reached} declared not reached, {unaccounted} in no "
        "account; a larger `model` or a higher `scan_effort` may read more)"
    )


def record_report(
    runner: actions.Runner, report_dir: Path, stamp: products.Stamp, *, withheld: bool
) -> None:
    """Record the report's directory for the job's later steps, when the report's checks passed
    (Stamp.verified), no research agent's reading is missing, the checkout was not sparse and
    too_much_unread() gives no reason, unless actions.Runner.record_report_dir refuses it. Print
    that it is recorded, or why it is not. The job summary also gets too_much_unread()'s reason."""
    if stamp.sparse:
        why = "the job's checkout was sparse"
    elif not stamp.verified:
        reason = f": {stamp.reason}" if stamp.reason_shown(withheld=withheld) else ""
        why = f"the report's verification status is {stamp.status.value}{reason}"
    elif stamp.lost:
        why = verdict.reading_missing(stamp.lost)
    elif why := too_much_unread(report_dir):
        runner.append_summary(
            f"\n**Claude Security plugin warning:** later steps find no report: {why}. The scan's "
            "SARIF log could close code scanning alerts in code that it may not have read.\n"
        )
    else:
        if runner.record_report_dir(report_dir, stamp.total):
            print("recorded the report directory for the job's later steps")
        return
    print(f"{why}, so the report's directory is not recorded for the job's later steps")


def run_without_changes(scan_root: str, job: Job) -> None:
    """For a pull request whose diff has no files: with nothing to scan, the verdict is a
    pass with no findings, left where a reviewed report's would be. The emptiness is checked
    against git."""
    merge_base, commit = job.merge_base, job.commit
    words = ("diff", "--ignore-submodules=none", "--name-only", git.NO_ORDER_FILE)
    changed = git.run(scan_root, *words, merge_base, commit, "--")
    if changed is None:
        width = plugin.SHORT_ID_CHARS
        msg = f"git could not compare {merge_base[:width]} with {commit[:width]}"
        raise ReviewError(msg)
    if changed:
        paths, shown = changed.splitlines(), 5
        named = ", ".join(paths[:shown]) + (", ..." if len(paths) > shown else "")
        msg = (
            f"the pull request changes {len(paths)} file{'' if len(paths) == 1 else 's'} "
            f"({named}), so it gets no verdict without a scan's report; a change the scan does "
            "not read, such as a submodule pointer, gets none until a commit changes a file the "
            "scan reads"
        )
        raise ReviewError(msg)
    outcome = verdict.Verdict.nothing_scanned()
    announce(outcome, job.runner)
    job.runner.append_summary(f"{review.REVIEW_HEADING}\n\n{outcome.sentence}\n")


def run_for_ref(report_dir: Path, stamp: products.Stamp, job: Job, policy: verdict.FailOn) -> None:
    """For a job with no pull request (a scheduled or manual branch scan): leave the verdict for
    later steps, put the verdict and the report on the job summary, and record the report's
    directory as record_report() does. A withheld report goes in as its notice and a table of its
    findings; any other whose checks did not all pass is followed by its stamp's reason, if it gives
    one. A report whose records do not fit its stamp is a refusal."""
    rows = products.finding_records(report_dir, stamp)
    items = products.findings_of(rows, stamp)
    graded = [item.graded for item in items]
    count = len(rows)
    print(f"the branch scan holds {count} finding{'' if count == 1 else 's'}")
    withheld = products.withholds(rows, stamp)
    outcome = verdict.Verdict.of(graded, status=stamp.status, lost=stamp.lost, policy=policy)
    announce(outcome, job.runner)
    summary = [f"_{outcome.sentence}_\n", products.report_markdown(report_dir, withheld=withheld)]
    if stamp.sparse:
        summary.insert(1, f"{review.SPARSE}\n")
    if not count and not stamp.refused:
        summary.insert(1, f"{review.NO_ASSURANCE}\n")
    if withheld:
        listed = [(item.withheld(), "") for item in items]
        summary += review.findings_table(listed, fix_column=False)
    job.runner.append_summary("\n".join(summary))
    if why := stamp.reason_shown(withheld=withheld):
        job.runner.append_summary(f"\nThe report is not verified: {why}.\n")
    record_report(job.runner, report_dir, stamp, withheld=withheld)


def finished_report(reports: Path) -> Path | None:
    """The report directory in `reports`, not itself a link, that has the completion mark. None when
    there is none; more than one is a refusal."""
    finished = sorted(
        entry
        for entry in reports.iterdir()
        if plugin.REPORT_DIR_RE.match(entry.name)
        and not link.is_link(entry)
        and os.path.isfile(entry / plugin.COMPLETE_NAME)
    )
    if len(finished) > 1:
        names = ", ".join(report.name for report in finished)
        msg = f"the scan left more than one complete report ({names}), so none is used"
        raise ReviewError(msg)
    return finished[0] if finished else None


def run_without_report(scan_root: str, reports: Path, job: Job | None) -> None:
    """What --finished does when the scan left no complete report in `reports`: the check for an
    empty change on a job that reviews a pull request, and on any other a refusal."""
    left = f"the scan left no complete report in {reports}"
    then = (
        "Run the job again. Of the scan's session, the job's log holds only a summary, so it may "
        "not give the reason."
    )
    if job is None or not job.reviews:
        msg = f"{left}, so there is nothing to review or record. {then}"
        raise ReviewError(msg)
    try:
        run_without_changes(scan_root, job)
    except ReviewError as refused:
        msg = f"{left}. {then} The pull request also cannot pass as an empty change: {refused}"
        raise ReviewError(msg) from refused


class Args(argparse.Namespace):
    scan_root: str = "."
    reports: str = ""
    handed_over: str | None = None
    probe: Effort | None = None


def dispatch(args: Args) -> None:
    """Run the mode the command line names. A pull request job that can post nothing is refused
    first."""
    settings = actions.Settings.from_environment(os.environ)
    job = Job.from_environment(os.environ)
    cli = actions.poster(job) if job and job.reviews else None
    reports = Path(args.reports)
    handed = Path(args.handed_over) if args.handed_over is not None else None
    if args.probe is not None:
        answer = probe(
            args.scan_root, reports, settings, job, cli, args.probe, fixes_only=handed is not None
        )
        print(strictjson.text(answer, indent=2))
        return
    report = finished_report(handed or reports)
    if report is None:
        run_without_report(args.scan_root, handed or reports, job)
    else:
        drafted = reports / report.name if handed else None
        run(report, args.scan_root, settings, job, cli, drafted)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="post_review.py",
        allow_abbrev=False,
        description="Write a pull request review from a changes scan's report and, under GitHub "
        "Actions, post it; or record a branch scan for the job.",
    )
    parser.add_argument(
        "scan_root",
        nargs="?",
        default=".",
        help="the scan root: the current directory when none is named",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--probe",
        type=tier,
        metavar="EFFORT",
        help="describe the job for a scan at this effort tier; refused when it names no tier",
    )
    mode.add_argument(
        "--finished",
        action="store_true",
        help="after the scan: review or record the report it marked complete; with none, pass a "
        "pull request whose diff has no files and refuse any other run",
    )
    parser.add_argument(
        "--reports",
        required=True,
        metavar="DIR",
        help="the folder of the report directory: where the scan makes it or, with --finished, "
        "where it lies after the scan",
    )
    parser.add_argument(
        "--handed-over",
        metavar="SCANNED",
        help="the folder that holds the report that an earlier job handed over: this job only "
        "drafts fixes for it",
    )
    args = parser.parse_args(argv, namespace=Args())
    for folder in (args.scan_root, args.reports, args.handed_over):
        if folder is not None and not os.path.isdir(folder):
            parser.error(f"not a directory: {folder}")
    try:
        dispatch(args)
    except (ReviewError, actions.JobError, products.ProductError, OSError) as error:
        about = "could not read or write a file: " if isinstance(error, OSError) else ""
        runner = actions.Runner.from_environment(os.environ)
        runner.say_stopped("post_review.py", f"{about}{error}")
        return 1
    return 0


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:]))
