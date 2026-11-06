import os
import subprocess
import tempfile

import pytest

from conftest import (
    GIT_ENV, STUB_VULN, VULN_PY, git, make_repo, metrics_of, run_hook,
    stop_payload, ups_payload, write_cli,
)

import diffstate
import gitutil


def _add_nested_repo(parent, rel, marker):
    """A directory with its own `.git` whose config names a filter command,
    the way an unpacked archive or a vendored checkout can. The command leaves
    a line in `marker` each time git runs it."""
    nested = make_repo(parent / rel, {
        "lib.py": "print('one')\n",
        ".gitattributes": "* filter=probe\n",
    })
    git(nested, "config", "filter.probe.clean",
        f"sh -c 'echo ran >> \"{marker.as_posix()}\"; cat'")
    # Same size, so git has to read the file to tell whether it changed.
    (nested / "lib.py").write_text("print('two')\n")
    old = os.stat(nested / ".git" / "index").st_mtime - 3600
    os.utime(nested / ".git" / "index", (old, old))
    return nested


@pytest.fixture
def outer(tmp_path):
    return make_repo(tmp_path / "outer", {"app.py": "print('hi')\n"})


@pytest.fixture
def marker(tmp_path):
    return tmp_path / "filter-ran"


def _turn(repo, hook_env, stub_api, during):
    stub_api.vulns = [STUB_VULN]
    assert run_hook(ups_payload(repo), hook_env)[0] == 0
    during()
    return run_hook(stop_payload(repo), hook_env)


def test_untracked_nested_repo_filter_not_run(outer, marker, hook_env, stub_api):
    def during():
        _add_nested_repo(outer, "vendor/pkg", marker)
        (outer / "app.py").write_text(VULN_PY)

    rc, out, err = _turn(outer, hook_env, stub_api, during)

    assert not marker.exists(), marker.read_text()
    # The turn's own edit is still reviewed.
    assert stub_api.calls, (rc, out, err)
    assert "app.py" in out + err


def test_untracked_nested_repo_alone_is_not_reviewed(outer, marker, hook_env, stub_api):
    rc, out, err = _turn(
        outer, hook_env, stub_api,
        lambda: _add_nested_repo(outer, "vendor/pkg", marker))

    assert not marker.exists(), marker.read_text()
    assert not stub_api.calls
    assert (metrics_of(out) or {}).get("skipped") is True


@pytest.fixture
def git_env(tmp_path, monkeypatch):
    """For calling gitutil in this process: a temp dir of our own, and the
    environment restored afterwards."""
    d = tmp_path / "tmproot"
    d.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(d))
    saved = dict(os.environ)
    os.environ.update(GIT_ENV)
    yield
    os.environ.clear()
    os.environ.update(saved)


def _record_nested_repo(outer, marker, gitmodules=None):
    nested = _add_nested_repo(outer, "vendor/pkg", marker)
    if gitmodules:
        (outer / ".gitmodules").write_text(gitmodules)
    git(outer, "add", "-A")
    git(outer, "commit", "-q", "-m", "add vendor/pkg")
    if marker.exists():
        marker.unlink()
    return nested


def test_untracked_nested_repo_is_not_a_changed_file(outer, marker, git_env):
    _add_nested_repo(outer, "vendor/pkg", marker)
    (outer / "new.py").write_text("x = 1\n")

    tracked, untracked = gitutil._git_status_porcelain(str(outer))

    assert (tracked, untracked) == (set(), {"new.py"})


def test_intent_to_add_skips_nested_repos(outer, marker, git_env):
    _add_nested_repo(outer, "vendor/pkg", marker)
    (outer / "new.py").write_text("x = 1\n")

    with gitutil._temp_index(str(outer), ["new.py", "vendor/pkg/"]) as env:
        assert env is not None
        listed = subprocess.run(
            ["git", "ls-files", "-s"], cwd=outer, capture_output=True,
            text=True, env=env,
        ).stdout

    assert "new.py" in listed
    assert "160000" not in listed
    assert not marker.exists()


# A repository can ask for one submodule to be checked whatever the default.
GITMODULES_IGNORE_NONE = (
    '[submodule "pkg"]\n\tpath = vendor/pkg\n\turl = ./vendor/pkg\n\tignore = none\n'
)


@pytest.mark.parametrize("gitmodules", [None, GITMODULES_IGNORE_NONE])
def test_status_and_diff_leave_out_recorded_nested_repo(outer, marker, git_env, gitmodules):
    nested = _record_nested_repo(outer, marker, gitmodules)
    (nested / "lib.py").write_text("print('abc')\n")
    (outer / "app.py").write_text(VULN_PY)

    tracked, untracked = gitutil._git_status_porcelain(str(outer))
    diff = gitutil.get_git_diff(str(outer), "HEAD", untracked_paths=[])
    names = gitutil._git_name_only(str(outer), "HEAD")

    assert tracked == {"app.py"}
    assert names == {"app.py"}
    assert "app.py" in diff and "vendor/pkg" not in diff
    assert not marker.exists()


