"""A commit still under review is not sent through a second review."""
import contextlib
import json
import os
import subprocess
import sys
import time

import pytest

from conftest import (
    HOOK_SCRIPT, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
)

import diffstate

_HOOKS_DIR = os.path.dirname(diffstate.__file__)

# Locks the way a review does on this platform: flock, or LockFileEx on Windows.
_HOLD = (
    "import os, sys, time\n"
    "sys.path.insert(0, sys.argv[3])\n"
    "import diffstate\n"
    "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
    "assert diffstate._flock_nb(fd, exclusive=True)\n"
    "print('held', flush=True)\n"
    "time.sleep(float(sys.argv[2]))\n"
)


@contextlib.contextmanager
def _held_by_another_review(repo, sha, seconds=60):
    """A marker on `sha` that a live process holds, as a running review does."""
    marker = repo / ".git" / f"sg-inflight-{sha}"
    p = subprocess.Popen(
        [sys.executable, "-c", _HOLD, str(marker), str(seconds), _HOOKS_DIR],
        stdout=subprocess.PIPE, text=True)
    try:
        assert p.stdout.readline().strip() == "held"
        yield marker
    finally:
        p.kill()
        p.wait()
        p.stdout.close()


@contextlib.contextmanager
def _hook_in_background(payload, env):
    p = subprocess.Popen(
        [sys.executable, str(HOOK_SCRIPT)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env,
    )
    try:
        p.stdin.write(json.dumps(payload))
        p.stdin.close()
        yield p
    finally:
        if p.poll() is None:
            p.kill()
        p.wait()
        p.stdout.close()


def _repo_with_remote(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")
    return repo, remote


def _markers(repo):
    return [n for n in os.listdir(repo / ".git") if n.startswith("sg-inflight-")]


def _wait_until(cond, what, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {what}")


def _reviews(stub_api):
    return [c for c in stub_api.calls if c.endswith("/v1/messages")]


def _commit_and_push(repo, remote):
    base = git(repo, "rev-parse", "HEAD").strip()
    sha, commit_out = commit_file(repo, "handlers.py", "def h(x):\n    return x\n")
    git(repo, "push", "-q", "origin", "main")
    push_out = f"To {remote}\n   {base[:7]}..{sha[:7]}  main -> main\n"
    return base, sha, commit_out, push_out


def test_push_right_after_commit_runs_one_review(tmp_path, hook_env, stub_api):
    repo, remote = _repo_with_remote(tmp_path)
    base, sha, commit_out, push_out = _commit_and_push(repo, remote)
    stub_api.delay = 6
    with _hook_in_background(bash_payload(repo, "git commit -m change", commit_out),
                             hook_env) as commit:
        _wait_until(lambda: _markers(repo), "the commit review's marker")
        rc, so, _ = run_hook(bash_payload(repo, "git push origin main", push_out), hook_env)
        commit.wait(timeout=60)

    m = metrics_of(so)
    assert rc == 0 and m["push_sweep"] is True
    assert m["pushed"] == 1 and m["unreviewed"] == 0
    assert m.get("inflight_wait_s", 0) >= 1
    assert len(_reviews(stub_api)) == 1
    assert sha in diffstate._load_reviewed_shas(str(repo))
    assert _markers(repo) == []


def test_push_reviews_commit_whose_review_died(tmp_path, hook_env, stub_api):
    repo, remote = _repo_with_remote(tmp_path)
    base, sha, _, push_out = _commit_and_push(repo, remote)
    with _held_by_another_review(repo, sha):
        pass  # killed: its marker file stays, its lock does not
    assert _markers(repo) == [f"sg-inflight-{sha}"]
    rc, so, _ = run_hook(bash_payload(repo, "git push origin main", push_out), hook_env)

    m = metrics_of(so)
    assert m["unreviewed"] == 1 and "inflight_wait_s" not in m
    assert len(_reviews(stub_api)) == 1
    assert _markers(repo) == []


def test_push_reviews_commit_whose_review_ended_without_a_verdict(tmp_path, hook_env, stub_api):
    repo, remote = _repo_with_remote(tmp_path)
    base, sha, _, push_out = _commit_and_push(repo, remote)
    with _held_by_another_review(repo, sha, seconds=3):
        rc, so, _ = run_hook(bash_payload(repo, "git push origin main", push_out), hook_env)

    m = metrics_of(so)
    assert m["unreviewed"] == 1
    assert m["files_reviewed"] == 1 and len(_reviews(stub_api)) == 1
    assert sha in diffstate._load_reviewed_shas(str(repo))


def test_push_stops_waiting_after_the_limit(tmp_path, hook_env, stub_api):
    repo, remote = _repo_with_remote(tmp_path)
    base, sha, _, push_out = _commit_and_push(repo, remote)
    env = {**hook_env, "SG_INFLIGHT_WAIT_S": "2"}
    with _held_by_another_review(repo, sha):
        rc, so, _ = run_hook(bash_payload(repo, "git push origin main", push_out), env)

    m = metrics_of(so)
    assert m["unreviewed"] == 1 and m["inflight_wait_s"] >= 2
    assert len(_reviews(stub_api)) == 1


def test_push_does_not_wait_when_an_earlier_commit_needs_review_anyway(tmp_path, hook_env, stub_api):
    repo, remote = _repo_with_remote(tmp_path)
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_file(repo, "outside.py", "def o(x):\n    return x\n")
    sha, _ = commit_file(repo, "handlers.py", "def h(x):\n    return x\n")
    git(repo, "push", "-q", "origin", "main")
    push_out = f"To {remote}\n   {base[:7]}..{sha[:7]}  main -> main\n"
    with _held_by_another_review(repo, sha):
        rc, so, _ = run_hook(bash_payload(repo, "git push origin main", push_out), hook_env)

    m = metrics_of(so)
    assert m["pushed"] == 2 and m["unreviewed"] == 2 and "inflight_wait_s" not in m
    assert m["files_reviewed"] == 2


def test_push_does_not_record_the_range_when_head_moves_during_the_wait(tmp_path, hook_env, stub_api):
    repo, remote = _repo_with_remote(tmp_path)
    base, sha, _, push_out = _commit_and_push(repo, remote)
    env = {**hook_env, "SG_INFLIGHT_WAIT_S": "10"}
    with _held_by_another_review(repo, sha):
        with _hook_in_background(bash_payload(repo, "git push origin main", push_out),
                                 env) as push:
            time.sleep(5)
            git(repo, "checkout", "-q", "-b", "elsewhere", base)
            so = push.stdout.read()
            push.wait(timeout=60)

    m = metrics_of(so)
    assert m["skip_reason"] == 44 and m.get("inflight_wait_s", 0) >= 1
    assert _reviews(stub_api) == []
    assert sha not in diffstate._load_reviewed_shas(str(repo))


def test_next_quiet_commit_leaves_a_running_review_its_commit(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    commit_file(repo, "a.py", "def a(x):\n    return x\n")
    stub_api.delay = 6
    with _hook_in_background(bash_payload(repo, "git commit -q -m a"), hook_env) as first:
        _wait_until(lambda: _markers(repo), "the first review's marker")
        commit_file(repo, "b.py", "def b(x):\n    return x\n")
        rc, so, _ = run_hook(bash_payload(repo, "git commit -q -m b"), hook_env)
        first.wait(timeout=60)

    m = metrics_of(so)
    assert m["sha_via_reflog"] is True and m["reflog_shas_n"] == 1
    assert m["files_reviewed"] == 1
    assert _markers(repo) == []


def test_marker_is_not_taken_from_a_live_review(tmp_path):
    repo = make_repo(tmp_path / "repo")
    sha = git(repo, "rev-parse", "HEAD").strip()
    with _held_by_another_review(repo, sha) as marker:
        diffstate._mark_inflight(str(repo), [sha])
        assert diffstate._inflight_held == {}
        assert diffstate._load_inflight_shas(str(repo), [sha]) == {sha}
    assert diffstate._load_inflight_shas(str(repo), [sha]) == set()
    assert marker.exists()  # fresh leftovers stay; old ones are removed
    old = time.time() - diffstate._INFLIGHT_GC_AGE_S - 5
    os.utime(marker, (old, old))
    diffstate._mark_inflight(str(repo), [])
    assert not marker.exists()


def test_no_marker_is_left_where_files_cannot_be_locked(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo")
    sha = git(repo, "rev-parse", "HEAD").strip()

    def no_locks(fd, exclusive):
        raise OSError(37, "No locks available")
    monkeypatch.setattr(diffstate, "_flock_nb", no_locks)
    diffstate._mark_inflight(str(repo), [sha])
    assert _markers(repo) == [] and diffstate._inflight_held == {}
    (repo / ".git" / f"sg-inflight-{sha}").write_text("")
    assert diffstate._load_inflight_shas(str(repo), [sha]) == set()


def test_own_marker_is_held_until_released(tmp_path):
    repo = make_repo(tmp_path / "repo")
    sha = git(repo, "rev-parse", "HEAD").strip()
    diffstate._mark_inflight(str(repo), [sha, "not-a-sha"])
    marker = repo / ".git" / f"sg-inflight-{sha}"
    try:
        assert _markers(repo) == [marker.name]
        assert diffstate._load_inflight_shas(str(repo), [sha]) == set()
        probe = (
            "import sys; sys.path.insert(0, sys.argv[1]); import diffstate; "
            "print(sorted(diffstate._load_inflight_shas(sys.argv[2], [sys.argv[3]])))"
        )
        seen = subprocess.run(
            [sys.executable, "-c", probe, _HOOKS_DIR, str(repo), sha],
            capture_output=True, text=True).stdout.strip()
        assert seen == str([sha])
        reviewed, waited = diffstate._reviewed_after_inflight(str(repo), [sha], 5)
        assert reviewed == set() and waited == 0.0
    finally:
        diffstate._release_inflight()
    assert not marker.exists()


def test_marker_is_closed_before_it_is_deleted_where_open_files_cannot_be(tmp_path, monkeypatch):
    # The order used on Windows, where deleting an open file is refused.
    repo = make_repo(tmp_path / "repo")
    sha = git(repo, "rev-parse", "HEAD").strip()
    marker = repo / ".git" / f"sg-inflight-{sha}"
    monkeypatch.setattr(diffstate, "_UNLINK_BEFORE_CLOSE", False)
    open_at_delete, refusals = [], [2]

    def delete_like_windows(p, fd):
        try:
            os.fstat(fd)
            open_at_delete.append(True)
        except OSError:
            open_at_delete.append(False)
        if refusals[0]:
            # Another review asking about the marker has it open just now.
            refusals[0] -= 1
            raise PermissionError(13, "The process cannot access the file")
        real_unlink(p)

    real_unlink = os.unlink
    try:
        diffstate._mark_inflight(str(repo), [sha])
        (fd,) = diffstate._inflight_held.values()
        monkeypatch.setattr(diffstate.os, "unlink", lambda p: delete_like_windows(p, fd))
        diffstate._release_inflight()
    finally:
        monkeypatch.setattr(diffstate.os, "unlink", real_unlink)
        diffstate._release_inflight()
    assert open_at_delete == [False, False, False] and not marker.exists()

    # An old leftover goes the same way.
    marker.write_text("")
    old = time.time() - diffstate._INFLIGHT_GC_AGE_S - 5
    os.utime(marker, (old, old))
    diffstate._mark_inflight(str(repo), [])
    assert not marker.exists()


def test_no_markers_in_a_python_without_file_locks(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("Windows locks with LockFileEx")
    repo = make_repo(tmp_path / "repo")
    sha = git(repo, "rev-parse", "HEAD").strip()
    monkeypatch.setitem(sys.modules, "fcntl", None)
    diffstate._mark_inflight(str(repo), [sha])
    assert _markers(repo) == [] and diffstate._inflight_held == {}
    (repo / ".git" / f"sg-inflight-{sha}").write_text("")
    assert diffstate._load_inflight_shas(str(repo), [sha]) == set()


def test_one_marker_that_cannot_be_claimed_does_not_stop_the_others(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo")
    first = git(repo, "rev-parse", "HEAD").strip()
    second, _ = commit_file(repo, "b.py", "b = 1\n")
    third, _ = commit_file(repo, "c.py", "c = 1\n")
    # Cannot be opened at all.
    (repo / ".git" / f"sg-inflight-{first}").mkdir()
    # Its last holder deletes it between this review's open and its lock.
    real_flock_nb = diffstate._flock_nb

    def holder_ends_first(fd, exclusive):
        taken = real_flock_nb(fd, exclusive)
        gone = repo / ".git" / f"sg-inflight-{second}"
        if gone.exists() and os.name != "nt":
            gone.unlink()
        return taken
    monkeypatch.setattr(diffstate, "_flock_nb", holder_ends_first)
    try:
        diffstate._mark_inflight(str(repo), [first, second, third])
        held = [os.path.basename(p) for p in diffstate._inflight_held]
        assert f"sg-inflight-{third}" in held and f"sg-inflight-{first}" not in held
        if os.name != "nt":
            assert held == [f"sg-inflight-{third}"]
    finally:
        diffstate._release_inflight()


class _FakeKernel32:
    """LockFileEx as kernel32 has it, for the code path only Windows runs."""

    def __init__(self):
        self.calls, self.result, self.error = [], 1, 0

        def LockFileEx(handle, flags, reserved, low, high, overlapped):
            ov = overlapped._obj
            self.calls.append((handle, flags, low, high, ov.Offset, ov.OffsetHigh))
            return self.result
        self.LockFileEx = LockFileEx


@pytest.fixture
def kernel32(monkeypatch):
    import ctypes
    import types
    fake = _FakeKernel32()
    monkeypatch.setattr(ctypes, "WinDLL", lambda name, use_last_error=False: fake, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: fake.error, raising=False)
    monkeypatch.setitem(sys.modules, "msvcrt",
                        types.SimpleNamespace(get_osfhandle=lambda fd: 1000 + fd))
    monkeypatch.setattr(diffstate, "_win_lock_file_ex", None)
    return fake


def test_windows_lock_call(kernel32):
    assert diffstate._win_lock_nb(7, exclusive=True) is True
    assert diffstate._win_lock_nb(7, exclusive=False) is True
    # Fail-immediately, exclusive or shared, one byte far past the end of the
    # file so that reading the marker is never refused.
    assert kernel32.calls == [(1007, 0x3, 1, 0, 0, 0x7FFFFFFF), (1007, 0x1, 1, 0, 0, 0x7FFFFFFF)]
    kernel32.result, kernel32.error = 0, 33
    assert diffstate._win_lock_nb(7, exclusive=True) is False
    for other_error in (5, 6, 997):
        kernel32.error = other_error
        with pytest.raises(OSError):
            diffstate._win_lock_nb(7, exclusive=True)


def test_windows_lock_is_off_where_the_call_is_missing(monkeypatch):
    import ctypes
    monkeypatch.delattr(ctypes, "WinDLL", raising=False)
    monkeypatch.setattr(diffstate, "_win_lock_file_ex", None)
    with pytest.raises(OSError):
        diffstate._win_lock_nb(7, exclusive=True)
