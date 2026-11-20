"""The hooks run no git in a repository other than the session's own whose config
names commands for git to run. The session's repository, its subfolders and its
linked worktrees are not affected, and neither are other repositories without
such settings."""
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import time
import zlib

import pytest

import conftest
import diffstate
import gitutil
import reporesolve

HOOKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
GIT_VERSION = tuple(int(x) for x in re.findall(
    r"\d+", subprocess.run(["git", "--version"], capture_output=True, text=True).stdout)[:2])
config_hooks = pytest.mark.skipif(GIT_VERSION < (2, 54), reason="git without hooks in the config")


@pytest.fixture(autouse=True)
def clean_env(tmp_path, monkeypatch):
    """No settings but the test's own, for git here and in the hooks."""
    for k in list(os.environ):
        if k.startswith(("GIT_", "CLAUDE_", "SECURITY_")):
            monkeypatch.delenv(k)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for who in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{who}_NAME", "t")
        monkeypatch.setenv(f"GIT_{who}_EMAIL", "t@example.com")
    monkeypatch.setattr(gitutil, "_other_repos", {})
    monkeypatch.setattr(gitutil, "_bare_folders", {})
    return home


@pytest.fixture
def marker(tmp_path):
    return tmp_path / "ran"


@pytest.fixture
def project(tmp_path, monkeypatch):
    p = new_repo(tmp_path / "proj")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(p))
    return p


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def new_repo(path, attributes=None):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    (path / "lib.py").write_text("print('one')\n")
    if attributes:
        (path / ".gitattributes").write_text(attributes)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", f"init {path.name}")
    return path


def edit(path):
    (path / "lib.py").write_text("print('two')\n")
    index = path / ".git" / "index"
    if index.exists():
        old = os.stat(index).st_mtime - 3600
        os.utime(index, (old, old))


def note(marker):
    return f"echo x >> '{marker.as_posix()}'"


def add_config(path, text):
    with open(path / ".git" / "config", "ab") as f:
        f.write(text if isinstance(text, bytes) else text.encode())


def nested(path, marker, kind):
    new_repo(path, "* filter=probe\n" if kind in ("clean", "process") else None)
    if kind == "clean":
        git(path, "config", "filter.probe.clean", f"{note(marker)}; cat")
    elif kind == "process":
        git(path, "config", "filter.probe.process", note(marker))
    elif kind == "download":
        blob = git(path, "rev-parse", "HEAD:lib.py")
        obj = path / ".git" / "objects" / blob[:2] / blob[2:]
        os.chmod(obj, 0o600)
        obj.unlink()
        git(path, "config", "core.repositoryformatversion", "1")
        git(path, "config", "extensions.partialClone", "origin")
        git(path, "config", "remote.origin.url", path.as_posix())
        git(path, "config", "remote.origin.promisor", "true")
        git(path, "config", "remote.origin.uploadpack", f"{note(marker)}; :")
    elif kind == "hook":
        git(path, "config", "hook.probe.event", "post-index-change")
        git(path, "config", "hook.probe.command", note(marker))
    edit(path)
    marker.unlink(missing_ok=True)
    return path


def prompt_hook(cwd, tmp_path):
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "security_reminder_hook.py")], cwd=cwd,
        env={**os.environ, "SECURITY_WARNINGS_STATE_DIR": str(tmp_path / "state")},
        input=json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "s",
                          "cwd": str(cwd), "prompt": "x"}),
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    files = list((tmp_path / "state").glob("security_warnings_state_*.json"))
    return (json.loads(files[0].read_text()) if files else {}).get("baseline_sha")


KINDS = ["clean", "process", pytest.param("hook", marks=config_hooks)]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("project_is_repo", [True, False])
def test_prompt_in_another_repo(tmp_path, monkeypatch, marker, kind, project_is_repo):
    project = tmp_path / "work"
    project.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    if project_is_repo:
        new_repo(project)
    other = nested(project / "vendor" / "lib", marker, kind)
    sha = prompt_hook(other, tmp_path)
    assert not marker.exists()
    # The turn's baseline is the session repository's, when there is one.
    assert sha == (git(project, "rev-parse", "HEAD") if project_is_repo else None)


@pytest.mark.parametrize("kind", KINDS)
def test_every_way_into_another_repo(project, marker, kind):
    other = str(nested(project / "lib", marker, kind))
    sha = git(other, "rev-parse", "HEAD")
    assert gitutil._git_toplevel(other) is None
    assert gitutil._git_toplevel_and_head(other) == (None, None)
    assert gitutil._git_dir(other) is None
    assert diffstate.capture_git_baseline(other) is None
    assert diffstate._list_untracked(other) == {}
    assert diffstate.compute_v2_review_set(other, None, None)[0] == []
    assert reporesolve.repos_from_paths([os.path.join(other, "lib.py")]) == []
    assert reporesolve.repo_containing_commit(sha, [str(project)]) is None
    assert not marker.exists()
    assert gitutil.repos_left_alone() == 1
    # ... and the session's own repository is reviewed all the same.
    assert os.path.samefile(gitutil._git_toplevel(str(project)), project)
    assert diffstate.capture_git_baseline(str(project))


@pytest.mark.parametrize("section, attribute", [
    (b'[filter "it\'s!"]', b"it's!"), (b'[filter ""]', b""), (b'[filter "a=b"]', b"a=b"),
    (b'[filter "\xff"]', b"\xff"), ('[filter "ünï"]'.encode(), "ünï".encode()),
    (b'[FILTER "p"]', b"p"),
])
def test_any_driver_name(project, marker, section, attribute, monkeypatch):
    other = new_repo(project / "lib")
    (other / ".gitattributes").write_bytes(b"* filter=" + attribute + b"\n")
    add_config(other, section + f'\n\tclean = "{note(marker)}; cat"\n'.encode())
    edit(other)
    for locale in ("C", "C.UTF-8"):
        monkeypatch.setenv("LC_ALL", locale)
        monkeypatch.setattr(gitutil, "_other_repos", {})
        assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


@pytest.mark.parametrize("how", ["include", "includeIf-gitdir", "includeIf-branch", "home", "worktree"])
def test_settings_in_another_file(project, marker, how, clean_env):
    other = new_repo(project / "lib", "* filter=probe\n")
    driver = f'[filter "probe"]\n\tclean = "{note(marker)}; cat"\n'
    extra = other / ".git" / "extra"
    if how == "worktree":
        git(other, "config", "core.repositoryformatversion", "1")
        git(other, "config", "extensions.worktreeConfig", "true")
        extra = other / ".git" / "config.worktree"
    elif how == "home":
        extra = clean_env / "extra"
        add_config(other, "[include]\n\tpath = ~/extra\n")
    else:
        branch = git(other, "symbolic-ref", "--short", "HEAD")
        section = {"include": "include", "includeIf-gitdir": 'includeIf "gitdir:lib/"',
                   "includeIf-branch": f'includeIf "onbranch:{branch}"'}[how]
        add_config(other, f"[{section}]\n\tpath = extra\n")
    extra.write_text(driver)
    edit(other)
    marker.unlink(missing_ok=True)
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_a_driver_the_user_set_up_is_kept(project, marker, clean_env):
    (clean_env / ".gitconfig").write_text(f'[filter "probe"]\n\tclean = "{note(marker)}; cat"\n')
    other = new_repo(project / "lib", "* filter=probe\n")
    edit(other)
    marker.unlink(missing_ok=True)
    assert diffstate.capture_git_baseline(str(other))
    assert marker.exists()