def test_commit_range_diff_does_not_enter_nested_repo(outer, marker, git_env, tmp_path):
    nested = _record_nested_repo(outer, marker, GITMODULES_IGNORE_NONE)
    ext_marker = tmp_path / "ext-diff-ran"
    git(nested, "config", "diff.external",
        f"sh -c 'echo ran >> \"{ext_marker.as_posix()}\"'")
    base = git(outer, "rev-parse", "HEAD").strip()
    git(nested, "commit", "-q", "-am", "two")
    git(outer, "commit", "-q", "-am", "move vendor/pkg")
    for m in (marker, ext_marker):
        if m.exists():
            m.unlink()
    # The user's own setting asks for a submodule's changes inline.
    os.environ.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "diff.submodule",
                       "GIT_CONFIG_VALUE_0": "diff"})

    out = gitutil._git_diff_range(str(outer), base, "HEAD")

    assert not ext_marker.exists() and not marker.exists()
    assert "lib.py" not in (out or "")


def _record_during_turn(outer, marker, commit):
    _add_nested_repo(outer, "vendor/pkg", marker)
    (outer / "app.py").write_text(VULN_PY)
    git(outer, "add", "-A")
    if commit:
        git(outer, "commit", "-q", "-m", "wip")
    marker.unlink(missing_ok=True)  # only what the hooks run counts


@pytest.mark.parametrize("finding", [False, True], ids=["no-finding", "finding"])
@pytest.mark.parametrize("commit", [False, True], ids=["staged", "committed"])
def test_nested_repo_recorded_during_the_turn_filter_not_run(
        outer, marker, hook_env, stub_api, commit, finding):
    stub_api.vulns = [STUB_VULN] if finding else []
    ran_at = []

    def hook(name, payload):
        rc, out, err = run_hook(payload, hook_env)
        # 2 is a Stop that hands a finding back.
        assert rc == (2 if finding and name.startswith("stop") else 0), (name, out, err)
        if marker.exists():
            ran_at.append(name)
            marker.unlink()

    hook("prompt 1", ups_payload(outer))
    _record_during_turn(outer, marker, commit)
    hook("stop 1", stop_payload(outer))
    hook("prompt 2", ups_payload(outer))
    (outer / "app.py").write_text(VULN_PY + "# one more edit\n")
    hook("stop 2", stop_payload(outer))
    hook("prompt 3", ups_payload(outer))

    assert ran_at == []
    assert stub_api.calls  # the turn's own edit is still reviewed


@pytest.mark.skipif(os.name == "nt", reason="'*' is not allowed in Windows file names")
@pytest.mark.parametrize("commit", [False, True], ids=["staged", "committed"])
def test_glob_shaped_file_name_beside_recorded_nested_repo(
        outer, marker, hook_env, stub_api, commit):
    assert run_hook(ups_payload(outer), hook_env)[0] == 0
    _record_during_turn(outer, marker, commit)
    (outer / "vendor" / "p*").write_text("x = 1\n")
    (outer / "new.py").write_text(VULN_PY)

    rc, out, err = run_hook(stop_payload(outer), hook_env)

    assert not marker.exists(), marker.read_text()
    assert stub_api.calls, (rc, out, err)


def _index_copies():
    return [f for _, _, files in os.walk(tempfile.gettempdir()) for f in files
            if f.startswith(gitutil._TEMP_INDEX_PREFIX)]


def _index_entries(repo, env=None):
    return subprocess.run(
        ["git", "ls-files", "-s"], cwd=repo, capture_output=True, text=True,
        env=env, check=True,
    ).stdout


@pytest.mark.parametrize("subdir", ["", "src"])
def test_index_copy_has_no_gitlinks_and_real_index_is_unchanged(
        outer, marker, git_env, subdir):
    (outer / "src").mkdir()
    (outer / "src" / "a.py").write_text("x = 1\n")
    _add_nested_repo(outer, "src/third party/dep", marker)
    _record_nested_repo(outer, marker)
    real = outer / ".git" / "index"
    before = (real.read_bytes(), real.stat().st_mtime_ns)

    with gitutil._temp_index(str(outer / subdir), untracked_paths=[]) as env:
        assert env is not None
        assert len(_index_copies()) == 1
        copy = _index_entries(outer, env)
        copy_mtime = os.stat(env["GIT_INDEX_FILE"]).st_mtime_ns

    assert "160000" not in copy
    assert "app.py" in copy and "src/a.py" in copy
    assert copy_mtime == before[1]
    assert (real.read_bytes(), real.stat().st_mtime_ns) == before
    assert _index_entries(outer).count("160000") == 2
    assert not marker.exists()


