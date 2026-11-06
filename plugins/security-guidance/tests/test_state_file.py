import json
import os
import signal
import subprocess
import sys
import time

import pytest

from conftest import HOOKS_DIR, make_repo, metrics_of, run_hook, stop_payload, ups_payload

import session_state as ss


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    d = tmp_path / "state"
    d.mkdir()
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(d))
    monkeypatch.delenv("CLAUDE_CODE_REMOTE_SESSION_ID", raising=False)
    # Keep the legacy lock-file sweep and the debug log out of the real home.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(ss, "debug_log", lambda _msg: None)
    return d


def _seed(session_id="s1"):
    ss.with_locked_state(session_id, lambda st: st.update(
        baseline_sha="a" * 40, touched_paths=["x.py"],
        untracked_at_baseline={f"dir/file_{i:05d}.py": i for i in range(1500)}))


def _on_disk(state_dir, session_id="s1"):
    return json.loads((state_dir / f"security_warnings_state_{session_id}.json").read_text())


def _leftovers(state_dir):
    return sorted(p.name for p in state_dir.iterdir() if p.name.endswith(".tmp"))


_MARK_ONE = (
    "import sys; sys.path.insert(0, sys.argv[1]); import session_state as s; "
    "s.with_locked_state('s1', lambda st: st['shown_warnings'].append(sys.argv[2]))"
)

# A save that dies half-way through writing, as a hook killed on timeout does.
_KILLED_MID_SAVE = """
import json, os, signal, sys
sys.path.insert(0, sys.argv[1])
import session_state as s
def dump(obj, f, **kw):
    data = json.dumps(obj)
    f.write(data[:len(data) // 2]); f.flush()
    os.kill(os.getpid(), signal.SIGKILL)
s.json.dump = dump
s.with_locked_state('s1', lambda st: st['touched_paths'].append('y.py'))
"""


@pytest.mark.skipif(os.name == "nt", reason="rename into place is not used on Windows")
class TestSaveIsAtomic:
    def test_a_save_killed_part_way_keeps_the_previous_state(self, state_dir):
        _seed()
        r = subprocess.run([sys.executable, "-c", _KILLED_MID_SAVE, str(HOOKS_DIR)],
                           env=dict(os.environ))
        assert r.returncode == -signal.SIGKILL
        state = ss.load_state("s1")
        assert state["baseline_sha"] == "a" * 40
        assert state["touched_paths"] == ["x.py"]
        assert len(state["untracked_at_baseline"]) == 1500
        assert "state_resets" not in state

    def test_no_temporary_file_is_left_behind(self, state_dir):
        _seed()
        ss.with_locked_state("s1", lambda st: st["touched_paths"].append("y.py"))
        assert _on_disk(state_dir)["touched_paths"] == ["x.py", "y.py"]
        assert _leftovers(state_dir) == []

    def test_state_that_cannot_be_written_leaves_the_file_alone(self, state_dir):
        _seed()
        with pytest.raises(TypeError):
            ss.save_state("s1", {"shown_warnings": [], "bad": object()})
        assert _on_disk(state_dir)["baseline_sha"] == "a" * 40
        assert _leftovers(state_dir) == []

    def test_writes_in_place_where_the_directory_refuses_a_rename(self, state_dir, monkeypatch):
        _seed()

        def refuse(_src, _dst):
            raise PermissionError("rename refused")
        monkeypatch.setattr(ss.os, "replace", refuse)
        ss.with_locked_state("s1", lambda st: st["touched_paths"].append("y.py"))
        assert _on_disk(state_dir)["touched_paths"] == ["x.py", "y.py"]
        assert _leftovers(state_dir) == []

    def test_a_full_disk_leaves_the_previous_state(self, state_dir, monkeypatch):
        _seed()

        def full(_obj, f, **_kw):
            f.write('{"shown_warn')
            raise OSError(28, "No space left on device")
        monkeypatch.setattr(ss.json, "dump", full)
        ss.save_state("s1", {"shown_warnings": []})
        assert _on_disk(state_dir)["baseline_sha"] == "a" * 40
        assert _leftovers(state_dir) == []

    def test_in_place_where_rename_is_not_used(self, state_dir, monkeypatch):
        monkeypatch.setattr(ss, "_RENAME_INTO_PLACE", False)
        monkeypatch.setattr(ss.os, "replace", lambda *_a: pytest.fail("renamed"))
        _seed()
        assert _on_disk(state_dir)["touched_paths"] == ["x.py"]