@pytest.mark.parametrize("settings, kept", [
    ('[filter "lfs"]\n\tclean = git-lfs clean -- %f\n\tsmudge = git-lfs smudge -- %f\n'
     "\tprocess = git-lfs filter-process\n\trequired = true\n", True),
    ('[filter "lfs"]\n\tclean = "git-lfs clean -- %f; true"\n', False),
    ('[filter "lfs"]\n\tclean = "git-lfs clean -- %f\\n true"\n', False),
    ('[filter "lfs"]\n\tclean = git-lfs clean %f\n\tsmudge = git-lfs smudge --skip %f\n', True),
    ('[filter "lfs"]\n\tsmudge =\n\tprocess =\n\trequired = false\n', True),
    ('[filter "x"]\n\tsmudge = true\n', True),
    ('[filter "x"]\n\tclean = true\n[filter "x"]\n\tclean =\n', False),
    ('[lfs "extension.x"]\n\tclean = true\n', False),
    ('[lfs "extension.x.clean=true "]\n\ty = z\n', False),
    ('[foo]\n\tbar = "x\\nlfs.extension.evil.clean=true"\n', False),
    ('[alias]\n\tx = "!a\\nb"\n', True),
    ('[remote "o"]\n\tpromisor = true\n\turl = https://example.com/x.git\n\tfetch = +a:b\n', True),
    ('[remote "o"]\n\tpromisor = true\n\turl = git@example.com:x/y.git\n', True),
    ('[remote "o"]\n\tpartialclonefilter = blob:none\n\turl = https://e.com/x\n\tuploadpack = u\n', False),
    ('[extensions]\n\tpartialClone = ../src\n', False),
    ('[extensions]\n\tpartialClone = o\n[remote "o"]\n\turl = https://e.com/x\n', True),
    ('[extensions]\n\tpartialClone = o\n[remote "p"]\n\turl = https://e.com/x\n', False),
    ('[remote "../src"]\n\tpromisor = true\n', False),
    ('[remote "--upload-pack=x;"]\n\tpromisor = true\n\turl = https://e.com/x\n', False),
    ('[extensions]\n\tpartialClone = --upload-pack=x\n[remote "--upload-pack=x"]\n\turl = https://e.com/x\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = work:o/r.git\n[user]\n\tname = x\n', True),
    ('[remote "o"]\n\tpromisor = true\n\turl = org-1@ssh.dev:o/r\n[credential "https://e.com"]\n'
     "\tuseHttpPath = true\n[branch \"main\"]\n\tremote = o\n", True),
    ('[remote "o"]\n\tpromisor = true\n\turl = https://e.com\n[credential "https://e.com"]\n\thelper = x\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = https://e.com\n[url "ext::x"]\n\tinsteadOf = https://e.com\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = C:/x\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = ext://run\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = file:///x\n', False),
    ('[core]\n\tvirtualFilesystem = true\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = https://e.com/x\n[http]\n\tcookieFile = x\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = https://e.com/x\n[fetch]\n\tbundleURI = x\n', False),
    # what `scalar clone`, a sparse index, git-lfs and Android's repo tool write
    ('[remote "o"]\n\tpromisor = true\n\turl = https://e.com/x\n\tprojectname = p\n[am]\n\tkeepCR = true\n'
     "[commitGraph]\n\tchangedPaths = true\n[index]\n\tsparse = true\n[lfs]\n\trepositoryformatversion = 0\n"
     "[alias]\n\tst = status\n[merge]\n\tstat = false\n", True),
    ('[core]\n\tuseGvfsHelper = true\n', False),
    ('[http]\n\tcookieFile = x\n[fetch]\n\tbundleURI = x\n', True),
    ('[lfs "EXTENSION.x"]\n\tclean = true\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = ext::sh -c x\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = none::x\n[alias]\n\tremote-none = !x\n', False),
    ('[remote "o"]\n\tpromisor = true\n\turl = ../x\n', False),
    ('[remote "o"]\n\turl = ../x\n\tuploadpack = u\n[core]\n\tsshCommand = ssh -i k\n', True),
    ('[core]\n\tautocrlf = input\n[filter "x"]\n\trequired = false\n[user]\n\tname = x\n', True),
])
def test_which_settings_count(project, settings, kept):
    other = new_repo(project / "lib")
    add_config(other, settings)
    assert (gitutil._git_toplevel(str(other)) is not None) is kept


@pytest.mark.parametrize("settings, bits", [
    ("", 0),
    ('[filter "lfs"]\n\tclean = git-lfs clean -- %f\n\tprocess = git-lfs filter-process\n', 0),
    ('[core]\n\tsshCommand = ssh -i k\n\thooksPath = .husky\n[remote "o"]\n\turl = git@example.com:x\n', 0),
    ('[extensions]\n\tpartialClone = o\n[remote "o"]\n\tpromisor = true\n\turl = https://example.com/x\n', 0),
    ('[filter "nbstripout"]\n\tclean = nbstripout\n\tsmudge = cat\n', 1),
    ('[filter "git-crypt-team"]\n\tclean = git-crypt clean\n\trequired = true\n', 2),
    ('[filter "annex"]\n\tprocess = git-annex filter-process\n', 4),
    ('[filter "lfs"]\n\tclean = mine\n', 8),
    ('[lfs "extension.x"]\n\tclean = mine\n', 8),
    ('[filter "jupytext"]\n\tclean = a\n[filter "nbstripout"]\n\tclean = b\n', 17),
    ('[hook "x"]\n\tcommand = a\n\tevent = post-index-change\n', 32),
    ('[core]\n\tvirtualFilesystem = a\n', 64),
    ('[remote "o"]\n\tpromisor = true\n\turl = https://example.com/x\n\tuploadpack = u\n', 128),
])
def test_commands_in_the_session_repo_are_counted(project, settings, bits):
    add_config(project, settings)
    assert gitutil.session_repo_commands() == bits
    assert gitutil._git_toplevel(str(project))  # and nothing else changes


def test_only_the_session_repo_is_counted(project, tmp_path, marker, monkeypatch):
    nested(project / "lib", marker, "clean")
    assert gitutil.session_repo_commands() == 0
    (project / "sub").mkdir()
    git(project, "config", "filter.x.clean", note(marker))
    marker.unlink(missing_ok=True)
    for start in (project, project / "sub"):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(start))
        assert gitutil.session_repo_commands() == 16
    assert not marker.exists()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert gitutil.session_repo_commands() == 0
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    assert gitutil.session_repo_commands() == 0


def test_the_count_is_on_the_stop_row(session, marker, hook_env, stub_api):
    project, _, _ = session
    git(project, "config", "filter.x.clean", "cat")
    env = {**hook_env, "CLAUDE_PROJECT_DIR": str(project)}
    for payload, sent in ((conftest.stop_payload(project), 16),
                          ({**conftest.stop_payload(project), "hook_event_name": "SubagentStop"}, None)):
        conftest.run_hook(conftest.ups_payload(project), env)
        (project / "lib.py").write_text(conftest.VULN_PY)
        m = conftest.metrics_of(conftest.run_hook(payload, env)[1])
        assert m.get("mode") == sent, m


def test_settings_of_the_session_repo_that_cannot_be_read(project):
    add_config(project, "[broken\n")
    assert gitutil.session_repo_commands() == 256


def test_partial_clone_with_a_command_to_download_by(project, marker):
    other = nested(project / "lib", marker, "download")
    assert gitutil._git_toplevel(str(other)) is None
    assert not marker.exists()


def test_looking_for_a_commit_downloads_nothing(project, marker):
    other = nested(project / "lib", marker, "download")
    git(other, "config", "remote.origin.url", "none::x")
    git(other, "config", "alias.remote-none", f"!{note(marker)}; :")
    reporesolve.repo_containing_commit("0" * 39 + "1", [str(project)])
    assert not marker.exists()


@pytest.mark.parametrize("where", ["top", "subfolder", "stray-git", "worktree", "from-worktree"])
def test_session_repo_keeps_its_config(tmp_path, monkeypatch, marker, where):
    project = nested(tmp_path / "proj", marker, "clean")
    cwd = home = project
    if where in ("subfolder", "stray-git"):
        cwd = project / "sub"
        cwd.mkdir()
        if where == "stray-git":
            (cwd / ".git").mkdir()
    elif where.endswith("worktree"):
        wt = tmp_path / "wt"
        git(project, "worktree", "add", "-q", str(wt))
        (wt / "lib.py").write_text("print('three')\n")
        cwd, home = (wt, project) if where == "worktree" else (project, wt)
        marker.unlink(missing_ok=True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(home))
    assert prompt_hook(cwd, tmp_path)
    assert marker.exists()


@pytest.mark.skipif(os.name == "nt", reason="folder names Windows does not allow")
@pytest.mark.parametrize("name", [b"g ", b" g", b"\xff", b"a\rb"])
def test_git_file_is_read_as_git_reads_it(project, marker, name):
    other = project / "lib"
    other.mkdir()
    r = subprocess.run([b"git", b"init", b"-q", b"--separate-git-dir", name, b"."],
                       cwd=other, capture_output=True)
    if r.returncode != 0:
        pytest.skip("a name this file system does not allow")
    (other / ".gitattributes").write_text("* filter=probe\n")
    (other / "lib.py").write_text("print('one')\n")
    git(other, "add", "-A")
    git(other, "commit", "-q", "-m", "init")
    git(other, "config", "filter.probe.clean", f"{note(marker)}; cat")
    (other / ".git").write_bytes(b"gitdir: " + name + b"\n")
    for lookalike in {name.strip(), name.decode("utf-8", "replace").encode(),
                      name.replace(b"\r", b"\n")} - {name}:
        os.symlink(os.fsencode(project / ".git"), os.path.join(os.fsencode(other), lookalike))
    (other / "lib.py").write_text("print('two')\n")
    marker.unlink(missing_ok=True)
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_folder_that_borrows_the_session_repo_is_not_its_worktree(project, marker):
    git(project, "config", "core.repositoryformatversion", "1")
    git(project, "config", "extensions.worktreeConfig", "true")
    fake = project / "vendor" / "lib"
    own = fake / "store"
    own.mkdir(parents=True)
    (own / "HEAD").write_text(git(project, "rev-parse", "HEAD") + "\n")
    (own / "commondir").write_text((project / ".git").as_posix() + "\n")
    (own / "gitdir").write_text((fake / ".git").as_posix() + "\n")
    (own / "config.worktree").write_text(f'[filter "probe"]\n\tclean = "{note(marker)}; cat"\n')
    (fake / ".git").write_text(f"gitdir: {own.as_posix()}\n")
    (fake / ".gitattributes").write_text("* filter=probe\n")
    (fake / "lib.py").write_text("print('one')\n")
    git(fake, "reset", "-q")
    (fake / "lib.py").write_text("print('two')\n")
    marker.unlink(missing_ok=True)
    assert diffstate.capture_git_baseline(str(fake)) is None
    assert not marker.exists()


