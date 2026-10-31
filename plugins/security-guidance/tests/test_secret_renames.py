"""A tracked file renamed away from a secret-shaped name stays out of the
Stop review, however the rename reached git."""
import errno
import os
import subprocess

import pytest

from conftest import (
    GIT_ENV, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
    stop_payload, ups_payload,
)

import diffstate
import gitutil

SECRET_BODY = "".join(f"KEY_{i}=SECRET_VALUE_{i}\n" for i in range(30))
EDIT = "import os\nos.system(input())\n"


def _repo(tmp_path):
    return make_repo(tmp_path / "repo", {"deploy_rsa": SECRET_BODY, "app.py": "x = 1\n"})


def _sent(stub_api):
    return "".join(stub_api.bodies)


def _rename(repo, how):
    if how == "moved":
        os.rename(repo / "deploy_rsa", repo / "settings.py")
        return
    git(repo, "mv", "deploy_rsa", "settings.py")
    if how == "committed":
        git(repo, "commit", "-qm", "rename")
    elif how == "amended":
        git(repo, "commit", "-q", "--amend", "-m", "init, renamed")
        # Edited after the commit, so the file is still part of the turn.
        with open(repo / "settings.py", "a") as f:
            f.write("KEY_NEW=SECRET_VALUE_NEW\n")


@pytest.mark.parametrize("how", ["moved", "staged", "committed", "amended"])
def test_stop_review_leaves_the_renamed_file_out(tmp_path, hook_env, stub_api, how):
    repo = _repo(tmp_path)
    run_hook(ups_payload(repo), hook_env)
    _rename(repo, how)
    (repo / "app.py").write_text(EDIT)
    _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
    m = metrics_of(stdout)
    assert m.get("skip_reason") is None, m
    assert m.get("files_reviewed") == 1
    # A plain mv is not a rename to git: the old name is listed as deleted.
    assert m.get("secret_renamed") == (None if how == "moved" else 1)
    assert "os.system" in _sent(stub_api)
    assert "SECRET_VALUE" not in _sent(stub_api)


def test_stop_review_with_nothing_but_the_rename_sends_nothing(tmp_path, hook_env, stub_api):
    repo = _repo(tmp_path)
    run_hook(ups_payload(repo), hook_env)
    git(repo, "mv", "deploy_rsa", "settings.py")
    _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
    assert metrics_of(stdout).get("skip_reason") == 7
    assert stub_api.bodies == []


def test_commit_review_leaves_the_renamed_file_out(tmp_path, hook_env, stub_api):
    repo = _repo(tmp_path)
    git(repo, "mv", "deploy_rsa", "settings.py")
    _sha, out = commit_file(repo, "app.py", EDIT)
    run_hook(bash_payload(repo, "git commit -m change", stdout=out), hook_env)
    assert "os.system" in _sent(stub_api)
    assert "SECRET_VALUE" not in _sent(stub_api)


@pytest.fixture
def git_env(monkeypatch):
    """The suite's git settings for calls made in this process."""
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(gitutil, "_secret_rename_origins", {})
    monkeypatch.setattr(diffstate, "_secret_rename_origins", gitutil._secret_rename_origins)


def test_listings_are_unchanged_and_note_the_secret_origin(tmp_path, git_env):
    repo = make_repo(tmp_path / "repo", {
        "deploy_rsa": SECRET_BODY, "old name.py": SECRET_BODY + "x = 1\n",
        "gone.py": "x = 1\n", "edit.py": "x = 1\n"})
    git(repo, "mv", "deploy_rsa", "settings.py")
    git(repo, "mv", "old name.py", "new name.py")
    git(repo, "rm", "-q", "gone.py")
    (repo / "edit.py").write_text("x = 2\n")
    names = {"settings.py", "new name.py", "gone.py", "edit.py"}
    assert gitutil._git_name_only(str(repo), "HEAD") == names
    assert gitutil._secret_rename_origins == {"settings.py": "deploy_rsa"}
    gitutil._secret_rename_origins.clear()
    assert gitutil._git_status_porcelain(str(repo)) == (names, set())
    assert gitutil._secret_rename_origins == {"settings.py": "deploy_rsa"}


def test_review_set_gains_only_the_origin_of_a_reviewed_file(tmp_path, git_env):
    repo = make_repo(tmp_path / "repo", {
        "deploy_rsa": SECRET_BODY, "old.py": SECRET_BODY + "x = 1\n"})
    git(repo, "mv", "deploy_rsa", "settings.py")
    git(repo, "mv", "old.py", "new.py")
    paths, _base, root, _untracked, metrics = diffstate.compute_v2_review_set(str(repo), None, None, {})
    assert sorted(os.path.relpath(p, root) for p in paths) == ["deploy_rsa", "new.py", "settings.py"]
    assert metrics["dirty_now_count"] == 2 and metrics["review_set_count"] == 3
    assert metrics["secret_renamed"] == 1


def test_origin_still_pairs_beside_a_nested_repo_and_a_split_path_list(
        tmp_path, git_env, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"deploy_rsa": SECRET_BODY, "app.py": "x = 1\n"})
    make_repo(repo / "nested", {"inner.py": "y = 1\n"})
    git(repo, "mv", "deploy_rsa", "settings.py")
    (repo / "app.py").write_text(EDIT)
    (repo / "a_much_longer_module_name.py").write_text("y = 1\n")
    (repo / "another_quite_long_module_name.py").write_text("y = 2\n")
    for i in range(20):
        (repo / f"note{i:02d}.txt").write_text("x\n")
    paths, base, root, untracked, metrics = diffstate.compute_v2_review_set(str(repo), None, None, {})
    names = [os.path.relpath(p, root) for p in paths]
    assert "deploy_rsa" in names and "settings.py" in names
    assert not any(n.startswith("nested") for n in names)
    assert metrics["secret_renamed"] == 1

    # The OS refuses the one command that holds every path, so the paths go
    # out in several: the old name has to be in the one with the new name.
    real_popen = subprocess.Popen
    limit = sum(len(a) + 1 for a in gitutil.GIT_CMD) + 220
    diffs = []

    def popen(cmd, *args, **kwargs):
        if sum(len(a) + 1 for a in cmd) > limit:
            raise OSError(errno.E2BIG, "Argument list too long")
        if "diff" in cmd:
            diffs.append(cmd)
        return real_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 80)
    diff = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
    assert len(diffs) > 1 and all("deploy_rsa" in c for c in diffs)
    reviewed = gitutil.parse_diff_into_files(diff)
    assert sorted(f for f, _ in reviewed) == [
        "a_much_longer_module_name.py", "another_quite_long_module_name.py", "app.py"]
    assert "SECRET_VALUE" not in "".join(d for _, d in reviewed)
