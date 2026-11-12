"""A command that both commits and pushes can send out other commits too.

The commit review sees only the commit the command made, and no later push
covers what is already behind the upstream, so the second start of the hook
for such a command runs the push review when something else went out.
"""
import contextlib
import errno
import json
import os
import subprocess
import sys
import time

import pytest

from conftest import (
    GIT_ENV, HOOK_SCRIPT, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
)

import diffstate
import security_reminder_hook as hook
from diffstate import _append_reviewed_shas, _load_reviewed_shas

CMD = "git add -A && git commit -m new && git push"


def _run(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                       env={**os.environ, **GIT_ENV})
    return r.stdout, r.stderr


@pytest.fixture
def repo(tmp_path):
    r = make_repo(tmp_path / "repo")
    subprocess.run(["git", "init", "-q", "--bare", str(tmp_path / "remote.git")], check=True)
    git(r, "remote", "add", "origin", str(tmp_path / "remote.git"))
    git(r, "push", "-q", "-u", "origin", "main")
    return r


def _commit_and_push(repo, name="new.py"):
    (repo / name).write_text("print('new')\n")
    git(repo, "add", "-A")
    out, err = _run(repo, "commit", "-m", "new")
    pout, perr = _run(repo, "push")
    return out + pout, err + perr


def _beyond(repo, output):
    pushed = git(repo, "rev-list", "@{u}@{1}..HEAD").split()
    return hook._pushed_beyond_commit_review(str(repo), pushed, output)


def _three_starts(repo, env, command, out, err):
    payload = bash_payload(str(repo), command, stdout=out, stderr=err, tool_use_id="t1")
    return [metrics_of(run_hook(payload, env)[1]) for _ in range(3)]


def test_older_unreviewed_commit_is_beyond_the_commit_review(repo):
    commit_file(repo, "older.py", "print('older')\n", "older")
    out, err = _commit_and_push(repo)
    assert _beyond(repo, out + err)


def test_only_the_new_commit_is_covered(repo):
    out, err = _commit_and_push(repo)
    assert not _beyond(repo, out + err)


def test_older_commit_already_reviewed_is_covered(repo):
    commit_file(repo, "older.py", "print('older')\n", "older")
    _append_reviewed_shas(str(repo), [git(repo, "rev-parse", "HEAD").strip()])
    out, err = _commit_and_push(repo)
    assert not _beyond(repo, out + err)


def test_earlier_commit_of_the_same_command_is_not_covered(repo):
    (repo / "a.py").write_text("print('a')\n")
    git(repo, "add", "-A")
    out1, _ = _run(repo, "commit", "-m", "one")
    out, err = _commit_and_push(repo)
    assert _beyond(repo, out1 + out + err)


def test_hidden_commit_line_uses_the_reflog(repo):
    _, err = _commit_and_push(repo)
    assert not _beyond(repo, err)


def test_commit_review_switched_off_covers_nothing(repo, monkeypatch):
    out, err = _commit_and_push(repo)
    monkeypatch.setattr(hook, "COMMIT_REVIEW_ENABLED", False)
    assert _beyond(repo, out + err)


def test_second_start_runs_the_push_review_for_older_commits(repo, env):
    commit_file(repo, "older.py", "print('older')\n", "older")
    out, err = _commit_and_push(repo)
    first, second, third = _three_starts(repo, env, CMD, out, err)
    assert first.get("commit_review") is True
    assert second.get("push_sweep") is True and second.get("skip_reason") != 47
    assert third.get("bash_hook_dedup") is True


def test_second_start_reviews_nothing_for_the_new_commit_alone(repo, env):
    out, err = _commit_and_push(repo)
    first, second, _ = _three_starts(repo, env, CMD, out, err)
    assert first.get("commit_review") is True
    assert second.get("skip_reason") == 47


def test_plain_commit_second_start_is_deduped(repo, env):
    (repo / "x.py").write_text("print(1)\n")
    git(repo, "add", "-A")
    out, err = _run(repo, "commit", "-m", "x")
    first, second, _ = _three_starts(repo, env, "git commit -m x", out, err)
    assert first.get("commit_review") is True
    assert second.get("bash_hook_dedup") is True


