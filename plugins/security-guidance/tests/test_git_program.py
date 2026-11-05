"""On Windows the hooks name git by its full path, found on PATH, so a git.exe
in the project is not the one that starts."""
import json
import os
import subprocess
import sys

import pytest

from conftest import HOOK_SCRIPT, make_repo, ups_payload, write_cli

import gitutil

windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows program lookup")


def _git_in(d):
    d.mkdir(parents=True, exist_ok=True)
    (d / "git.exe").write_bytes(b"")
    return str(d / "git.exe")


def test_bare_name_outside_windows():
    assert gitutil._git_program(windows=False) == "git"


def test_first_git_on_path(tmp_path, monkeypatch):
    first, second = tmp_path / "a", tmp_path / "b"
    first.mkdir()
    expected = _git_in(second)
    _git_in(tmp_path / "c")
    monkeypatch.setenv("PATH", os.pathsep.join([str(first), str(second), str(tmp_path / "c")]))
    assert gitutil._git_program(windows=True) == expected


def test_working_directory_and_relative_entries_are_left_out(tmp_path, monkeypatch):
    project = tmp_path / "project"
    _git_in(project)
    _git_in(project / "bin")
    expected = _git_in(tmp_path / "installed")
    monkeypatch.chdir(project)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("PATH", os.pathsep.join(
        ["", ".", "bin", str(project), str(project) + os.sep, str(tmp_path / "installed")]))
    assert gitutil._git_program(windows=True) == expected


def test_folder_inside_the_project_is_left_out(tmp_path, monkeypatch):
    project = tmp_path / "project"
    _git_in(project)
    _git_in(project / ".venv" / "Scripts")
    (project / "pkg").mkdir()
    expected = _git_in(tmp_path / "installed")
    monkeypatch.chdir(project / "pkg")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    monkeypatch.setenv("PATH", os.pathsep.join(
        [str(project), str(project / ".venv" / "Scripts"), str(tmp_path / "installed")]))
    assert gitutil._git_program(windows=True) == expected


def test_project_above_the_home_folder_keeps_the_users_tools(tmp_path, monkeypatch):
    home = tmp_path / "me"
    expected = _git_in(home / "scoop" / "shims")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("PATH", str(home / "scoop" / "shims"))
    assert gitutil._git_program(windows=True) == expected


def test_similar_folder_name_stays(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    expected = _git_in(tmp_path / "project-tools")
    monkeypatch.chdir(project)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "project-tools"))
    assert gitutil._git_program(windows=True) == expected


def test_quoted_entry(tmp_path, monkeypatch):
    expected = _git_in(tmp_path / "installed")
    monkeypatch.setenv("PATH", f'"{tmp_path / "installed"}"')
    assert gitutil._git_program(windows=True) == expected


def test_no_git_on_path_names_nothing_that_exists(tmp_path, monkeypatch):
    project = tmp_path / "project"
    _git_in(project)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", str(project))
    program = gitutil._git_program(windows=True)
    assert os.path.isabs(program) and not os.path.exists(program)


def test_working_directory_that_is_gone(tmp_path, monkeypatch):
    expected = _git_in(tmp_path / "installed")
    monkeypatch.setattr(gitutil.os, "getcwd", lambda: (_ for _ in ()).throw(OSError()))
    monkeypatch.setenv("PATH", str(tmp_path / "installed"))
    assert gitutil._git_program(windows=True) == expected


@windows_only
def test_git_exe_in_the_project_does_not_start(tmp_path, env):
    marker = tmp_path / "started"
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    write_cli(repo, "git", f"open({str(marker)!r}, 'a').write('x')\n")

    r = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)], input=json.dumps(ups_payload(repo)),
        capture_output=True, text=True, env=env, cwd=repo, timeout=120)

    assert r.returncode == 0, r.stderr
    assert not marker.exists()
