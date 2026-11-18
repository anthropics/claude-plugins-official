"""Several commits in one command, and git cannot show one of them: only the
commits the review read are recorded as reviewed."""
import contextlib
import json
import os
import subprocess
import sys
import time

import pytest

from conftest import (
    GIT_ENV, HOOK_SCRIPT, VULN_PY, bash_payload, git, make_repo, metrics_of, run_hook,
)

from diffstate import _load_reviewed_shas

COMMITS = "git commit -qm older && git commit -qm newer"

# The hook, with the diff of one commit hitting the time limit.
_TIMES_OUT = (
    "import os, runpy, subprocess, sys\n"
    "sys.argv = sys.argv[1:]\n"
    "sys.path.insert(0, os.path.dirname(sys.argv[0]))\n"
    "import gitutil\n"
    "real = gitutil._run_diff_bounded\n"
    "def run(cmd, timeout, *a, **k):\n"
    "    if sys.argv[1] in cmd:\n"
    "        cmd, timeout = [sys.executable, '-c', 'import time; time.sleep(60)'], 1\n"
    "    return real(cmd, timeout, *a, **k)\n"
    "gitutil._run_diff_bounded = run\n"
    "runpy.run_path(sys.argv[0], run_name='__main__')\n"
)


@pytest.fixture
def repo(tmp_path):
    r = make_repo(tmp_path / "repo")
    subprocess.run(["git", "init", "-q", "--bare", str(tmp_path / "remote.git")], check=True)
    git(r, "remote", "add", "origin", str(tmp_path / "remote.git"))
    git(r, "push", "-q", "-u", "origin", "main")
    # Reviewed, so that only the commits of the test are looked at.
    run_sha = git(r, "rev-parse", "HEAD").strip()
    (r / ".git" / "sg-reviewed-shas").write_text(f"{run_sha}\t0\t0\t0\n")
    return r


def _quiet_commit(repo, name):
    (repo / f"{name}.py").write_text(VULN_PY + f"# MARK_{name}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", name)
    return git(repo, "rev-parse", "HEAD").strip()


def _two_commits(repo):
    return {name: _quiet_commit(repo, name) for name in ("older", "newer")}


@contextlib.contextmanager
def _unreadable(repo, sha, name):
    """git show fails on `sha`, which is still there: a blob of it is not."""
    blob = git(repo, "rev-parse", f"{sha}:{name}.py").strip()
    loose = repo / ".git" / "objects" / blob[:2] / blob[2:]
    away = repo.parent / "blob"
    os.replace(loose, away)
    try:
        yield
    finally:
        os.replace(away, loose)


