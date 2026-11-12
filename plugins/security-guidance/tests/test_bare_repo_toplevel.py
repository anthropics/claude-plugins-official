"""The plugin only treats ordinary checkouts as repositories to run git in."""
import os
import subprocess

import pytest

from conftest import GIT_ENV, git, make_repo

import gitutil


def _run(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}, check=True).stdout


@pytest.fixture
def carried(tmp_path):
    d = tmp_path / "project" / "src"
    d.mkdir(parents=True)
    _run(d, "init", "-q", "-b", "main", "--bare", ".")
    _run(d, "config", "core.bare", "false")
    _run(d, "config", "core.worktree", ".")
    return d


def test_folder_without_its_own_git_entry_is_not_a_repo(carried):
    assert gitutil._git_toplevel(str(carried)) is None
    assert gitutil._git_toplevel_and_head(str(carried)) == (None, None)


def test_ordinary_checkout(tmp_path):
    r = make_repo(tmp_path / "repo")
    assert os.path.samefile(gitutil._git_toplevel(str(r)), r)


def test_linked_worktree_of_a_bare_repo(tmp_path):
    src = make_repo(tmp_path / "repo")
    bare = tmp_path / "store.git"
    _run(tmp_path, "clone", "-q", "--bare", str(src), str(bare))
    wt = tmp_path / "wt"
    _run(bare, "worktree", "add", "-q", str(wt), "main")
    assert os.path.samefile(gitutil._git_toplevel(str(wt)), wt)


def test_repo_named_by_the_environment(carried, monkeypatch):
    monkeypatch.setenv("GIT_DIR", str(carried))
    assert gitutil._git_toplevel(str(carried)) is not None