def test_settings_that_cannot_be_read_leave_out_only_that_repo(project, monkeypatch):
    other = new_repo(project / "lib")
    looks = []

    def fail(path):
        looks.append(path)
        raise subprocess.TimeoutExpired("git", 5)
    monkeypatch.setattr(gitutil, "_own_settings", fail)
    assert gitutil._git_toplevel(str(other)) is None
    assert diffstate.capture_git_baseline(str(other)) is None
    assert gitutil._git_toplevel(str(project)) is not None
    assert len(looks) == gitutil.repos_left_alone() == 1


def test_settings_are_looked_at_again_after_a_while(project, marker, monkeypatch):
    other = new_repo(project / "lib", "* filter=probe\n")
    assert diffstate.capture_git_baseline(str(other))
    git(other, "config", "filter.probe.clean", f"{note(marker)}; cat")
    edit(other)
    marker.unlink(missing_ok=True)
    monkeypatch.setattr(gitutil, "_OTHER_REPO_FINE_S", -1)
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_one_look_per_repository(project, monkeypatch):
    other = new_repo(project / "lib")
    paths = []
    for i in range(5):
        (other / f"d{i}").mkdir()
        paths.append(str(other / f"d{i}" / "x.py"))
    looks = []
    real = gitutil._own_settings
    monkeypatch.setattr(gitutil, "_own_settings", lambda p: looks.append(p) or real(p))
    assert len(reporesolve.repos_from_paths(paths)) == 1
    assert len(looks) == 1


def test_without_a_project_folder_nothing_changes(tmp_path, marker):
    other = nested(tmp_path / "lib", marker, "clean")
    assert prompt_hook(other, tmp_path)
    assert marker.exists()


def test_work_tree_of_another_repo(project, marker):
    outer = nested(project / "vendor", marker, "clean")
    inner = new_repo(outer / "a")
    git(inner, "config", "core.worktree", "../..")
    assert gitutil._git_toplevel(str(inner)) is None
    assert diffstate.capture_git_baseline(str(inner)) is None
    assert diffstate.compute_v2_review_set(str(inner), None, None)[0] == []
    assert not marker.exists()


def test_checked_out_submodule_is_kept(project, tmp_path):
    lib = new_repo(tmp_path / "upstream")
    git(project, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(lib), "sub")
    assert os.path.samefile(gitutil._git_toplevel(str(project / "sub")), project / "sub")


def test_relative_git_dir_names_no_one_repository(project, marker, monkeypatch):
    other = nested(project / "lib", marker, "clean")
    monkeypatch.setenv("GIT_DIR", ".git")
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_git_config_variable_does_not_hide_the_settings(project, marker, monkeypatch, clean_env):
    other = nested(project / "lib", marker, "clean")
    (clean_env / "other").write_text("[user]\n\tname = x\n")
    monkeypatch.setenv("GIT_CONFIG", str(clean_env / "other"))
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_showing_a_commit_verifies_no_signature(project, marker):
    tree = git(project, "rev-parse", "HEAD^{tree}")
    body = (f"tree {tree}\nauthor t <t@example.com> 1 +0000\ncommitter t <t@example.com> 1 +0000\n"
            "gpgsig -----BEGIN PGP SIGNATURE-----\n \n x\n -----END PGP SIGNATURE-----\n\nm\n")
    sha = subprocess.run(["git", "hash-object", "-t", "commit", "-w", "--stdin"], cwd=project,
                         input=body.encode(), capture_output=True, check=True).stdout.decode().strip()
    tool = project / "tool.sh"
    tool.write_text(f"#!/bin/sh\n{note(marker)}\n")
    tool.chmod(0o755)
    git(project, "config", "gpg.program", tool.as_posix())
    git(project, "config", "format.pretty", "%G? %H")
    r = subprocess.run([*gitutil.GIT_CMD, "show", "-p", sha, "--"], cwd=project, capture_output=True)
    assert r.returncode == 0 and sha.encode() in r.stdout
    assert not marker.exists()


def test_project_folder_that_is_gone(project, monkeypatch, tmp_path):
    plain = new_repo(tmp_path / "plain")
    filtered = nested(tmp_path / "filtered", tmp_path / "ran", "clean")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project / "gone"))
    assert gitutil._git_toplevel(str(plain)) is not None
    assert gitutil._git_toplevel(str(filtered)) is None


def test_worktree_settings_without_their_file(project):
    other = new_repo(project / "lib")
    git(other, "config", "core.repositoryformatversion", "1")
    git(other, "config", "extensions.worktreeConfig", "true")
    assert gitutil._git_toplevel(str(other)) is not None


@pytest.mark.parametrize("how", ["GIT_DIR", "GIT_CEILING_DIRECTORIES"])
def test_a_look_from_a_subfolder_counts_for_the_repository(project, marker, monkeypatch, how):
    other = nested(project / "lib", marker, "clean")
    (other / "sub").mkdir()
    monkeypatch.setenv(how, ".git" if how == "GIT_DIR" else str(other))
    assert diffstate.capture_git_baseline(str(other / "sub")) is None
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_long_value_is_read_quickly(project):
    started = time.monotonic()
    gitutil._names_commands([(b"x.y", b"\n" * 300_000)])
    assert time.monotonic() - started < 2


def test_session_started_in_a_bare_repo_that_holds_its_worktrees(tmp_path, monkeypatch, marker):
    src = new_repo(tmp_path / "src")
    hub = tmp_path / "hub.git"
    git(tmp_path, "clone", "-q", "--bare", str(src), str(hub))
    git(hub, "worktree", "add", "-q", "-b", "side", str(hub / "side"))
    git(hub, "config", "filter.probe.clean", f"{note(marker)}; cat")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(hub))
    for k, v in gitutil.git_config_env(gitutil.SAFE_GIT_CONFIG).items():
        monkeypatch.setenv(k, v)
    assert gitutil._git_toplevel(str(hub / "side")) is not None


@pytest.fixture
def session(project, marker, hook_env, tmp_path):
    """A session in `project`, with an earlier turn's hint at a third
    repository, and a left-out repository `lib` in the project folder."""
    other = nested(project / "lib", marker, "clean")
    third = new_repo(tmp_path / "third")
    hook_env["CLAUDE_PROJECT_DIR"] = str(project)
    conftest.run_hook(conftest.edit_payload(tmp_path, third / "a.py"), hook_env)
    conftest.run_hook(conftest.ups_payload(tmp_path), hook_env)
    (third / "a.py").write_text("x = 1\n")
    conftest.run_hook(conftest.stop_payload(tmp_path), hook_env)
    return project, other, third


def test_turn_in_a_left_out_repo_keeps_the_session_repos_review(session, marker, hook_env, stub_api):
    project, other, _ = session
    stub_api.bodies.clear()
    conftest.run_hook(conftest.ups_payload(other), hook_env)
    (project / "lib.py").write_text(conftest.VULN_PY)  # as a Bash command would
    m = conftest.metrics_of(conftest.run_hook(conftest.stop_payload(other), hook_env)[1])
    assert m.get("skip_reason") is None and m["files_reviewed"] == 1, m
    assert m["repos_left_alone"] == 1
    assert any("subprocess.call" in b for b in stub_api.bodies)
    assert not marker.exists()


@pytest.mark.parametrize("command, output", [
    ("git commit -q -m x", ""), ("git commit -m x", "[main 1234567] x\n 1 file changed\n"),
    ("git push -u origin main", "To x\n * [new branch]      main -> main\n"),
    ("git push", "Everything up-to-date\n"),
])
def test_commit_or_push_in_a_left_out_repo_is_not_another_ones(
        session, marker, hook_env, stub_api, command, output):
    _, other, third = session
    before = len(stub_api.calls)
    m = conftest.metrics_of(conftest.run_hook(conftest.bash_payload(other, command, output), hook_env)[1])
    assert m["skip_reason"] in (21, 26), m
    assert "repo_resolution" not in m or m["repo_resolution"] == reporesolve.RES_NONE
    assert len(stub_api.calls) == before
    assert not marker.exists()


NEW_BRANCH = "To x\n * [new branch]      main -> main\n"


