"""A command that both commits and pushes can send out other commits too.

The commit review sees only the commit the command made, and no later push
covers what is already behind the upstream, so the second start of the hook
for such a command runs the push review when something else went out.
"""
import os
import subprocess

import pytest

from conftest import GIT_ENV, bash_payload, commit_file, git, make_repo, metrics_of, run_hook

import security_reminder_hook as hook
from diffstate import _append_reviewed_shas

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
