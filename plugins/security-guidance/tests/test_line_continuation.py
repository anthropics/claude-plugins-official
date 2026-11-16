"""A git command continued on the next line is still a commit or a push."""
import time

import pytest

from conftest import bash_payload, commit_file, git, make_repo, metrics_of, run_hook

import security_reminder_hook as hook
from diffstate import _load_reviewed_shas


@pytest.mark.parametrize("command", [
    "git \\\n  commit -m x",
    "git \\\r\n  commit -m x",
    "git `\r\n  commit -m x",
    "git -C \\\n . commit",
    "git \\\n  -c user.name='A B' \\\n  --no-pager \\\n  commit -m x",
    "git --git-dir \\\n .git commit",
    "gt \\\n  create x",
    "# kept in C:\\temp\\\ngit commit -m x",
    "git commit \\\n  -m x",
])
def test_is_a_commit(command):
    assert hook._GIT_COMMIT_RE.search(command)


@pytest.mark.parametrize("command", [
    "git \\\n  push origin main", "git -C x `\n push", "gt \\\n submit", "echo a\\\ngit push",
])
def test_is_a_push(command):
    assert hook._GIT_PUSH_RE.search(command)


@pytest.mark.parametrize("command", [
    "git log \\\n  commit", "git \\ commit", "git \\\n  --help commit", "git \\\n  commit-graph write",
    "git log `date`\ncommit", "legit\\\ncommit",
])
def test_is_neither(command):
    assert not hook._GIT_COMMIT_RE.search(command)
    assert not hook._GIT_PUSH_RE.search(command)


def test_continued_gt_modify_is_an_amend():
    assert hook._GIT_AMEND_RE.search("gt \\\n  modify -m x")


def test_long_command_is_matched_quickly():
    for part in (" \\\n", " -c \\\n", " -c a=b \\\n", " --x \\\n", "\\\n", " `\n-p"):
        start = time.monotonic()
        hook._GIT_COMMIT_RE.search("git" + part * 3000 + " x")
        assert time.monotonic() - start < 2


@pytest.mark.parametrize("tool, command", [
    ("Bash", "git \\\n  commit -m change"),
    ("Bash", "git -c core.abbrev=12 \\\n  commit -m change"),
    ("PowerShell", "git `\n  commit -m change"),
    ("Bash", "cd .. && git -C \\\n  repo \\\n  commit -m change"),
])
def test_continued_commit_is_reviewed(tmp_path, hook_env, stub_api, tool, command):
    repo = make_repo(tmp_path / "repo")
    sha, out = commit_file(repo, "a.py", "print('a')\n")
    payload = {**bash_payload(str(repo), command, out), "tool_name": tool}
    _, so, _ = run_hook(payload, hook_env)
    assert metrics_of(so).get("commit_review") is True
    assert sha in _load_reviewed_shas(str(repo))


def test_continued_push_is_reviewed(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo")
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")
    base = git(repo, "rev-parse", "HEAD").strip()
    sha, _ = commit_file(repo, "a.py", "print('a')\n")
    git(repo, "push", "-q", "origin", "main")
    out = f"To {remote}\n   {base[:7]}..{sha[:7]}  main -> main\n"
    _, so, _ = run_hook(bash_payload(str(repo), "git \\\n  push origin main", out), hook_env)
    assert metrics_of(so).get("push_sweep") is True
    assert sha in _load_reviewed_shas(str(repo))