@pytest.mark.parametrize("where", ["session", "beside"])
@pytest.mark.parametrize("command, output", [
    ("git -C {} push", NEW_BRANCH), ("cd {} && git push", "Everything up-to-date\n"),
    ("git -C {} commit -q -m x", ""), ("cd {} && git commit -q -m x", ""),
    ("cd {} && git commit -m x", "[main 1234567] x\n 1 file changed\n"),
    ("cd {} && git commit -q -m x && git push", NEW_BRANCH),
])
def test_command_that_names_a_left_out_repo_is_not_another_ones(
        session, tmp_path, marker, hook_env, stub_api, where, command, output):
    """Neither the session's repository nor the one an earlier turn worked in,
    which both have a commit that was not pushed."""
    project, other, third = session
    conftest.commit_file(project, "b.py", conftest.VULN_PY)
    conftest.commit_file(third, "b.py", conftest.VULN_PY)
    cwd = project
    if where == "beside":
        cwd = tmp_path / "beside"
        cwd.mkdir()
    before = len(stub_api.calls)
    for start in range(2):  # one for each entry in hooks.json
        m = conftest.metrics_of(conftest.run_hook(conftest.bash_payload(
            cwd, command.format(other.as_posix()), output, tool_use_id="toolu_1"), hook_env)[1])
        if where == "beside" or not start or "commit" in command and "push" in command:
            assert m["skip_reason"] in (21, 26) and m["repo_resolution"] == reporesolve.RES_NONE, m
        else:
            assert "skip_reason" not in m and "files_reviewed" not in m, m
    assert len(stub_api.calls) == before
    assert not (project / ".git" / "sg-reviewed-shas").exists()
    assert not marker.exists()


@pytest.mark.parametrize("below", [False, True])
def test_commit_the_output_names_after_a_look_into_a_left_out_repo(
        session, marker, hook_env, stub_api, below):
    """The session's own, though the command reads as one in the other."""
    project, other, _ = session
    _, out = conftest.commit_file(project, "src/b.py", conftest.VULN_PY)
    cwd = project / "src" if below else project
    m = conftest.metrics_of(conftest.run_hook(conftest.bash_payload(
        cwd, f"(cd {other.as_posix()} && make); git commit -m x", out), hook_env)[1])
    assert m.get("skip_reason") is None and m["files_reviewed"] == 1, m
    assert m["repo_resolution"] == reporesolve.RES_SHA_SCAN
    assert not marker.exists()


def test_command_in_a_left_out_repo_and_another(session, tmp_path, marker, hook_env, stub_api):
    project, other, _ = session
    _, out = conftest.commit_file(project, "b.py", conftest.VULN_PY)
    m = conftest.metrics_of(conftest.run_hook(conftest.bash_payload(
        tmp_path, f"git -C {other.as_posix()} commit -q -m x; git -C {project.as_posix()} commit -m x", out),
        hook_env)[1])
    assert m.get("skip_reason") is None and m["files_reviewed"] == 1, m
    assert m["repo_resolution"] == reporesolve.RES_COMMAND
    assert not marker.exists()


def test_commit_made_elsewhere_from_a_left_out_repo_is_found(session, marker, hook_env, stub_api):
    project, other, _ = session
    _, out = conftest.commit_file(project, "b.py", conftest.VULN_PY)
    m = conftest.metrics_of(conftest.run_hook(
        conftest.bash_payload(other, 'cd "$REPO" && git commit -m change', out),
        {**hook_env, "CLAUDE_PROJECT_DIR": str(project)})[1])
    assert m.get("skip_reason") is None and m["files_reviewed"] == 1, m
    assert m["repo_resolution"] == reporesolve.RES_SHA_SCAN
    assert not marker.exists()


def test_turn_in_an_embedded_repository_keeps_the_session_repos_review(
        project, marker, hook_env, stub_api):
    inside = embedded(project / "pkg" / "x", marker)
    (inside / "lib.py").write_text("print('two')\n")
    marker.unlink(missing_ok=True)
    hook_env["CLAUDE_PROJECT_DIR"] = str(project)
    conftest.run_hook(conftest.ups_payload(inside), hook_env)
    (project / "lib.py").write_text(conftest.VULN_PY)
    conftest.run_hook(conftest.stop_payload(inside), hook_env)
    assert any("subprocess.call" in b for b in stub_api.bodies)
    assert not marker.exists()


def test_alias_in_a_partial_clone(project):
    repo = new_repo(project / "lib")
    for k, v in (("core.repositoryformatversion", "1"), ("extensions.partialClone", "origin"),
                 ("remote.origin.url", "https://example.com/x.git"), ("remote.origin.promisor", "true")):
        git(repo, "config", k, v)
    assert gitutil._git_toplevel(str(repo))
    git(repo, "config", "alias.credential-some-helper", "!echo")
    gitutil._other_repos.clear()
    assert gitutil._git_toplevel(str(repo)) is None


def embedded(inside, marker):
    """A bare repository laid out in a work tree's own folder, whose filter git
    before 2.38 would start from there."""
    inside.mkdir(parents=True)
    git(inside, "init", "-q", "--bare", ".")
    git(inside, "config", "core.bare", "false")
    git(inside, "config", "core.worktree", ".")
    (inside / ".gitattributes").write_text("* filter=probe\n")
    (inside / "lib.py").write_text("print('one')\n")
    git(inside, "add", ".gitattributes", "lib.py")
    git(inside, "commit", "-q", "-m", "x")
    git(inside, "config", "filter.probe.clean", f"{note(marker)}; cat")
    return inside


HEAD_LAYOUTS = ["padded-head", "tab-head", pytest.param("newline", marks=pytest.mark.skipif(
    os.name == "nt", reason="a folder name Windows does not allow")), pytest.param("head-link", marks=pytest.mark.skipif(
    os.name == "nt", reason="symbolic links"))]


@pytest.mark.parametrize("layout", ["plain", "commondir", "empty-git", "bogus-commondir", "bogus-gitdir"]
                         + HEAD_LAYOUTS)
@pytest.mark.parametrize("project_dir", [True, False])
def test_embedded_repository_git_before_2_38_would_take(project, marker, layout, project_dir, monkeypatch):
    if not project_dir:
        monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    inside = embedded(project / "pkg" / ("x\ny" if layout == "newline" else "x"), marker)
    sha, branch = git(inside, "rev-parse", "HEAD"), git(inside, "symbolic-ref", "HEAD")
    if layout == "head-link":
        git(inside, "pack-refs", "--all")
        (inside / "HEAD").unlink()
        os.symlink(branch, inside / "HEAD")
    elif layout == "padded-head":
        (inside / "HEAD").write_text("ref:" + " " * 120 + branch + "\n")
    elif layout == "tab-head":
        (inside / "HEAD").write_text("ref:\t" + branch + "\n")
    elif layout == "commondir":
        store = project / "store"
        store.mkdir()
        for name in ("objects", "refs", "config"):
            os.rename(inside / name, store / name)
        (inside / "commondir").write_text("../../store\n")
    elif layout not in ("plain", "newline"):
        dot = inside / ".git"
        dot.mkdir()
        if layout == "bogus-commondir":
            (dot / "HEAD").write_text("ref: refs/heads/main\n")
            (dot / "commondir").write_text("nowhere\n")
        elif layout == "bogus-gitdir":
            (dot / "HEAD").write_text("ref: refs/heads/main\n")
            (dot / "refs").mkdir()
    (inside / "lib.py").write_text("print('two')\n")
    marker.unlink(missing_ok=True)
    (inside / "sub").mkdir()
    for d in (inside, inside / "sub"):
        assert diffstate.capture_git_baseline(str(d)) is None
        assert diffstate.compute_v2_review_set(str(d), None, None)[0] == []
        assert gitutil._git_toplevel(str(d)) is None
    assert reporesolve.repo_containing_commit(sha, [str(project)]) is None
    assert not marker.exists()


def test_ordinary_checkouts_beside_a_head_file(project, tmp_path):
    (project / "HEAD").write_text("ref: refs/heads/main\n")
    (project / "sub").mkdir()
    assert gitutil._git_toplevel(str(project / "sub"))
    git(project, "worktree", "add", "-q", str(tmp_path / "wt"))
    (tmp_path / "wt" / "HEAD").write_text("x")
    assert gitutil._git_toplevel(str(tmp_path / "wt"))
    hub = tmp_path / "hub.git"
    git(tmp_path, "clone", "-q", "--bare", str(project), str(hub))
    git(hub, "worktree", "add", "-q", "-b", "side", str(hub / "side"))
    assert gitutil._git_toplevel(str(hub / "side"))
    outer = new_repo(tmp_path / "outer")
    git(outer, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(project), "sub")
    (outer / "sub" / "HEAD").write_text("x")
    assert gitutil._git_toplevel(str(outer / "sub"))


def test_git_is_asked_once_about_a_folder_below_a_head_file(project, monkeypatch):
    (project / "HEAD").write_text("x")
    asked = []
    real = gitutil._git_paths
    monkeypatch.setattr(gitutil, "_git_paths", lambda *a: asked.append(a) or real(*a))
    for _ in range(3):
        assert not gitutil._found_through_bare_folder(str(project))
    assert len(asked) == 1