@contextlib.contextmanager
def _started(payload, env):
    p = subprocess.Popen(
        [sys.executable, str(HOOK_SCRIPT)], stdin=subprocess.PIPE,
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


def _asked(stub_api):
    return any(c.endswith("/v1/messages") for c in stub_api.calls)


def _push(repo):
    r = subprocess.run(["git", "push", "origin", "main"], cwd=repo, capture_output=True,
                       text=True, env={**os.environ, **GIT_ENV})
    assert r.returncode == 0, r.stderr
    return r.stderr


def _commit_hook(repo, env):
    rc, out, err = run_hook(bash_payload(str(repo), COMMITS), env)
    assert rc == 0, err
    return metrics_of(out)


def _sent(stub_api, name):
    return f"MARK_{name}" in "\n".join(stub_api.bodies)


@pytest.mark.parametrize("unread,read", [("older", "newer"), ("newer", "older")])
def test_the_next_push_reviews_the_commit_that_was_not_read(
        repo, hook_env, stub_api, unread, read):
    shas = _two_commits(repo)
    with _unreadable(repo, shas[unread], unread):
        m = _commit_hook(repo, hook_env)
    assert m["reflog_shas_n"] == 2 and m["files_reviewed"] == 1
    assert _sent(stub_api, read) and not _sent(stub_api, unread)
    recorded = _load_reviewed_shas(str(repo))
    assert shas[read] in recorded and shas[unread] not in recorded

    out = _push(repo)
    _, so, _ = run_hook(bash_payload(str(repo), "git push origin main", stderr=out), hook_env)
    # A commit already reviewed before the unread one is left out again.
    assert metrics_of(so)["unreviewed"] == (2 if unread == "older" else 1)
    assert _sent(stub_api, unread)
    assert shas[unread] in _load_reviewed_shas(str(repo))


def test_a_commit_whose_diff_hits_the_time_limit(repo, hook_env, stub_api):
    shas = _two_commits(repo)
    r = subprocess.run(
        [sys.executable, "-c", _TIMES_OUT, str(HOOK_SCRIPT), shas["older"]],
        input=json.dumps(bash_payload(str(repo), COMMITS)), capture_output=True,
        text=True, env=hook_env, timeout=60)
    assert r.returncode == 0, r.stderr
    assert metrics_of(r.stdout)["files_reviewed"] == 1
    recorded = _load_reviewed_shas(str(repo))
    assert shas["newer"] in recorded and shas["older"] not in recorded


def test_the_next_quiet_commit_reviews_it_too(repo, hook_env, stub_api):
    shas = _two_commits(repo)
    with _unreadable(repo, shas["older"], "older"):
        _commit_hook(repo, hook_env)
    later = _quiet_commit(repo, "later")
    _, out, _ = run_hook(bash_payload(str(repo), "git commit -qm later"), hook_env)
    m = metrics_of(out)
    assert m["reflog_shas_n"] == 2 and m["files_reviewed"] == 2
    assert _sent(stub_api, "older") and stub_api.bodies[-1].count("MARK_newer") == 0
    assert {shas["older"], later} <= _load_reviewed_shas(str(repo))


def test_push_in_the_same_command_takes_it_over(repo, hook_env, stub_api):
    shas = _two_commits(repo)
    out = _push(repo)
    payload = bash_payload(str(repo), COMMITS + " && git push origin main",
                           stderr=out, tool_use_id="t1")
    stub_api.delay = 3
    once = repo / ".git" / "sg-hook-once-t1"
    with contextlib.ExitStack() as spawns:
        with _unreadable(repo, shas["older"], "older"):
            commit = spawns.enter_context(_started(payload, hook_env))
            _until(once.exists, "the commit spawn's claim")
            push = spawns.enter_context(_started(payload, hook_env))
            _until(lambda: _asked(stub_api), "the commit review's request")
        commit, push = (metrics_of(p.communicate(timeout=90)[0]) for p in (commit, push))
    assert commit["files_reviewed"] == 1
    assert push["commit_no_verdict"] is True and "skip_reason" not in push
    assert _sent(stub_api, "older")
    assert set(shas.values()) <= _load_reviewed_shas(str(repo))


@pytest.mark.parametrize("unread,unreviewed", [("older", 2), ("newer", 1)])
def test_a_push_during_the_review_waits_only_for_what_it_covers(
        repo, hook_env, stub_api, unread, unreviewed):
    shas = _two_commits(repo)
    out = _push(repo)
    stub_api.delay = 4
    with contextlib.ExitStack() as spawns:
        with _unreadable(repo, shas[unread], unread):
            commit = spawns.enter_context(
                _started(bash_payload(str(repo), COMMITS), hook_env))
            _until(lambda: _asked(stub_api), "the commit review's request")
        markers = {n for n in os.listdir(repo / ".git") if n.startswith("sg-inflight-")}
        assert markers == {"sg-inflight-" + s for n, s in shas.items() if n != unread}
        _, so, _ = run_hook(
            bash_payload(str(repo), "git push origin main", stderr=out), hook_env)
        commit.communicate(timeout=60)
    m = metrics_of(so)
    assert m["unreviewed"] == unreviewed
    # Reviewing the older commit takes the newer one along, waiting or not.
    assert ("inflight_wait_s" in m) == (unread == "newer")
    bodies = "\n".join(stub_api.bodies)
    assert bodies.count("# MARK_older") == 1
    assert bodies.count("# MARK_newer") == (2 if unread == "older" else 1)


def test_a_file_renamed_into_code_is_shown_up_to_the_last_commit_read(
        repo, hook_env, stub_api):
    (repo / "notes.txt").write_text(VULN_PY + "# MARK_notes\n" + "x = 1\n" * 30)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "notes")
    with open(repo / ".git" / "sg-reviewed-shas", "a") as f:
        f.write(git(repo, "rev-parse", "HEAD").strip() + "\t0\t0\t0\n")
    git(repo, "mv", "notes.txt", "newer.py")
    _quiet_commit(repo, "older")
    with open(repo / "newer.py", "a") as f:
        f.write("y = 2\n")
    git(repo, "commit", "-q", "-am", "newer")
    newer = git(repo, "rev-parse", "HEAD").strip()
    with _unreadable(repo, newer, "newer"):
        _commit_hook(repo, hook_env)
    assert _sent(stub_api, "older") and _sent(stub_api, "notes")


def test_every_commit_read(repo, hook_env, stub_api):
    shas = _two_commits(repo)
    m = _commit_hook(repo, hook_env)
    assert m["files_reviewed"] == 2
    assert set(shas.values()) <= _load_reviewed_shas(str(repo))


def test_no_commit_read(repo, hook_env, stub_api):
    sha = _quiet_commit(repo, "only")
    with _unreadable(repo, sha, "only"):
        _, out, _ = run_hook(bash_payload(str(repo), "git commit -qm only"), hook_env)
    m = metrics_of(out)
    assert m["skip_reason"] == 28
    assert sha not in _load_reviewed_shas(str(repo))
