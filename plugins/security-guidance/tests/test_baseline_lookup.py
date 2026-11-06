import os

import pytest

from conftest import git, make_repo, run_hook, ups_payload

import diffstate

OLD = "import os\nos.system(cmd)\n"
FILE = "packages/app/main.py"


def write_payload(cwd, file_path, content, session_id="s1"):
    return {
        "session_id": session_id,
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(file_path), "content": content},
        "tool_response": {},
        "cwd": str(cwd),
    }


@pytest.fixture
def repo(tmp_path):
    repo = make_repo(tmp_path / "ws" / "mono")
    # Bytes, so the committed text is OLD on every platform: write_text turns
    # "\n" into "\r\n" on Windows.
    for name in (FILE, "top.py"):
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_bytes(OLD.encode())
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add files")
    return repo


def _symlink(link, target):
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError):
        if os.name != "nt":
            raise
        pytest.skip("this Windows account cannot create symlinks")


@pytest.fixture
def linked(repo, tmp_path):
    """The same repo, reached through a symlinked parent directory."""
    _symlink(tmp_path / "alias", tmp_path / "ws")
    return tmp_path / "alias" / "mono"


@pytest.fixture
def baseline(repo, monkeypatch):
    sha = git(repo, "rev-parse", "HEAD").strip()
    monkeypatch.setattr(diffstate, "load_baseline_sha", lambda _sid: sha)
    return sha


class TestBaselineFileContent:
    """`git show <rev>:<path>` reads the path from the repo root, so the lookup
    must not depend on where in the repo the session was started."""

    @pytest.mark.parametrize("session_dir", ["", "packages", "packages/app"])
    def test_found_from_any_session_directory(self, repo, baseline, session_dir):
        cwd = str(repo / session_dir)
        assert diffstate.get_baseline_file_content("s1", str(repo / FILE), cwd) == OLD
        assert diffstate.get_baseline_file_content("s1", str(repo / "top.py"), cwd) == OLD

    def test_native_separators_are_not_passed_to_git(self, repo, baseline, monkeypatch):
        # What os.path.relpath returns on Windows.
        monkeypatch.setattr(diffstate.os, "sep", "\\")
        monkeypatch.setattr(diffstate.os.path, "relpath",
                            lambda _p, _start: "packages\\app\\main.py")
        assert diffstate.get_baseline_file_content("s1", str(repo / FILE), str(repo)) == OLD

    def test_file_not_in_baseline(self, repo, baseline):
        (repo / "packages" / "app" / "new.py").write_text(OLD)
        for p in ("packages/app/new.py", "packages/gone/main.py"):
            assert diffstate.get_baseline_file_content(
                "s1", str(repo / p), str(repo / "packages")) is None

    def test_file_outside_the_session_repo(self, repo, baseline, tmp_path):
        outside = tmp_path / "ws" / "main.py"
        outside.write_text(OLD)
        assert diffstate.get_baseline_file_content("s1", str(outside), str(repo)) is None
        # A second checkout of the same repo shares its objects; its files are
        # still not this session's baseline.
        git(repo, "worktree", "add", "-q", str(tmp_path / "ws" / "other"), "-b", "other")
        twin = tmp_path / "ws" / "other" / FILE
        assert twin.read_bytes().replace(b"\r\n", b"\n") == OLD.encode()
        for cwd in (repo, repo / "packages" / "app"):
            assert diffstate.get_baseline_file_content("s1", str(twin), str(cwd)) is None

    @pytest.mark.parametrize("session_dir", ["", "packages/app"])
    def test_found_through_a_symlinked_directory(self, repo, baseline, linked, session_dir):
        """macOS reaches /tmp and /var through symlinks, so the tool's path and
        the session directory can spell the same repo differently."""
        real, alias = repo / session_dir, linked / session_dir
        for cwd, path in ((real, linked / FILE), (alias, repo / FILE), (alias, linked / FILE)):
            assert diffstate.get_baseline_file_content("s1", str(path), str(cwd)) == OLD

    def test_session_directory_is_a_symlink_into_the_repo(self, repo, baseline, tmp_path):
        _symlink(tmp_path / "app", repo / "packages" / "app")
        for path in (tmp_path / "app" / "main.py", repo / FILE):
            assert diffstate.get_baseline_file_content(
                "s1", str(path), str(tmp_path / "app")) == OLD

    def test_committed_content_not_the_working_copy(self, repo, baseline):
        (repo / FILE).write_text("print('rewritten')\n")
        assert diffstate.get_baseline_file_content(
            "s1", str(repo / FILE), str(repo / "packages" / "app")) == OLD


@pytest.mark.parametrize("session_dir", ["", "packages/app"])
def test_rewrite_through_a_symlinked_path_does_not_re_flag(repo, linked, hook_env, session_dir):
    """The session runs in the real directory and the tool names the file
    through the symlink, as under /tmp on macOS."""
    cwd = repo / session_dir
    env = {**hook_env, "CLAUDE_PROJECT_DIR": str(cwd)}
    run_hook(ups_payload(cwd), env)

    _rc, stdout, _err = run_hook(write_payload(cwd, linked / FILE, OLD + "print('x')\n"), env)
    assert "additionalContext" not in stdout

    _rc, stdout, _err = run_hook(
        write_payload(cwd, linked / FILE, OLD + "import pickle\npickle.loads(data)\n"), env)
    assert "pickle" in stdout and "os.system" not in stdout


@pytest.mark.parametrize("session_dir", ["", "packages/app"])
def test_rewrite_does_not_re_flag_code_that_was_already_there(repo, hook_env, session_dir):
    """A full-file Write that keeps a pre-existing risky call is not a new
    finding, whether the session runs at the repo root or below it."""
    cwd = repo / session_dir
    env = {**hook_env, "CLAUDE_PROJECT_DIR": str(cwd)}
    run_hook(ups_payload(cwd), env)

    _rc, stdout, _err = run_hook(write_payload(cwd, repo / FILE, OLD + "print('x')\n"), env)
    assert "additionalContext" not in stdout

    _rc, stdout, _err = run_hook(
        write_payload(cwd, repo / FILE, OLD + "import pickle\npickle.loads(data)\n"), env)
    assert "additionalContext" in stdout
    assert "pickle" in stdout and "os.system" not in stdout