def test_baseline_and_diff_with_recorded_nested_repo(outer, marker, git_env):
    nested = _record_nested_repo(outer, marker)
    (nested / "lib.py").write_text("print('abc')\n")
    (outer / "app.py").write_text(VULN_PY)
    (outer / "new.py").write_text("x = 1\n")

    baseline = diffstate.capture_git_baseline(str(outer))
    diff = gitutil.get_git_diff(str(outer), "HEAD", untracked_paths=["new.py"])
    since = gitutil.get_git_diff(str(outer), baseline, untracked_paths=["new.py"])
    # The snapshot has no entry for the nested repository; the real index does.
    tracked_since = gitutil.get_git_diff(str(outer), baseline, untracked_paths=[])
    names_since = gitutil._git_name_only(str(outer), baseline)

    # The baseline is a snapshot with the edit in it, not HEAD.
    assert baseline and baseline != git(outer, "rev-parse", "HEAD").strip()
    assert "app.py" in diff and "new.py" in diff and "vendor/pkg" not in diff
    assert "new.py" in since and "app.py" not in since and "vendor/pkg" not in since
    assert tracked_since == "" and "vendor/pkg" not in names_since
    assert not marker.exists()


def test_whole_tree_index_copy_with_recorded_nested_repo(outer, marker, git_env):
    nested = _record_nested_repo(outer, marker)
    (nested / "lib.py").write_text("print('abc')\n")
    (outer / "new.py").write_text("x = 1\n")

    with gitutil._temp_index(str(outer)) as env:
        assert env is not None
        copy = _index_entries(outer, env)

    assert "new.py" in copy and "160000" not in copy
    assert not marker.exists()


def test_no_index_copy_when_gitlinks_cannot_be_removed(
        outer, marker, git_env, monkeypatch):
    _record_nested_repo(outer, marker)
    (outer / "app.py").write_text(VULN_PY)
    real_run = subprocess.run

    def run(cmd, *a, **kw):
        if "update-index" in cmd:
            return subprocess.CompletedProcess(cmd, 1, b"", b"no")
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(gitutil.subprocess, "run", run)

    with gitutil._temp_index(str(outer), untracked_paths=[]) as env:
        assert env is None
    # Without the copy the baseline is HEAD.
    assert diffstate.capture_git_baseline(str(outer)) == git(outer, "rev-parse", "HEAD").strip()
    assert diffstate.last_baseline_fail == 2
    assert not marker.exists()
    assert _index_copies() == []


@pytest.mark.skipif(os.name == "nt", reason="':' and '*' are not allowed in Windows file names")
def test_untracked_file_name_is_not_read_as_a_pattern(outer, git_env):
    name = ":(glob)**"
    (outer / name).write_text("x = 1\n")
    (outer / "other.py").write_text("x = 2\n")

    with gitutil._temp_index(str(outer), [name]) as env:
        copy = _index_entries(outer, env)

    assert name in copy and "other.py" not in copy


def test_gitlink_without_a_repository_stays_in_the_copy(outer, marker, git_env):
    """A submodule that is not checked out: an empty directory."""
    nested = _record_nested_repo(outer, marker)
    # Moved, not deleted: git's object files are read-only on Windows.
    nested.rename(outer.parent / "moved-away")
    nested.mkdir()
    (outer / "app.py").write_text(VULN_PY)

    with gitutil._temp_index(str(outer), untracked_paths=[]) as env:
        copy = _index_entries(outer, env)
    baseline = diffstate.capture_git_baseline(str(outer))

    assert "160000" in copy
    assert baseline and baseline != git(outer, "rev-parse", "HEAD").strip()
    assert diffstate.last_baseline_fail == 0


def test_gitlinks_listed_by_a_git_without_sparse_listing(outer, marker, git_env, monkeypatch):
    _record_nested_repo(outer, marker)
    real_popen = subprocess.Popen
    seen = []

    def popen(cmd, *a, **kw):
        if "ls-files" in cmd and "-z" in cmd:  # the plugin's own listing
            seen.append("--sparse" in cmd)
        if "--sparse" in cmd:
            cmd = [*gitutil.GIT_CMD, "ls-files", "--no-such-option"]
        return real_popen(cmd, *a, **kw)

    monkeypatch.setattr(gitutil.subprocess, "Popen", popen)
    monkeypatch.setattr(gitutil, "_ls_files_sparse", True)

    for _ in range(2):
        with gitutil._temp_index(str(outer), untracked_paths=[]) as env:
            assert "160000" not in _index_entries(outer, env)

    assert seen == [True, False, False]