@pytest.mark.skipif(os.name == "nt", reason="a folder name cannot end in a space")
def test_folder_without_a_repository_of_its_own_below_another(project, marker):
    nested(project / "b", marker, "clean")
    spaced = new_repo(project / "b ")
    (spaced / "sub" / ".git").mkdir(parents=True)
    assert gitutil._git_toplevel(str(spaced / "sub")) is None
    assert diffstate.compute_v2_review_set(str(spaced / "sub"), None, None)[0] == []
    assert not marker.exists()


def test_folder_that_points_at_the_session_repo_is_not_its_work_tree(project, marker):
    (project / "tools").mkdir()
    git(project, "config", "filter.tidy.clean", "sh tools/c.sh")
    fake = project / "vendor" / "lib"
    (fake / "tools").mkdir(parents=True)
    (fake / "tools" / "c.sh").write_text(f"{note(marker)}; cat\n")
    (fake / ".git").write_text("gitdir: ../../.git\n")
    (fake / ".gitattributes").write_text("*.py filter=tidy\n")
    (fake / "lib.py").write_text("print('two')\n")
    assert diffstate.capture_git_baseline(str(fake)) is None
    git(project, "config", "--unset", "filter.tidy.clean")
    git(project, "worktree", "add", "-q", str(project / "wt"))
    git(project, "config", "filter.tidy.clean", "sh tools/c.sh")
    (fake / ".git").write_text("gitdir: ../../.git/worktrees/wt\n")
    gitutil._other_repos.clear()
    assert diffstate.capture_git_baseline(str(fake)) is None
    assert not marker.exists()
    assert gitutil._git_toplevel(str(project / "wt"))


def test_bare_layout_in_a_session_subfolder_is_not_the_session_repo(project, marker, monkeypatch):
    start = project / "pkg"
    hub = embedded(start, marker)
    git(hub, "worktree", "add", "-q", "-b", "side", str(hub / "x"))
    (hub / "x" / "lib.py").write_text("print('two')\n")
    marker.unlink(missing_ok=True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(start))
    assert diffstate.capture_git_baseline(str(hub / "x")) is None
    assert not marker.exists()


def test_baseline_content_is_not_read_in_an_embedded_repository(project, marker, monkeypatch):
    inside = embedded(project / "pkg" / "x", marker)
    sha = git(inside, "rev-parse", "HEAD")
    monkeypatch.setattr(diffstate, "load_baseline_sha", lambda session_id: sha)
    assert diffstate.get_baseline_file_content("s", str(inside / "lib.py"), str(inside)) is None
    assert diffstate.get_baseline_file_content(
        "s", str(project / "lib.py"), str(project)) is None  # not a commit there
    head = git(project, "rev-parse", "HEAD")
    monkeypatch.setattr(diffstate, "load_baseline_sha", lambda session_id: head)
    assert diffstate.get_baseline_file_content("s", str(project / "lib.py"), str(project))


@pytest.mark.skipif(os.name == "nt", reason="named pipes")
def test_named_pipe_above_a_checkout_does_not_matter(project, tmp_path):
    os.mkfifo(tmp_path / "HEAD")
    assert gitutil._git_toplevel(str(project))


def test_bare_repo_the_session_was_started_in_keeps_its_hint(tmp_path, monkeypatch):
    src = new_repo(tmp_path / "src")
    hub = tmp_path / "hub.git"
    git(tmp_path, "clone", "-q", "--bare", str(src), str(hub))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(hub))
    assert not gitutil.in_left_out_repo(str(hub))


@pytest.mark.skipif(os.name == "nt", reason="symbolic links")
@pytest.mark.parametrize("session_in", ["main", "worktree"])
def test_git_entry_linked_to_the_session_repo_is_not_its_work_tree(project, marker, monkeypatch, session_in, tmp_path):
    wt = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(wt))
    git(project, "config", "filter.tidy.clean", "sh tools/c.sh")
    fake = tmp_path / "fake"
    (fake / "tools").mkdir(parents=True)
    (fake / "tools" / "c.sh").write_text(f"{note(marker)}; cat\n")
    (fake / ".gitattributes").write_text("*.py filter=tidy\n")
    (fake / "lib.py").write_text("print('two')\n")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project if session_in == "main" else wt))
    for target in (wt / ".git", project / ".git"):
        os.symlink(target, fake / ".git")
        gitutil._other_repos.clear()
        assert diffstate.capture_git_baseline(str(fake)) is None
        (fake / ".git").unlink()
    assert not marker.exists()
    assert gitutil._git_toplevel(str(wt)) and gitutil._git_toplevel(str(project))


def test_submodule_of_the_session_repo_keeps_its_config(project, marker, tmp_path, monkeypatch):
    lib = new_repo(tmp_path / "upstream", "* filter=probe\n")
    git(project, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(lib), "sub")
    git(project, "commit", "-q", "-m", "sub")
    git(project / "sub", "config", "filter.probe.clean", f"{note(marker)}; cat")
    assert gitutil._git_toplevel(str(project / "sub"))
    wt = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(wt))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(wt))
    gitutil._other_repos.clear()
    assert gitutil._git_toplevel(str(project / "sub"))
    fake = project / "fake"
    fake.mkdir()
    (fake / "lib.py").write_text("print('two')\n")
    git(project / "sub", "worktree", "add", "-q", str(tmp_path / "subwt"))
    for target in ("sub", "sub/worktrees/subwt"):
        (fake / ".git").write_text(f"gitdir: ../.git/modules/{target}\n")
        gitutil._other_repos.clear()
        assert gitutil._git_toplevel(str(fake)) is None
    # Seen from the other checkouts of the session's repository, and from the submodule.
    git(wt, "-c", "protocol.file.allow=always", "submodule", "update", "-q", "--init")
    git(wt / "sub", "config", "filter.probe.clean", f"{note(marker)}; cat")
    git(project, "config", "filter.probe.clean", f"{note(marker)}; cat")
    for start, at in ((project, wt / "sub"), (project, tmp_path / "subwt"), (project / "sub", project)):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(start))
        gitutil._other_repos.clear()
        assert gitutil._git_toplevel(str(at)), (start, at)


def test_stray_git_folder_in_another_repo_or_worktree(project, marker, tmp_path):
    other = new_repo(project / "plain")
    wt = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(wt))
    for top in (other, wt):
        (top / "fix" / ".git").mkdir(parents=True)
        assert os.path.samefile(gitutil._git_toplevel(str(top / "fix")), top)
    filtered = nested(project / "filtered", marker, "clean")
    (filtered / "fix" / ".git").mkdir(parents=True)
    assert gitutil._git_toplevel(str(filtered / "fix")) is None
    assert diffstate.capture_git_baseline(str(filtered / "fix")) is None
    assert not marker.exists()


def test_commit_lookup_costs_one_git_start_per_repository(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(work))
    for i in range(4):
        new_repo(work / f"r{i}")
    runs = []
    real = subprocess.run
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: runs.append(a) or real(*a, **k))
    assert reporesolve.repo_containing_commit("0" * 39 + "1", [str(work)]) is None
    assert len(runs) == 4


@pytest.mark.parametrize("start", ["hub", "side"])
def test_repository_inside_a_worktree_of_a_bare_hub(tmp_path, monkeypatch, marker, start):
    src = new_repo(tmp_path / "src")
    hub = tmp_path / "hub.git"
    git(tmp_path, "clone", "-q", "--bare", str(src), str(hub))
    git(hub, "worktree", "add", "-q", "-b", "side", str(hub / "side"))
    other = nested(hub / "side" / "vendor" / "lib", marker, "clean")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(hub if start == "hub" else hub / "side"))
    assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()
    assert gitutil._git_toplevel(str(hub / "side"))


def test_bare_layout_around_the_start_folder_vouches_for_nothing(tmp_path, monkeypatch, marker):
    root = tmp_path / "unpacked"
    for name in ("refs", "objects", "app"):
        (root / name).mkdir(parents=True)
    (root / "HEAD").write_text("ref: refs/heads/main\n")
    (root / "config").write_text("[core]\n\tbare = true\n")
    other = nested(root / "vendor" / "lib", marker, "clean")
    for start in (root, root / "app"):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(start))
        gitutil._other_repos.clear()
        assert diffstate.capture_git_baseline(str(other)) is None
    assert not marker.exists()