# The push spawn waits for the commit spawn, and takes over what it gave no
# verdict on.

@contextlib.contextmanager
def _spawn(payload, env):
    p = subprocess.Popen([sys.executable, str(HOOK_SCRIPT)], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    try:
        p.stdin.write(json.dumps(payload))
        p.stdin.close()
        p.stdin = None
        yield p
    finally:
        if p.poll() is None:
            p.kill()
        p.communicate()


def _until(cond, what, timeout=30):
    end = time.time() + timeout
    while not cond():
        assert time.time() < end, f"timed out waiting for {what}"
        time.sleep(0.05)


def _both_spawns(repo, env, out, err, meanwhile=lambda commit: None, command=CMD):
    """The two spawns of one call, the commit spawn first. Returns the commit
    spawn's (exit code, metrics, stderr), then the push spawn's."""
    payload = bash_payload(str(repo), command, stdout=out, stderr=err, tool_use_id="t1")
    with _spawn(payload, env) as commit:
        _until(lambda: (repo / ".git" / "sg-hook-once-t1").exists(), "the commit spawn's claim")
        with _spawn(payload, env) as push:
            _until(lambda: (repo / ".git" / "sg-hook-once-t1-push").exists(),
                   "the push spawn's claim")
            meanwhile(commit)
            ends = []
            for p in (commit, push):
                so, se = p.communicate(timeout=90)
                ends.append((p.returncode, metrics_of(so), se))
    return ends


def _reviews(stub_api):
    return len([c for c in stub_api.calls if c.endswith("/v1/messages")])


def _head(repo):
    return git(repo, "rev-parse", "HEAD").strip()


def test_one_review_while_the_push_spawn_waits(repo, hook_env, stub_api):
    out, err = _commit_and_push(repo)
    stub_api.delay = 4
    commit, push = _both_spawns(repo, hook_env, out, err)
    assert commit[1]["commit_review"] is True and "skip_reason" not in commit[1]
    assert push[1]["skip_reason"] == 47 and push[1]["inflight_wait_s"] >= 1
    assert "commit_no_verdict" not in push[1]
    assert _reviews(stub_api) == 1


def test_failed_commit_review_is_taken_over(repo, hook_env, stub_api):
    out, err = _commit_and_push(repo)
    stub_api.fail_first, stub_api.delay = 2, 1  # the review and its retry
    commit, push = _both_spawns(repo, hook_env, out, err)
    # The push review reports, so the commit review does not.
    assert commit[0] == 0 and commit[1]["review_failed"] is True and not commit[2]
    assert push[1]["commit_no_verdict"] is True and push[1]["unreviewed"] == 1
    assert "skip_reason" not in push[1] and _reviews(stub_api) == 3
    assert _head(repo) in _load_reviewed_shas(str(repo))


def test_killed_commit_review_is_taken_over(repo, hook_env, stub_api):
    out, err = _commit_and_push(repo)
    stub_api.delay = 6

    def kill(commit):
        _until(lambda: _reviews(stub_api) == 1, "the commit review's request")
        commit.kill()

    _, push = _both_spawns(repo, hook_env, out, err, kill)
    assert push[1]["commit_no_verdict"] is True and push[1]["unreviewed"] == 1
    assert _head(repo) in _load_reviewed_shas(str(repo))


def test_take_over_keeps_to_the_commit_review_cap(repo, hook_env, stub_api):
    hook_env["MAX_COMMIT_REVIEWS_PER_HOUR"] = "1"
    _, first = commit_file(repo, "first.py", "print('first')\n", "first")
    run_hook(bash_payload(str(repo), "git commit -m first", first), hook_env)
    out, err = _commit_and_push(repo)
    commit, push = _both_spawns(repo, hook_env, out, err)
    assert commit[1]["skip_reason"] == 23
    assert push[1]["skip_reason"] == 23
    assert _reviews(stub_api) == 1


def test_commit_without_reviewable_files_sends_nothing(repo, hook_env, stub_api):
    out, err = _commit_and_push(repo, "notes.png")
    commit, push = _both_spawns(repo, hook_env, out, err)
    assert commit[1]["skip_reason"] == 30 and push[1]["skip_reason"] == 30
    assert _reviews(stub_api) == 0


def test_message_only_amend_is_not_reviewed_again(repo, hook_env, stub_api):
    _, made = commit_file(repo, "a.py", "print('a')\n", "a")
    run_hook(bash_payload(str(repo), "git commit -m a", made), hook_env)
    out, err = _run(repo, "commit", "--amend", "-m", "better")
    pout, perr = _run(repo, "push")
    commit, push = _both_spawns(repo, hook_env, out + pout, err + perr,
                                command="git commit --amend -m better && git push")
    assert commit[1]["skip_reason"] == 35 and push[1]["skip_reason"] == 47
    assert _reviews(stub_api) == 1


def test_nothing_is_held_where_files_cannot_be_locked(repo, monkeypatch):
    def no_locks(fd, exclusive):
        raise OSError(errno.ENOLCK, "no locks here")

    path = str(repo / ".git" / "sg-hook-once-t1")
    open(path, "w").close()
    monkeypatch.setattr(diffstate, "_flock_nb", no_locks)
    for p in (path, path + "-missing", None):
        diffstate.hold_until_exit(p)
        assert diffstate.is_held(p) is None
        assert diffstate.wait_for_holder(p, 5) == (False, 0.0)
        assert diffstate.becomes_held(p, 0) is False


def test_wait_for_holder_stops_at_the_limit(tmp_path):
    path = tmp_path / "held"
    path.write_text("")
    script = ("import sys, time\nsys.path.insert(0, sys.argv[2])\nimport diffstate\n"
              "diffstate.hold_until_exit(sys.argv[1])\n"
              "print('held', flush=True)\ntime.sleep(60)\n")
    p = subprocess.Popen([sys.executable, "-c", script, str(path), os.path.dirname(diffstate.__file__)],
                         stdout=subprocess.PIPE, text=True)
    try:
        assert p.stdout.readline().strip() == "held"
        ended, waited = diffstate.wait_for_holder(str(path), 1)
        assert ended is False and waited >= 1
        assert diffstate.is_held(str(path)) is True
        p.kill()
        p.wait()
        assert diffstate.wait_for_holder(str(path), 20) == (True, 0.0)
    finally:
        p.kill()
        p.communicate()


def test_both_reviews_pick_the_same_commits(repo):
    """The output names a commit but has no diffstat: both go by the reflog."""
    (repo / "quiet.py").write_text("print('quiet')\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "quiet")
    out, err = _run(repo, "commit", "--allow-empty", "-m", "marker")
    pout, perr = _run(repo, "push")
    output = out + pout + err + perr
    assert hook._COMMIT_SHA_RE.findall(output) and not hook._commit_in_output(output)
    both = git(repo, "rev-list", "@{u}@{1}..HEAD").split()
    assert hook._commit_review_candidates(output, str(repo))[0][:2] == both
    assert not _beyond(repo, output)


def test_quiet_commit_then_empty_commit_runs_one_review(repo, hook_env, stub_api):
    (repo / "quiet.py").write_text("print('quiet')\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "quiet")
    out, err = _run(repo, "commit", "--allow-empty", "-m", "marker")
    pout, perr = _run(repo, "push")
    stub_api.delay = 2
    commit, push = _both_spawns(
        repo, hook_env, out + pout, err + perr,
        command="git commit -q -m quiet && git commit --allow-empty -m marker && git push")
    assert commit[1]["sha_via_reflog"] is True and push[1]["skip_reason"] == 47
    assert _reviews(stub_api) == 1


def test_slow_commit_review_is_left_alone(repo, hook_env, stub_api):
    """It outlasts the wait: skipped as before, not reviewed twice."""
    out, err = _commit_and_push(repo)
    stub_api.delay = 4
    commit, push = _both_spawns(repo, {**hook_env, "SG_INFLIGHT_WAIT_S": "1"}, out, err)
    assert "skip_reason" not in commit[1] and push[1]["skip_reason"] == 47
    assert "commit_no_verdict" not in push[1]
    assert _reviews(stub_api) == 1


def test_take_over_after_head_moved(repo, hook_env, stub_api):
    """Another commit landed meanwhile: still reviewed, as it was pushed."""
    out, err = _commit_and_push(repo)
    pushed = _head(repo)
    stub_api.fail_first, stub_api.delay = 2, 2

    def move_head(commit):
        _until(lambda: diffstate.is_held(str(repo / ".git" / "sg-hook-once-t1-push")),
               "the push spawn's wait")
        commit_file(repo, "later.py", "print('later')\n", "later")

    _, push = _both_spawns(repo, hook_env, out, err, move_head)
    assert push[1]["commit_no_verdict"] is True and "skip_reason" not in push[1]
    assert "new.py" in stub_api.bodies[-1] and "later.py" not in stub_api.bodies[-1]
    assert _load_reviewed_shas(str(repo)) == {pushed}


def test_no_promise_of_a_push_review_that_ended(repo, hook_env, stub_api):
    """Two branches pushed: that push review skips, and nothing takes over."""
    git(repo, "branch", "side")
    git(repo, "push", "-q", "origin", "side")
    git(repo, "checkout", "-q", "side")
    commit_file(repo, "side.py", "print('side')\n", "side")
    git(repo, "checkout", "-q", "main")
    (repo / "new.py").write_text("print('new')\n")
    git(repo, "add", "-A")
    out, err = _run(repo, "commit", "-m", "new")
    pout, perr = _run(repo, "push", "--all", "origin")
    stub_api.fail_first, stub_api.delay = 2, 2
    commit, push = _both_spawns(repo, hook_env, out + pout, err + perr,
                                command="git commit -m new && git push --all origin")
    assert push[1]["skip_reason"] == 44 and commit[1]["review_failed"] is True
    assert "a later push will not re-check it" in commit[2]


def test_message_only_amend_while_the_original_is_under_review(repo, hook_env, stub_api):
    _, made = commit_file(repo, "a.py", "print('a')\n", "a")
    stub_api.delay = 5
    with _spawn(bash_payload(str(repo), "git commit -m a", made), hook_env):
        _until(lambda: _reviews(stub_api) == 1, "the original's review")
        out, err = _run(repo, "commit", "--amend", "-m", "better")
        pout, perr = _run(repo, "push")
        commit, push = _both_spawns(repo, hook_env, out + pout, err + perr,
                                    command="git commit --amend -m better && git push")
    assert commit[1]["skip_reason"] == 35 and push[1]["skip_reason"] == 47
    assert _reviews(stub_api) == 1


def test_failed_review_at_the_cap_still_reports(repo, hook_env, stub_api):
    """The cap leaves the push review no turn, so the commit review reports."""
    out, err = _commit_and_push(repo)
    stub_api.fail_first, stub_api.delay = 2, 1
    commit, push = _both_spawns(repo, {**hook_env, "MAX_COMMIT_REVIEWS_PER_HOUR": "1"}, out, err)
    assert commit[0] == 2 and "a later push will not re-check it" in commit[2]
    assert push[1]["skip_reason"] == 23


def test_both_reviews_fail(repo, hook_env, stub_api):
    out, err = _commit_and_push(repo)
    stub_api.status = 400
    commit, push = _both_spawns(repo, hook_env, out, err)
    assert commit[0] == 0 and commit[1]["review_failed"] is True
    assert push[0] == 2 and "a later push will not re-check them" in push[2]


def test_older_commit_under_another_review_is_left_to_it(repo, hook_env, stub_api):
    _, made = commit_file(repo, "older.py", "print('older')\n", "older")
    stub_api.delay = 4
    with _spawn(bash_payload(str(repo), "git commit -m older", made), hook_env) as older:
        _until(lambda: _reviews(stub_api) == 1, "the older commit's review")
        out, err = _commit_and_push(repo)
        commit, push = _both_spawns(repo, hook_env, out, err)
        older.communicate(timeout=60)
    assert push[1]["skip_reason"] == 47
    assert _reviews(stub_api) == 2
