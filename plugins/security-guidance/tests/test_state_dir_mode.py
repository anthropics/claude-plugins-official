"""The state dir holds the reviewer's venv, review logs and session state. It
is created, and kept, with access for its user alone, whatever the umask."""
import os
import stat
import sys

import pytest

import _base
import session_state

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes")


@pytest.fixture
def loose_umask():
    old = os.umask(0o002)
    yield
    os.umask(old)


def _mode(p):
    return stat.S_IMODE(os.stat(p).st_mode)


def test_new_state_dir_is_owner_only(tmp_path, monkeypatch, loose_umask):
    d = tmp_path / "state"
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(d))
    session_state.save_state("s1", {"k": 1})
    assert _mode(d) == 0o700


def test_existing_default_state_dir_is_narrowed(tmp_path, monkeypatch, loose_umask):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SECURITY_WARNINGS_STATE_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    d = tmp_path / ".claude" / "security"
    d.mkdir(parents=True)
    os.chmod(d, 0o775)
    _base.make_state_dir()
    assert _mode(d) == 0o700


def test_existing_folder_named_by_the_user_is_left_alone(tmp_path, monkeypatch):
    d = tmp_path / "team"
    d.mkdir()
    os.chmod(d, 0o2775)
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(d))
    _base.make_state_dir()
    assert _mode(d) == 0o2775


def test_a_link_at_the_default_state_dir_is_left_alone(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SECURITY_WARNINGS_STATE_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    shared = tmp_path / "shared"
    shared.mkdir()
    os.chmod(shared, 0o775)
    (tmp_path / ".claude").mkdir()
    os.symlink(shared, tmp_path / ".claude" / "security")
    _base.make_state_dir()
    assert _mode(shared) == 0o775


def test_other_folders_are_left_alone(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SECURITY_WARNINGS_STATE_DIR", raising=False)
    logs = tmp_path / "logs"
    logs.mkdir()
    os.chmod(logs, 0o755)
    _base.make_state_dir(str(logs))
    assert _mode(logs) == 0o755


def test_debug_log_in_the_working_directory_leaves_the_state_dir_alone(tmp_path, monkeypatch):
    d = tmp_path / "state"
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(d))
    with pytest.raises(OSError):
        _base.make_state_dir("")
    assert not d.exists()


@pytest.mark.parametrize("nofollow", [True, False])
def test_in_place_save_replaces_a_symlink(tmp_path, monkeypatch, nofollow):
    d = tmp_path / "state"
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(d))
    monkeypatch.setattr(session_state, "_RENAME_INTO_PLACE", False)
    if not nofollow:  # the Windows path: no O_NOFOLLOW
        monkeypatch.delattr(os, "O_NOFOLLOW")
    _base.make_state_dir()
    target = tmp_path / "elsewhere.txt"
    target.write_text("keep\n")
    state_file = session_state.get_state_file("s1")
    os.symlink(target, state_file)
    session_state.save_state("s1", {"k": 1})
    assert target.read_text() == "keep\n"
    assert not os.path.islink(state_file)
    assert session_state.load_state("s1").get("k") == 1


def test_in_place_save_creates_an_owner_only_file(tmp_path, monkeypatch, loose_umask):
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(session_state, "_RENAME_INTO_PLACE", False)
    session_state.save_state("s1", {"k": 1})
    assert _mode(session_state.get_state_file("s1")) == 0o600
    assert session_state.load_state("s1").get("k") == 1