def test_git_directory_that_is_the_session_work_tree(project, marker):
    for name in ("refs", "objects"):
        (project / name).mkdir()
    (project / "HEAD").write_text("ref: refs/heads/main\n")
    (project / "config").write_text(
        f'[core]\n\trepositoryformatversion = 0\n\tbare = false\n\tworktree = vendor/x\n'
        f'[filter "probe"]\n\tclean = "{note(marker)}; cat"\n')
    inside = project / "vendor" / "x"
    inside.mkdir(parents=True)
    (inside / ".git").write_text("gitdir: ../..\n")
    (inside / ".gitattributes").write_text("* filter=probe\n")
    (inside / "lib.py").write_text("print('two')\n")
    assert gitutil._git_toplevel(str(inside)) is None
    assert diffstate.capture_git_baseline(str(inside)) is None
    assert diffstate.compute_v2_review_set(str(inside), None, None)[0] == []
    assert not marker.exists()


def holds_a_repository(where, marker, recorded="sub", on_disk="sub", again=False):
    """A repository at `where` without settings of its own, that holds another
    one, whose config names a command, and records it under the name `recorded`.
    `again`: the repository is there already."""
    outer = where if again else new_repo(where)
    (outer / ".gitmodules").write_text(
        f'[submodule "sub"]\n\tpath = {on_disk}\n\turl = ./x\n\tignore = none\n')
    inner = nested(outer / os.path.normpath(on_disk), marker, "clean")
    git(outer, "add", ".gitmodules")
    git(outer, "commit", "-q", "-m", "modules")
    id_len = len(git(outer, "rev-parse", "HEAD"))
    git(outer, "update-index", "--add", "--cacheinfo",
        f"160000,{git(inner, 'rev-parse', 'HEAD').ljust(id_len, '1')},{recorded}")
    (outer / "lib.py").write_text("print('three')\n")
    marker.unlink(missing_ok=True)
    return outer


def rewrite_index(repo, old, new):
    """Change the index file itself: git would not write it like that."""
    index = repo / ".git" / "index"
    data = index.read_bytes()[:-20]
    assert old in data
    data = data.replace(old, new)
    index.write_bytes(data + hashlib.sha1(data).digest())
    os.utime(index, (1e9, 1e9))


@pytest.mark.parametrize("mode", [0o160000, 0o160644, 0o160755, 0o167777, 0o360000])
def test_any_mode_that_git_takes_for_a_repository(project, marker, mode):
    outer = holds_a_repository(project / "vendor", marker)
    rewrite_index(outer, b"\x00\x00\xe0\x00", struct.pack(">I", mode))
    sha = diffstate.capture_git_baseline(str(outer))
    assert sha and sha != git(outer, "rev-parse", "HEAD")
    assert not marker.exists()


@pytest.mark.parametrize("recorded,on_disk", [
    (".!sub", "./sub"), ("sub!", "sub/"), ("a!/sub", "a//sub"), ("ab/!!/sub", "ab/../sub")])
def test_a_repository_recorded_under_another_spelling(project, marker, recorded, on_disk):
    outer = holds_a_repository(project / "vendor", marker, recorded, on_disk)
    (outer / "ab").mkdir()
    rewrite_index(outer, recorded.encode(), on_disk.encode())
    sha = diffstate.capture_git_baseline(str(outer))
    assert sha and sha != git(outer, "rev-parse", "HEAD")
    assert not marker.exists()


sparse_index = pytest.mark.skipif(GIT_VERSION < (2, 35), reason="git without a sparse index")


def sparse_repo(path):
    """A repository whose index holds `out` as one entry."""
    repo = new_repo(path)
    for d in ("in", "out"):
        (repo / d).mkdir()
        (repo / d / "a.py").write_text("x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "dirs")
    git(repo, "sparse-checkout", "init", "--cone", "--sparse-index")
    git(repo, "sparse-checkout", "set", "in")
    return repo


def tree(repo, entries):
    """A tree object with the entries in the order given."""
    raw = b"".join(f"{mode} {name}".encode() + b"\0" + bytes.fromhex(sha) for mode, name, sha in entries)
    raw = b"tree %d\0" % len(raw) + raw
    sha = hashlib.sha1(raw).hexdigest()
    (repo / ".git" / "objects" / sha[:2]).mkdir(exist_ok=True)
    (repo / ".git" / "objects" / sha[:2] / sha[2:]).write_bytes(zlib.compress(raw))
    return sha


def pull_a_repository(repo, tmp_path, marker, modules=None, in_order=True):
    """What a pull brings into `out`, which stays collapsed, and then a
    repository appears there."""
    inner = nested(tmp_path / "inner", marker, "clean")
    side = tmp_path / "side"
    git(tmp_path, "clone", "-q", str(repo), str(side))
    files = [("100644", f"f{i}.py", git(side, "rev-parse", "HEAD:out/a.py")) for i in range(10)]
    link = [("160000", "sub", git(inner, "rev-parse", "HEAD"))]
    out = tree(side, files + link if in_order else link + files)
    git(side, "rm", "-q", "-r", "--cached", "out")
    if modules:
        (side / ".gitmodules").write_text(modules)
        git(side, "add", ".gitmodules")
    top = git(side, "write-tree")
    entries = [line.split() for line in git(side, "ls-tree", top).splitlines()]
    entries = [(mode.lstrip("0"), name, sha) for mode, _, sha, name in entries] + [("40000", "out", out)]
    commit = git(side, "commit-tree", tree(side, sorted(entries, key=lambda e: e[1])), "-p", "HEAD", "-m", "sub")
    git(side, "update-ref", "HEAD", commit)
    git(repo, "pull", "-q", str(side), "HEAD")
    assert "040000" in git(repo, "ls-files", "-s", "--sparse")
    (repo / "out").mkdir(exist_ok=True)
    os.rename(inner, repo / "out" / "sub")
    (repo / "lib.py").write_text("print('three')\n")
    marker.unlink(missing_ok=True)


@sparse_index
@pytest.mark.parametrize("modules", [
    None, '[submodule "sub"]\n\tpath = out/sub\n\turl = ./x\n',
    '[submodule "sub"]\n\tpath = out/sub\n\turl = ./x\n\tignore = none\n'])
def test_a_repository_inside_a_collapsed_directory(tmp_path, monkeypatch, marker, modules):
    project = sparse_repo(tmp_path / "proj")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    pull_a_repository(project, tmp_path, marker, modules)
    sha = diffstate.capture_git_baseline(str(project))
    assert sha and sha != git(project, "rev-parse", "HEAD")
    assert not marker.exists()


@sparse_index
def test_collapsed_directory_that_is_not_in_order(tmp_path, monkeypatch, marker):
    project = sparse_repo(tmp_path / "proj")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    pull_a_repository(project, tmp_path, marker, in_order=False)
    assert diffstate.capture_git_baseline(str(project))
    assert not marker.exists()


@sparse_index
def test_collapsed_directory_that_appears_later(tmp_path, monkeypatch, marker):
    project = sparse_repo(tmp_path / "proj")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    pull_a_repository(project, tmp_path, marker)
    os.rename(project / "out", tmp_path / "out")
    real = gitutil._drop_gitlinks

    def then_appears(*args):
        done = real(*args)
        os.rename(tmp_path / "out", project / "out")
        return done

    monkeypatch.setattr(gitutil, "_drop_gitlinks", then_appears)
    sha = diffstate.capture_git_baseline(str(project))
    assert sha and sha != git(project, "rev-parse", "HEAD")
    assert not marker.exists()


OTHER_INDEXES = [pytest.param("sparse", marks=sparse_index), "split",
                 pytest.param("sha256", marks=pytest.mark.skipif(
                     GIT_VERSION < (2, 42), reason="git with only one kind of object id"))]


@pytest.fixture(params=OTHER_INDEXES)
def kind_of_index(request):
    return request.param


def other_index(path, kind):
    """A repository with a changed file, and an index of that kind."""
    if kind == "sparse":
        repo = sparse_repo(path)
    else:
        path.mkdir(parents=True)
        git(path, "init", "-q", *(["--object-format=sha256"] if kind == "sha256" else []))
        repo = new_repo(path)
        if kind == "split":
            git(repo, "update-index", "--split-index")
    (repo / "lib.py").write_text("print('three')\n")
    return repo


def test_baseline_of_another_repository_with_another_kind_of_index(project, kind_of_index):
    repo = other_index(project / "vendor", kind_of_index)
    git_dir = repo / ".git"
    before, files, names = (git_dir / "index").read_bytes(), set(os.listdir(git_dir)), git(repo, "ls-files")
    sha = diffstate.capture_git_baseline(str(repo))
    (repo / "new.py").write_text("x = 1\n")
    with gitutil._temp_index(str(repo), ["new.py"]) as env:
        if kind_of_index == "sha256":
            assert git(repo, "diff", "--name-only", "HEAD", sha) == "lib.py"
            listed = subprocess.run(["git", "ls-files"], cwd=repo, env=env, check=True,
                                    capture_output=True, text=True).stdout.split("\n")
            assert listed == sorted([*names.split("\n"), "new.py"]) + [""]
        else:
            assert sha == git(repo, "rev-parse", "HEAD")
            assert env is None
    assert (git_dir / "index").read_bytes() == before
    assert set(os.listdir(git_dir)) == files


def test_turns_in_another_repository_with_another_kind_of_index(
        tmp_path, hook_env, stub_api, kind_of_index):
    """The session was started in a folder that only holds it. New files that
    cannot be added are told about once."""
    hook_env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    repo = other_index(tmp_path / "vendor", kind_of_index)
    for turn in range(3):
        conftest.run_hook(conftest.ups_payload(repo), hook_env)
        (repo / "lib.py").write_text(conftest.VULN_PY.replace("def run", f"def turn{turn}"))
        (repo / f"new{turn}.py").write_text(conftest.VULN_PY.replace("def run", f"def added{turn}"))
        code, out, _ = conftest.run_hook(conftest.stop_payload(repo), hook_env)
        m = conftest.metrics_of(out)
        sent = "".join(stub_api.bodies)
        assert f"def turn{turn}" in sent
        if kind_of_index == "sha256":
            assert code == 0 and "add_fail" not in m and f"def added{turn}" in sent, m
        else:
            assert code == (0 if turn else 2) and m["add_fail"] // 100000 == 5, m


def test_split_index_set_for_all_repositories_leaves_nothing_behind(project, clean_env):
    repo = new_repo(project / "vendor")
    (clean_env / ".gitconfig").write_text("[core]\n\tsplitIndex = true\n")
    git(repo, "update-index", "--split-index")
    files = set(os.listdir(repo / ".git"))
    for n in range(3):
        (repo / "lib.py").write_text(f"x = {n}\n")
        diffstate.capture_git_baseline(str(repo))
        (repo / f"new{n}.py").write_text("x = 1\n")
        with gitutil._temp_index(str(repo), [f"new{n}.py"]):
            pass
    assert set(os.listdir(repo / ".git")) == files


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="named pipes")
@pytest.mark.parametrize("kind", ["settings", "split"])
def test_named_pipe_in_a_worktree_of_the_session_repo(project, tmp_path, kind):
    wt = project / "wt"
    git(project, "worktree", "add", "-q", str(wt))
    if kind == "settings":
        git(project, "config", "filter.probe.clean", "cat")
    else:
        git(wt, "update-index", "--split-index")
    back = project / ".git" / "worktrees" / "wt" / "gitdir"
    back.unlink()
    os.mkfifo(back)
    start = time.monotonic()
    prompt_hook(wt, tmp_path)
    assert time.monotonic() - start < 30


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="named pipes")
def test_named_pipe_in_the_settings_below_a_git_that_is_a_script(project, tmp_path, monkeypatch):
    """Killing the script leaves git itself with the pipe open."""
    repo = new_repo(project / "vendor")
    os.mkfifo(repo / "pipe")
    add_config(repo, "[include]\n\tpath = ../pipe\n")
    shim = tmp_path / "shim"
    shim.write_text('#!/bin/sh\ngit "$@"\nexit $?\n')
    shim.chmod(0o755)
    monkeypatch.setattr(gitutil, "GIT_CMD", [str(shim), *gitutil.GIT_CMD[1:]])
    start = time.monotonic()
    assert gitutil._stay_out(str(repo))
    assert time.monotonic() - start < 20
    with open(os.open(repo / "pipe", os.O_WRONLY | os.O_NONBLOCK), "wb"):
        pass  # lets what is left of git end


