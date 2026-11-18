"""Git Bash spells `C:\\x` as `/c/x` (#7161)."""
import ntpath
import os
import types

import pytest

import reporesolve as rr
from conftest import (
    VULN_PY, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
)

windows_only = pytest.mark.skipif(os.name != "nt", reason="drive paths exist on Windows only")


@pytest.mark.parametrize("path,expected", [
    ("/c/Users/me/repo", "c:/Users/me/repo"),
    ("/D/work", "D:/work"),
    ("/c/", "c:/"),
    ("/c", "/c"),
    ("/cc/x", "/cc/x"),
    ("/tmp/x", "/tmp/x"),
    ("/1/x", "/1/x"),
    ("//c/share", "//c/share"),
    ("c/x", "c/x"),
    ("C:/x", "C:/x"),
    ("~/x", "~/x"),
    ("", ""),
])
def test_drive_path(path, expected):
    assert rr._drive_path(path) == expected


@pytest.mark.skipif(os.name == "nt", reason="a one-letter folder at the root is a drive there")
def test_one_letter_folder_stays_a_folder_elsewhere():
    assert rr.dirs_from_command("cd /c/repo && git commit -m x", "/w") == ["/c/repo"]


@pytest.fixture
def as_windows(monkeypatch):
    monkeypatch.setattr(rr, "os", types.SimpleNamespace(
        name="nt", sep="\\", path=ntpath, getcwd=lambda: "C:\\w", environ=os.environ))


SHAPES = [
    "cd /c/a/repo && git commit -m x",
    "pushd /c/a/repo && git commit -m x",
    "cd /c/a && cd repo && git commit -m x",
    "git -C /c/a/repo commit -m x",
    "git --git-dir=/c/a/repo/.git commit -m x",
    "git --git-dir /c/a/repo/.git commit -m x",
    "git --work-tree=/c/a/repo commit -m x",
    "git --work-tree /c/a/repo commit -m x",
]


@pytest.mark.parametrize("command", SHAPES)
def test_bash_command(as_windows, command):
    assert rr.dirs_from_command(command, "D:\\s") == ["c:\\a\\repo"]


@pytest.mark.parametrize("command", SHAPES)
def test_powershell_command_is_left_as_it_is(as_windows, command):
    assert all(not d.startswith("c:\\a") for d in rr.dirs_from_command(command, "D:\\s", bash=False))


@pytest.mark.parametrize("command", [
    "cd /d && git commit -m x", "cd /tmp/repo && git commit -m x", "cd sub && git commit -m x",
])
def test_other_paths_stay(as_windows, command):
    assert rr.dirs_from_command(command, "D:\\s") == rr.dirs_from_command(command, "D:\\s", bash=False)


def test_drive_letter_case_is_not_another_folder(as_windows, monkeypatch):
    monkeypatch.setattr(rr, "_git_toplevel", lambda d: pytest.fail("git was started"))
    assert rr.toplevel_from_command("cd /c/ws && git commit -m x", "C:\\ws", None, "C:/ws") == "C:/ws"


def _bash(path):
    drive, rest = os.path.splitdrive(str(path))
    return "/" + drive[0].lower() + rest.replace("\\", "/")


@windows_only
@pytest.mark.parametrize("shape", [
    'cd "{p}" && git commit -m x',
    'pushd "{p}" && git commit -m x',
    'git -C "{p}" commit -m x',
    'git --git-dir="{p}/.git" --work-tree="{p}" commit -m x',
    '(cd "{p}"; git commit -m x)',
])
def test_command_in_another_repo(tmp_path, shape):
    session, other = tmp_path / "session", tmp_path / "other repo"
    for d in (session, other):
        d.mkdir()
        make_repo(d)
    top, how = rr.resolve_repo_root(str(session), shape.format(p=_bash(other)), rr.COMMIT_SUBCOMMANDS)
    assert how == rr.RES_COMMAND and os.path.samefile(top, other)


@windows_only
def test_powershell_reads_it_as_a_folder_of_the_current_drive(tmp_path):
    session, other = tmp_path / "session", tmp_path / "other"
    for d in (session, other):
        d.mkdir()
        make_repo(d)
    cmd = f'cd "{_bash(other)}"; git commit -m x'
    assert rr.resolve_repo_root(str(session), cmd, bash=False)[1] == rr.RES_CWD


@pytest.fixture
def two_repos(tmp_path):
    session, other = tmp_path / "session", tmp_path / "other"
    for d in (session, other):
        d.mkdir()
        make_repo(d)
    return session, other


@windows_only
@pytest.mark.parametrize("shown", [True, False])
def test_commit_in_another_repo_is_reviewed(two_repos, hook_env, stub_api, shown):
    session, other = two_repos
    _, out = commit_file(other, "app.py", VULN_PY)
    payload = bash_payload(session, f'cd "{_bash(other)}" && git commit -m x', out if shown else "")
    m = metrics_of(run_hook(payload, hook_env)[1])
    assert m.get("skip_reason") is None and m["repo_resolution"] == rr.RES_COMMAND, m
    assert "shell=True" in "".join(stub_api.bodies)


@windows_only
def test_push_in_another_repo_is_reviewed(two_repos, hook_env, stub_api, tmp_path):
    session, other = two_repos
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(other, "remote", "add", "origin", str(remote))
    git(other, "push", "-q", "-u", "origin", "main")
    base = git(other, "rev-parse", "--short", "HEAD").strip()
    sha, _ = commit_file(other, "app.py", VULN_PY)
    git(other, "push", "-q")
    out = f"To {remote}\n   {base}..{sha[:7]}  main -> main\n"
    payload = bash_payload(session, f'cd "{_bash(other)}" && git push', out)
    m = metrics_of(run_hook(payload, hook_env)[1])
    assert m.get("skip_reason") is None and m["repo_resolution"] == rr.RES_COMMAND, m


@windows_only
def test_powershell_call_is_not_mapped(two_repos, hook_env, stub_api):
    session, other = two_repos
    _, out = commit_file(other, "app.py", VULN_PY)
    payload = {**bash_payload(session, f'cd "{_bash(other)}"; git commit -m x', out), "tool_name": "PowerShell"}
    assert metrics_of(run_hook(payload, hook_env)[1]).get("skip_reason") == 28
    assert not any("messages" in c for c in stub_api.calls)
