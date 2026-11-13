"""The plugin only treats ordinary checkouts as repositories to run git in."""
import os
import subprocess

import pytest

from conftest import GIT_ENV, git, make_repo

import diffstate
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


# The tests run without apply_safe_git_env, so git here finds these folders the
# way git before 2.38 does.
@pytest.fixture
def carried_with_filter(carried, tmp_path):
    marker = tmp_path / "filter-ran"
    (carried / "app.py").write_text("print('inner')\n")
    (carried / ".gitattributes").write_text("* filter=probe\n")
    _run(carried, "add", ".gitattributes", "app.py")
    _run(carried, "commit", "-q", "-m", "inner")
    _run(carried, "config", "filter.probe.clean", f"sh -c 'echo x >> \"{marker.as_posix()}\"; cat'")
    (carried / "app.py").write_text("print('chang')\n")  # same size, so git has to hash it
    return carried, marker


def _assert_stays_out(d, marker):
    assert diffstate.capture_git_baseline(str(d)) is None
    assert diffstate._list_untracked(str(d)) == {}
    paths, _base, _repo, untracked, metrics = diffstate.compute_v2_review_set(str(d), "HEAD", None)
    assert (paths, untracked, metrics["review_set_count"]) == ([], [], 0)
    assert not marker.exists()


def test_prompt_and_stop_git_stay_out_of_the_folder(carried_with_filter):
    d, marker = carried_with_filter
    _run(d, "status", "--porcelain")
    assert marker.exists()  # the filter does run for a plain git status here
    marker.unlink()
    _assert_stays_out(d, marker)


def test_folder_whose_work_tree_is_a_real_checkout(tmp_path):
    project = make_repo(tmp_path / "project")
    d = project / "carried"
    d.mkdir()
    _run(d, "init", "-q", "-b", "main", "--bare", ".")
    _run(d, "config", "core.bare", "false")
    _run(d, "config", "core.worktree", "..")
    assert gitutil._git_toplevel(str(d)) is None


def test_no_plugin_records_in_the_folder(carried):
    assert gitutil._git_dir(str(carried)) is None


def test_subfolder_of_the_folder(carried):
    sub = carried / "sub"
    sub.mkdir()
    assert gitutil._found_through_bare_folder(str(sub))


def test_git_dir_with_a_work_tree_elsewhere(tmp_path):
    gd = tmp_path / "gd"
    wt = tmp_path / "wtree"
    gd.mkdir()
    wt.mkdir()
    _run(gd, "init", "-q", "-b", "main")
    _run(gd, "config", "core.worktree", str(wt))
    assert not gitutil._found_through_bare_folder(str(gd))
    assert os.path.samefile(gitutil._git_toplevel(str(gd)), wt)


def test_inside_a_dot_git_directory(tmp_path):
    r = make_repo(tmp_path / "repo")
    assert not gitutil._found_through_bare_folder(str(r / ".git"))


def test_project_folder_named_like_a_repository(tmp_path):
    r = make_repo(tmp_path / "repo")
    d = r / "docs"
    (d / "objects").mkdir(parents=True)
    (d / "refs").mkdir()
    (d / "HEAD").write_text("notes\n")
    assert not gitutil._found_through_bare_folder(str(d))


def test_head_text_that_is_not_a_ref(tmp_path):
    r = make_repo(tmp_path / "repo")
    d = r / "docs"
    (d / "objects").mkdir(parents=True)
    (d / "refs").mkdir()
    (d / "HEAD").write_text("ref: see the notes\n")
    assert not gitutil._found_through_bare_folder(str(d))


@pytest.mark.skipif(os.name == "nt", reason="symbolic links")
def test_head_that_is_a_link_into_refs(carried):
    (carried / "HEAD").unlink()
    os.symlink("refs/heads/main", carried / "HEAD")
    assert gitutil._found_through_bare_folder(str(carried))


@pytest.mark.skipif(os.name == "nt", reason="named pipes")
def test_head_that_is_a_named_pipe_is_not_opened(tmp_path):
    d = tmp_path / "pipe"
    (d / "objects").mkdir(parents=True)
    (d / "refs").mkdir()
    os.mkfifo(d / "HEAD")
    assert not gitutil._looks_like_git_dir(str(d))


def test_commondir_layout(carried):
    (carried / "commondir").write_text("../store\n")
    (carried / "objects").rename(carried.parent / "objects")
    (carried / "refs").rename(carried.parent / "refs")
    assert gitutil._found_through_bare_folder(str(carried))


def test_empty_git_folder_does_not_hide_the_repository(carried):
    (carried / ".git").mkdir()
    assert gitutil._found_through_bare_folder(str(carried))