def test_settings_are_read_without_a_folder_to_write_in(project, tmp_path, monkeypatch):
    repo = new_repo(project / "vendor")
    wt = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(wt))

    def none(*args, **kw):
        raise FileNotFoundError("No usable temporary directory found")

    monkeypatch.setattr(gitutil.tempfile, "TemporaryFile", none)
    assert gitutil._git_toplevel(str(repo)) and gitutil._git_toplevel(str(wt))


@pytest.mark.skipif(os.name == "nt", reason="symbolic links and devices")
@pytest.mark.parametrize("where", ["other", "session", "file"])
def test_index_that_is_a_link(project, where):
    """To something without an end, or to an ordinary file."""
    repo = project if where == "session" else new_repo(project / "vendor")
    index = repo / ".git" / "index"
    edit(repo)
    if where == "file":
        index.rename(repo / ".git" / "real")
        index.symlink_to("real")
    else:
        index.unlink()
        index.symlink_to("/dev/zero")
    start = time.monotonic()
    copy = repo / ".git" / "copy"
    copy.symlink_to(index)
    assert gitutil._index_holds(copy, b"nothing") is (where != "file")
    assert (gitutil._write_file_entries(str(repo), str(copy)) is None) is (where != "file")
    diffstate.capture_git_baseline(str(repo))
    assert time.monotonic() - start < 20


def test_index_that_grows_past_the_limit(project, monkeypatch):
    repo = new_repo(project / "vendor")
    index = repo / ".git" / "index"
    monkeypatch.setattr(gitutil, "_MAX_INDEX_BYTES", os.path.getsize(index) - 1)
    assert gitutil._write_file_entries(str(repo), str(index)) is None


@pytest.mark.parametrize("empty", ["folder", "file"])
def test_folder_in_no_repository_below_an_entry_that_is_none(project, tmp_path, hook_env, empty):
    home = tmp_path / "some"
    (home / "notes").mkdir(parents=True)
    if empty == "folder":
        (home / ".git").mkdir()
    else:
        (home / ".git").write_text("")
    cwd = str(home / "notes")
    assert not gitutil.in_left_out_repo(cwd)
    assert gitutil.session_repo_instead_of(cwd) is None
    assert gitutil._git_toplevel(cwd) is None
    assert gitutil.repos_left_alone() == 0


@pytest.mark.parametrize("what", ["worktree", "other", "session"])
def test_config_that_lists_too_much(project, tmp_path, monkeypatch, what):
    repo = project
    if what == "other":
        repo = new_repo(project / "vendor")
    add_config(repo, "[a]\n" + f"\tb = {'x' * 1000}\n" * 200)
    cwd = repo
    if what == "worktree":
        cwd = tmp_path / "wt"
        git(project, "worktree", "add", "-q", str(cwd))
    assert gitutil._git_toplevel(str(cwd)) and gitutil.session_repo_commands() == 0
    monkeypatch.setattr(gitutil, "_MAX_CONFIG_BYTES", 100_000)
    gitutil._other_repos.clear()
    assert bool(gitutil._git_toplevel(str(cwd))) is (what == "session")
    assert gitutil.session_repo_commands() == (256 if what != "other" else 0)


@pytest.mark.parametrize("mode", [0o160000, 0o160644])
def test_repository_in_another_ones_index_of_another_kind(project, marker, kind_of_index, mode):
    outer = holds_a_repository(other_index(project / "vendor", kind_of_index), marker, again=True)
    if mode != 0o160000:
        n = 32 if kind_of_index == "sha256" else 20
        index, swap = outer / ".git" / "index", {b"\x00\x00\xe0\x00": struct.pack(">I", mode)}
        # The index names the file it shares by its checksum.
        for f in [*(outer / ".git").glob("sharedindex.*"), index]:
            data = f.read_bytes()
            f.chmod(0o600)
            old, data = data[-n:], data[:-n]
            for a, b in swap.items():
                data = data.replace(a, b)
            new = gitutil._ID_HASHES[n](data).digest()
            f.write_bytes(data + new)
            if f != index:
                swap[old] = new
                f.rename(f.with_name("sharedindex." + new.hex()))
        os.utime(index, (1e9, 1e9))
        assert b"%o" % mode in subprocess.run(["git", "ls-files", "-s"], cwd=outer, capture_output=True).stdout
    assert diffstate.capture_git_baseline(str(outer))
    (outer / "new.py").write_text("x = 1\n")
    with gitutil._temp_index(str(outer), ["new.py"]) as env:
        assert bool(env) is (kind_of_index == "sha256")
    assert not marker.exists()


@sparse_index
@pytest.mark.parametrize("in_order", [True, False])
def test_repository_in_a_collapsed_directory_of_another_one(project, tmp_path, marker, in_order):
    outer = sparse_repo(tmp_path / "outer")
    pull_a_repository(outer, tmp_path, marker, '[submodule "sub"]\n\tpath = out/sub\n\turl = ./x\n\tignore = none\n',
                      in_order=in_order)
    assert diffstate.capture_git_baseline(str(outer)) == git(outer, "rev-parse", "HEAD")
    (outer / "new.py").write_text("x = 1\n")
    with gitutil._temp_index(str(outer), ["new.py"]) as env:
        assert env is None
    assert not marker.exists()


@sparse_index
def test_worktree_of_a_session_repo_with_a_sparse_index(tmp_path, monkeypatch):
    """It keeps its index, whole or not."""
    project = sparse_repo(tmp_path / "proj")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    wt = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(wt))
    git(wt, "sparse-checkout", "init", "--cone", "--sparse-index")
    git(wt, "sparse-checkout", "set", "in")
    assert gitutil.may_be_sparse(project / ".git" / "worktrees" / "wt" / "index")
    (wt / "lib.py").write_text("print('three')\n")
    sha = diffstate.capture_git_baseline(str(wt))
    assert git(wt, "diff", "--name-only", "HEAD", sha) == "lib.py"