def test_no_index_copy_when_the_listing_cannot_be_watched(outer, marker, git_env, monkeypatch):
    _record_nested_repo(outer, marker)

    def no_thread(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(gitutil.threading.Timer, "start", no_thread)

    with gitutil._temp_index(str(outer), untracked_paths=[]) as env:
        assert env is None
    assert _index_copies() == []


def _listings(monkeypatch):
    """Counts the plugin's own `git ls-files` runs."""
    real_popen = subprocess.Popen
    seen = []

    def popen(cmd, *a, **kw):
        if "ls-files" in cmd and "-z" in cmd:
            seen.append(cmd)
        return real_popen(cmd, *a, **kw)

    monkeypatch.setattr(gitutil.subprocess, "Popen", popen)
    return seen


def test_index_without_gitlinks_is_not_listed(outer, git_env, monkeypatch):
    for i in range(300):
        (outer / f"f{i}.py").write_text(f"x = {i}\n")
    git(outer, "add", "-A")
    seen = _listings(monkeypatch)

    with gitutil._temp_index(str(outer), untracked_paths=[]) as env:
        assert env is not None

    assert seen == []


@pytest.mark.parametrize("setup", [
    [],
    [("config", "index.version", "4")],
    [("config", "core.splitIndex", "true")],
    [("config", "feature.manyFiles", "true")],
], ids=["default", "index-v4", "split-index", "many-files"])
def test_gitlink_found_in_every_index_format(outer, marker, git_env, monkeypatch, setup):
    for args in setup:
        git(outer, *args)
    for i in range(50):
        (outer / f"f{i}.py").write_text(f"x = {i}\n")
    git(outer, "add", "-A")
    git(outer, "commit", "-q", "-m", "files")
    nested = _record_nested_repo(outer, marker)
    # One more index write after the gitlink went in.
    (outer / "later.py").write_text("x = 1\n")
    git(outer, "add", "later.py")
    marker.unlink(missing_ok=True)
    (nested / "lib.py").write_text("print('abc')\n")
    (outer / "app.py").write_text(VULN_PY)
    seen = _listings(monkeypatch)

    with gitutil._temp_index(str(outer), untracked_paths=[]) as env:
        copy = _index_entries(outer, env)
    baseline = diffstate.capture_git_baseline(str(outer))

    assert seen and "160000" not in copy and "later.py" in copy
    assert baseline != git(outer, "rev-parse", "HEAD").strip()
    assert not marker.exists()


def _signed_head(repo, tmp_path, marker):
    """Make HEAD a commit that carries a signature, with log.showSignature on
    and gpg.program naming a stand-in that leaves a line in `marker`."""
    program = write_cli(tmp_path, "signature-check", (
        "import sys\n"
        f"open({str(marker)!r}, 'a').write('ran\\n')\n"
        "sys.exit(1)\n"))
    head = git(repo, "rev-parse", "HEAD").strip()
    tree = git(repo, "rev-parse", "HEAD^{tree}").strip()
    who = "t <t@example.com> 1800000000 +0000"
    commit = (
        f"tree {tree}\nparent {head}\nauthor {who}\ncommitter {who}\n"
        "gpgsig -----BEGIN PGP SIGNATURE-----\n \n xx\n"
        " -----END PGP SIGNATURE-----\n\nsigned\n")
    sha = subprocess.run(
        ["git", "hash-object", "-t", "commit", "-w", "--stdin"], cwd=repo,
        input=commit.encode(), capture_output=True, check=True,
    ).stdout.decode().strip()
    git(repo, "update-ref", "--create-reflog", "-m", "commit: signed", "HEAD", sha)
    git(repo, "config", "log.showSignature", "true")
    git(repo, "config", "gpg.program", str(program))
    return sha


def test_reading_the_reflog_does_not_check_signatures(outer, marker, tmp_path, git_env):
    sha = _signed_head(outer, tmp_path, marker)
    # The stand-in does run for a plain `git log` in this repository.
    git(outer, "log", "-1")
    assert marker.exists()
    marker.unlink()

    fresh, _stale = gitutil._git_reflog_recent_commits(str(outer), max_age_s=10**10)

    assert sha in fresh
    assert not marker.exists(), marker.read_text()


def test_reviewer_environment_turns_signature_display_off(outer, marker, tmp_path, git_env):
    _signed_head(outer, tmp_path, marker)

    gitutil.apply_safe_git_env()
    git(outer, "log", "-1")

    assert not marker.exists(), marker.read_text()