@pytest.mark.skipif(ss.fcntl is None, reason="needs file locking")
def test_concurrent_writers_all_land(state_dir):
    """Eight hooks marking one warning each at the same moment keep all eight."""
    for _round in range(5):
        (state_dir / "security_warnings_state_s1.json").unlink(missing_ok=True)
        procs = [subprocess.Popen([sys.executable, "-c", _MARK_ONE, str(HOOKS_DIR), f"k{i}"],
                                  env=dict(os.environ)) for i in range(8)]
        assert [p.wait() for p in procs] == [0] * 8
        assert sorted(_on_disk(state_dir)["shown_warnings"]) == [f"k{i}" for i in range(8)]
    assert _leftovers(state_dir) == []


class TestStateLossIsCounted:
    def test_missing_file_is_a_fresh_state(self, state_dir):
        assert ss.load_state("s1") == {"shown_warnings": []}

    @pytest.mark.parametrize("content", [
        b"", b'{"baseline_sha": "abc", "touched_pa', b"42", b'{"baseline_sha": "\xff\xfe"}'])
    def test_unreadable_file_is_counted(self, state_dir, content):
        (state_dir / "security_warnings_state_s1.json").write_bytes(content)
        assert ss.load_state("s1") == {"shown_warnings": [], "state_resets": 1}

    def test_overwriting_another_hooks_save_is_counted_without_locking(
            self, state_dir, monkeypatch):
        monkeypatch.setattr(ss, "fcntl", None)
        _seed()
        assert "state_overwrites" not in _on_disk(state_dir)

        def slow_hook(state):
            # Another hook saves while this one is between its read and write.
            time.sleep(0.01)
            ss.save_state("s1", {**state, "touched_paths": ["x.py", "other.py"]})
            state["shown_warnings"].append("k")
        ss.with_locked_state("s1", slow_hook)
        after = _on_disk(state_dir)
        assert after["state_overwrites"] == 1
        assert after["touched_paths"] == ["x.py"]  # the other hook's save was lost

    def test_a_concurrent_save_of_the_same_state_is_not_counted(self, state_dir, monkeypatch):
        monkeypatch.setattr(ss, "fcntl", None)
        _seed()

        def reader(state):
            ss.save_state("s1", dict(state))  # another hook that only read
            return state["baseline_sha"]
        assert ss.with_locked_state("s1", reader) == "a" * 40
        assert "state_overwrites" not in _on_disk(state_dir)

    def test_stop_reports_the_counts_once(self, tmp_path, hook_env):
        repo = make_repo(tmp_path / "repo")
        hook_env = {k: v for k, v in hook_env.items() if k != "CLAUDE_CODE_REMOTE_SESSION_ID"}
        state_file = os.path.join(hook_env["SECURITY_WARNINGS_STATE_DIR"],
                                  "security_warnings_state_s1.json")
        run_hook(ups_payload(repo), hook_env)
        _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(stdout)
        assert "state_resets" not in m and "state_overwrites" not in m

        with open(state_file, "w") as f:
            f.write('{"baseline_sha": "abc", "touched_pa')
        run_hook(ups_payload(repo), hook_env)
        with open(state_file) as f:
            state = json.load(f)
        state["state_overwrites"] = 3
        with open(state_file, "w") as f:
            json.dump(state, f)
        _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(stdout)
        assert (m["state_resets"], m["state_overwrites"]) == (1, 3)

        _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(stdout)
        assert "state_resets" not in m and "state_overwrites" not in m


def test_cleanup_removes_old_temporary_files(state_dir):
    old = state_dir / "security_warnings_state_s1.json.a1b2c3.tmp"
    new = state_dir / "security_warnings_state_s2.json.a1b2c3.tmp"
    old.write_text("{}")
    new.write_text("{}")
    long_ago = time.time() - 31 * 24 * 60 * 60
    os.utime(old, (long_ago, long_ago))
    ss.cleanup_old_state_files()
    assert not old.exists() and new.exists()