def entries(index):
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    run = lambda *a: subprocess.run(["git", *a], cwd=index.parent, env=env, check=True,
                                    capture_output=True).stdout
    return run("ls-files", "-s", "-v", "-z"), re.sub(rb"(?m)^  ", b"", run("ls-files", "--debug"))


@pytest.mark.parametrize("version", ["2", "4"])
def test_copy_with_only_the_files(tmp_path, version):
    repo = new_repo(tmp_path / "r")
    for n in range(1, 20):
        f = repo / "d" / ("x" * n)
        f.parent.mkdir(exist_ok=True)
        f.write_text(str(n))
    (repo / "d" / "run.sh").write_text("x")
    git(repo, "add", "-A")
    git(repo, "update-index", "--chmod=+x", "d/run.sh")
    blob = git(repo, "rev-parse", "HEAD:lib.py")
    for mode, name in (("120000", "lnk"), ("100644", "y" * 300), ("100644", "z" * 4200)):
        git(repo, "update-index", "--add", "--cacheinfo", f"{mode},{blob},{name}")
    git(repo, "update-index", "--assume-unchanged", "d/x")
    git(repo, "update-index", "--skip-worktree", "d/xx")
    (repo / "new.py").write_text("x")
    git(repo, "add", "-N", "new.py")
    git(repo, "update-index", "--index-version", version)
    index = repo / ".git" / "index"
    before = index.read_bytes()
    new, left_out = gitutil._file_entries(before)
    copy = repo / ".git" / "copy"
    copy.write_bytes(new)
    assert left_out == 0
    assert entries(copy) == entries(index)
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{'12' * 20},d/xxxy")
    new, left_out = gitutil._file_entries(index.read_bytes())
    copy.write_bytes(new)
    assert left_out == 1
    assert b"160000" in entries(index)[0] and b"160000" not in entries(copy)[0]
    assert entries(copy)[0].count(b"\0") == entries(index)[0].count(b"\0") - 1


@pytest.mark.parametrize("change", [
    lambda d: d[:-21] + d[-20:], lambda d: d[:40], lambda d: b"", lambda d: b"X" + d[1:],
    lambda d: d[:8] + b"\xff\xff\xff\xff" + d[12:], lambda d: d[:7] + b"\x09" + d[8:],
    lambda d: d[:-20] + b"link\0\0\0\0" + d[-20:], lambda d: d[:-20] + b"sdir\0\0\0\0" + d[-20:],
    lambda d: d[:-20] + b"AAAA\0\0\0\x09" + d[-20:]])
def test_index_that_is_not_read_as_git_wrote_it(tmp_path, change):
    data = (new_repo(tmp_path / "r") / ".git" / "index").read_bytes()
    gitutil._file_entries(data)
    with pytest.raises((ValueError, IndexError, struct.error)):
        gitutil._file_entries(change(data))


def test_index_that_asks_to_shorten_a_name_by_more_than_it_has(tmp_path):
    entry = bytearray(62)
    struct.pack_into(">I", entry, 24, 0o100644)
    struct.pack_into(">H", entry, 60, 1)
    data = b"DIRC" + struct.pack(">II", 4, 1) + bytes(entry) + b"\xff" * 4_000_000 + b"\x01a\0" + b"\0" * 20
    start = time.monotonic()
    with pytest.raises(ValueError):
        gitutil._file_entries(data)
    assert time.monotonic() - start < 1


@pytest.mark.skipif(GIT_VERSION < (2, 42), reason="git with only one kind of object id")
def test_index_with_other_object_ids(project):
    repo = project / "vendor"
    repo.mkdir()
    git(repo, "init", "-q", "--object-format=sha256")
    new_repo(repo)
    ids = (new_repo(project / "other") / ".git" / "index").read_bytes()
    index = repo / ".git" / "index"
    index.write_bytes(ids)  # one that reads well with the usual ids
    assert gitutil._write_file_entries(str(repo), str(index)) is None
    assert index.read_bytes() == ids


def test_new_files_left_out_with_the_copy_are_noted(project, monkeypatch):
    repo = new_repo(project / "vendor")
    (repo / "new.py").write_text("x = 1\n")
    with gitutil._temp_index(str(repo), ["new.py"]) as env:
        assert env
    monkeypatch.setattr(gitutil, "_add_failed", {"code": 0, "left_out": False})
    monkeypatch.setattr(gitutil, "_MAX_INDEX_BYTES", 10)
    with gitutil._temp_index(str(repo), ["new.py"]) as env:
        assert env is None
    assert gitutil._add_failed == {"code": 500001, "left_out": True}


@pytest.mark.parametrize("big", [False, True])
def test_worktree_of_the_session_repo_keeps_its_index(project, tmp_path, monkeypatch, big):
    wt = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(wt))
    (wt / "lib.py").write_text("print('three')\n")
    if big:
        monkeypatch.setattr(gitutil, "_BIG_INDEX_BYTES", 0)
    rewritten = []
    real = gitutil._write_file_entries
    monkeypatch.setattr(gitutil, "_write_file_entries", lambda *a: rewritten.append(a) or real(*a))
    sha = diffstate.capture_git_baseline(str(wt))
    assert sha and sha != git(wt, "rev-parse", "HEAD")
    assert bool(rewritten) is not big


def test_copy_of_another_repository(project, monkeypatch):
    repo = new_repo(project / "vendor")
    index = repo / ".git" / "index"
    os.utime(index, ns=(10**18, 10**18))
    before = index.read_bytes()
    folder = None
    with gitutil._temp_index(str(repo), []) as env:
        copy = env["GIT_INDEX_FILE"]
        folder = os.path.dirname(copy)
        assert os.stat(copy).st_mtime_ns == 10**18
        assert not os.path.samefile(copy, index)
    assert index.read_bytes() == before
    assert not [n for n in os.listdir(folder) if n.startswith(os.path.basename(copy))]


def test_whole_tree_add_in_a_repository_with_link_in_a_name(project):
    (project / "linked.py").write_text("x")
    git(project, "add", "linked.py")
    (project / "new.py").write_text("x")
    with gitutil._temp_index(str(project)) as env:
        assert env


@sparse_index
def test_new_file_next_to_a_collapsed_directory(tmp_path, monkeypatch, marker):
    project = sparse_repo(tmp_path / "proj")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    pull_a_repository(project, tmp_path, marker)
    (project / "in" / "new.py").write_text("x = 1\n")
    with gitutil._temp_index(str(project), ["in/new.py"]) as env:
        listed = subprocess.run([*gitutil.GIT_CMD, *gitutil.SPARSE_AS_IT_IS, "ls-files", "-s", "--sparse"],
                                cwd=project, env=env, capture_output=True, text=True).stdout
    assert "in/new.py" in listed and "160000" not in listed
    assert not marker.exists()


def test_repository_the_user_named_is_kept(project, tmp_path, monkeypatch):
    home = tmp_path / "dots"
    home.mkdir()
    (home / "lib.py").write_text("print('one')\n")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(home))
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("GIT_WORK_TREE", str(home))
    git(home, "init", "-q")
    git(home, "add", "-A")
    git(home, "commit", "-q", "-m", "i")
    git(home, "update-index", "--split-index")
    (home / "lib.py").write_text("print('three')\n")
    sha = diffstate.capture_git_baseline(str(home))
    assert sha and sha != git(home, "rev-parse", "HEAD")


def test_ordinary_repository_that_holds_another_keeps_its_baseline(project, tmp_path, marker):
    outer = new_repo(project / "vendor")
    inner = new_repo(tmp_path / "inner")
    git(outer, "update-index", "--add", "--cacheinfo",
        f"160000,{git(inner, 'rev-parse', 'HEAD')},sub")
    git(outer, "commit", "-q", "-m", "sub")
    os.rename(inner, outer / "sub")
    (outer / "lib.py").write_text("print('three')\n")
    sha = diffstate.capture_git_baseline(str(outer))
    assert sha and sha != git(outer, "rev-parse", "HEAD")


@pytest.mark.parametrize("start_there", [True, False])
def test_index_of_the_session_repo_that_is_not_in_order(project, tmp_path, monkeypatch, marker, start_there):
    """git does not find an entry that is out of order to remove it."""
    outer = holds_a_repository(tmp_path / "own", marker, "!ub", "sub")
    rewrite_index(outer, b"!ub", b"sub")
    if start_there:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(outer))
    else:
        monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    assert diffstate.capture_git_baseline(str(outer)) == git(outer, "rev-parse", "HEAD")
    (outer / "new.py").write_text("x = 1\n")
    with gitutil._temp_index(str(outer), ["new.py"]) as env:
        assert env is None
    assert gitutil._add_failed["left_out"]
    assert not marker.exists()
