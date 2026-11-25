"""The records and markers kept in the git directory are the plugin's own
regular files; anything else by one of their names is neither read nor written."""
import os
import stat
import subprocess
import sys
import threading
import time

import pytest

from conftest import (
    GIT_ENV, STUB_VULN, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
)

import diffstate

DIFFS, SHAS = "sg-reviewed-diffs", "sg-reviewed-shas"
DIFF = [("handlers.py", "@@ -0,0 +1,2 @@\n+def h(x):\n+    return x")]
OTHER = "".join(f"line {i}\n" for i in range(600)) + "same\nsame\n"
SOURCE = "import os\ndef f(u):\n    os.system(u)\n"

no_fifo = pytest.mark.skipif(sys.platform == "win32", reason="no mkfifo")
BOTH = pytest.mark.parametrize("name", [DIFFS, SHAS])


@pytest.fixture(autouse=True)
def _claude_code_output(monkeypatch):
    # diffstate reads the output mode from the test runner's environment.
    monkeypatch.setattr(diffstate, "portable_output", lambda: False)


@pytest.fixture(params=["flag", "no flag"])
def every_platform(request, monkeypatch):
    """Once as here, once as where os has no O_NOFOLLOW (Windows)."""
    if request.param == "no flag":
        monkeypatch.setattr(diffstate, "_NO_FOLLOW", 0)


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})


@pytest.fixture
def other(tmp_path):
    p = tmp_path / "other.txt"
    p.write_text(OTHER)
    os.utime(p, (time.time() - 600,) * 2)
    return p


def _symlink(link, target):
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError) as e:
        pytest.skip(f"cannot make a link here: {e}")


def _hard_link(link, target):
    try:
        os.link(target, link)
    except (OSError, NotImplementedError) as e:
        pytest.skip(f"cannot make a link here: {e}")


LINKS = pytest.mark.parametrize("link", [_symlink, _hard_link], ids=["symlink", "hard link"])


def _within(seconds, fn, *args):
    """fn(*args), failing the test rather than hanging the run if it waits."""
    got = []
    t = threading.Thread(target=lambda: got.append(fn(*args)), daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), "still waiting"
    return got[0]


def _head(repo):
    return git(repo, "rev-parse", "HEAD").strip()


def _write(repo, name):
    """What a review does with the record `name`."""
    if name == DIFFS:
        token, _ = diffstate._diff_review_started(str(repo), DIFF)
        diffstate._diff_review_done(token)
    else:
        diffstate._append_reviewed_shas(str(repo), [_head(repo)])


def _is_plain(path):
    st = os.lstat(path)
    return stat.S_ISREG(st.st_mode) and st.st_nlink == 1


def _unchanged(other):
    return other.read_text() == OTHER and time.time() - other.stat().st_mtime > 500


@pytest.fixture
def released():
    yield
    diffstate._release_inflight()


# ── the two records ──────────────────────────────────────────────────────

@BOTH
def test_a_record_is_made_and_added_to(repo, name):
    _write(repo, name)
    first = (repo / ".git" / name).read_bytes()
    commit_file(repo, "b.py", "x = 1\n")
    _write(repo, name)
    now = (repo / ".git" / name).read_bytes()
    assert first and now.startswith(first) and len(now) > len(first)
    assert now.endswith(b"\n")
    if name == DIFFS:
        assert b"\r" not in now  # written as bytes, on every platform


@pytest.mark.skipif(os.name == "nt", reason="POSIX modes")
@BOTH
def test_a_new_record_has_the_mode_open_gives(repo, name):
    old = os.umask(0o027)
    try:
        _write(repo, name)
    finally:
        os.umask(old)
    assert stat.S_IMODE(os.stat(repo / ".git" / name).st_mode) == 0o640


@BOTH
def test_a_repository_reached_through_a_link_keeps_its_records(repo, tmp_path, name, every_platform):
    try:
        os.symlink(repo, tmp_path / "alias", target_is_directory=True)
    except (OSError, NotImplementedError) as e:
        pytest.skip(f"cannot make a link here: {e}")
    _write(tmp_path / "alias", name)
    first = (repo / ".git" / name).read_bytes()
    commit_file(repo, "b.py", "x = 1\n")
    _write(tmp_path / "alias", name)
    assert first and (repo / ".git" / name).read_bytes().startswith(first)


@LINKS
@BOTH
def test_a_link_is_replaced_not_followed(repo, other, name, link, every_platform):
    link(repo / ".git" / name, other)
    _write(repo, name)
    assert _unchanged(other)
    assert _is_plain(repo / ".git" / name)
    assert (repo / ".git" / name).read_text().count("\n") == (2 if name == DIFFS else 1)


def test_a_link_put_there_while_the_review_runs_is_replaced(repo, other):
    token, _ = diffstate._diff_review_started(str(repo), DIFF)
    (repo / ".git" / DIFFS).unlink()
    _symlink(repo / ".git" / DIFFS, other)
    diffstate._diff_review_done(token)
    assert _unchanged(other) and _is_plain(repo / ".git" / DIFFS)


@BOTH
def test_a_link_to_nothing_makes_nothing(repo, tmp_path, name, every_platform):
    _symlink(repo / ".git" / name, tmp_path / "absent.txt")
    _write(repo, name)
    assert not os.path.lexists(tmp_path / "absent.txt")
    assert _is_plain(repo / ".git" / name)


def test_a_link_through_a_link_is_replaced(repo, other, every_platform):
    _symlink(repo / "hop", other)
    _symlink(repo / ".git" / DIFFS, os.path.join("..", "hop"))
    _write(repo, DIFFS)
    assert _unchanged(other) and _is_plain(repo / ".git" / DIFFS)


@no_fifo
@BOTH
def test_a_pipe_is_replaced_without_waiting(repo, name):
    os.mkfifo(repo / ".git" / name)
    _within(10, _write, repo, name)
    assert _is_plain(repo / ".git" / name)


@BOTH
def test_a_file_too_large_to_be_a_record_is_replaced(repo, name, monkeypatch):
    monkeypatch.setattr(diffstate, "_OWN_FILE_MAX_BYTES", 1000)
    (repo / ".git" / name).write_bytes(b"x" * 1001)
    _write(repo, name)
    assert b"x" not in (repo / ".git" / name).read_bytes()


@BOTH
def test_a_folder_is_left_and_nothing_is_raised(repo, name):
    (repo / ".git" / name).mkdir()
    _write(repo, name)
    assert (repo / ".git" / name).is_dir()


def test_a_diff_that_cannot_be_noted_is_counted_as_an_error(repo):
    (repo / ".git" / DIFFS).mkdir()
    assert diffstate._diff_review_started(str(repo), DIFF) == (
        None, {"diff_seen": diffstate.DIFF_SEEN_ERROR})


@LINKS
def test_reviewed_commits_are_not_read_through_a_link(repo, tmp_path, link, every_platform):
    listed = tmp_path / "listed.txt"
    listed.write_text(_head(repo) + "\t1\t1\t0\n")
    link(repo / ".git" / SHAS, listed)
    assert diffstate._load_reviewed_shas(str(repo)) == set()
    assert os.path.lexists(repo / ".git" / SHAS), "reading removes nothing"


@no_fifo
def test_reviewed_commits_are_not_read_from_a_pipe(repo):
    os.mkfifo(repo / ".git" / SHAS)
    assert _within(10, diffstate._load_reviewed_shas, str(repo)) == set()


def test_no_more_than_a_record_can_hold_is_read(repo, monkeypatch):
    """The size is looked at when the file is opened; it can grow after that."""
    monkeypatch.setattr(diffstate, "_OWN_FILE_MAX_BYTES", 100)
    (repo / ".git" / SHAS).write_text("")
    real_open = diffstate._open_own_file

    def open_then_grow(path, flags, mode=0o666):
        fd = real_open(path, flags, mode)
        with open(path, "a") as f:
            f.write("x" * 79 + "\n" + _head(repo) + "\t1\t1\t0\n")
        return fd

    monkeypatch.setattr(diffstate, "_open_own_file", open_then_grow)
    assert diffstate._load_reviewed_shas(str(repo)) == set()


def test_bytes_that_are_no_text_cost_only_their_own_row(repo):
    record = repo / ".git" / SHAS
    record.write_bytes(b"\xff\xfe\x81\n" + ("0" * 40).encode() + b"\t1\t1\t0\n")
    assert diffstate._load_reviewed_shas(str(repo)) == {"0" * 40}
    diffstate._append_reviewed_shas(str(repo), [_head(repo)])
    assert diffstate._load_reviewed_shas(str(repo)) == {"0" * 40, _head(repo)}


# Locks the way a review does on this platform.
_HOLD = (
    "import os, sys, time\n"
    "sys.path.insert(0, sys.argv[2])\n"
    "import diffstate\n"
    "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
    "assert diffstate._flock_nb(fd, exclusive=True)\n"
    "print('held', flush=True)\n"
    "time.sleep(60)\n"
)


def test_a_lock_that_stays_held_does_not_hold_the_row_back(repo):
    holder = subprocess.Popen(
        [sys.executable, "-c", _HOLD, str(repo / ".git" / SHAS), os.path.dirname(diffstate.__file__)],
        stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        _within(10, diffstate._append_reviewed_shas, str(repo), [_head(repo)])
    finally:
        holder.kill()
        holder.wait()
        holder.stdout.close()
    assert _head(repo) in diffstate._load_reviewed_shas(str(repo))


@pytest.mark.skipif(os.name == "nt", reason="no flock; rows are only appended there")
def test_the_row_is_in_the_file_before_the_lock_is_released(repo, monkeypatch):
    import fcntl
    real_flock, at_unlock = fcntl.flock, []

    def flock(fd, op):
        if op == fcntl.LOCK_UN:
            at_unlock.append((repo / ".git" / SHAS).read_text())
        return real_flock(fd, op)

    monkeypatch.setattr(fcntl, "flock", flock)
    diffstate._append_reviewed_shas(str(repo), [_head(repo)])
    assert at_unlock and _head(repo) in at_unlock[0]


# ── a name that changes between the first look and the open ──────────────

def _swap_after_the_first_look(monkeypatch, path, swap):
    real_lstat = os.lstat
    done = []

    def lstat_then_swap(p, *a, **k):
        st = real_lstat(p, *a, **k)
        if os.fspath(p) == str(path) and not done:
            done.append(1)
            path.unlink()
            swap(path)
        return st

    monkeypatch.setattr(diffstate.os, "lstat", lstat_then_swap)
    return done


SWAPS = pytest.mark.parametrize("kind", ["symlink", "hard link", pytest.param("pipe", marks=no_fifo)])


@SWAPS
@BOTH
def test_the_open_file_is_looked_at_too(repo, other, name, kind, monkeypatch, every_platform):
    record = repo / ".git" / name
    record.write_text("")
    swap = {"symlink": lambda p: _symlink(p, other),
            "hard link": lambda p: _hard_link(p, other),
            "pipe": lambda p: os.mkfifo(p)}[kind]
    swapped = _swap_after_the_first_look(monkeypatch, record, swap)
    _within(10, _write, repo, name)
    monkeypatch.undo()
    assert swapped and _unchanged(other)


def _appear_after_the_first_look(monkeypatch, path, put):
    real_lstat = os.lstat
    done = []

    def lstat_then_put(p, *a, **k):
        try:
            return real_lstat(p, *a, **k)
        except FileNotFoundError:
            if os.fspath(p) == str(path) and not done:
                done.append(1)
                put(path)
            raise

    monkeypatch.setattr(diffstate.os, "lstat", lstat_then_put)
    return done


@BOTH
def test_a_link_that_appears_where_nothing_was_is_not_written_through(
        repo, other, name, monkeypatch, every_platform):
    appeared = _appear_after_the_first_look(
        monkeypatch, repo / ".git" / name, lambda p: _symlink(p, other))
    _write(repo, name)
    monkeypatch.undo()
    assert appeared and _unchanged(other)


@BOTH
def test_a_link_that_is_a_hard_link_by_the_second_look_is_not_written_through(
        repo, other, name, monkeypatch, every_platform):
    record = repo / ".git" / name
    real_lstat = os.lstat
    looks = []

    def lstat_with_changes(p, *a, **k):
        if os.fspath(p) == str(record):
            looks.append(1)
            if len(looks) == 2 and os.path.islink(record):
                record.unlink()
                _hard_link(record, other)
        try:
            return real_lstat(p, *a, **k)
        except FileNotFoundError:
            if os.fspath(p) == str(record) and len(looks) == 1:
                _symlink(record, other)
            raise

    monkeypatch.setattr(diffstate.os, "lstat", lstat_with_changes)
    _write(repo, name)
    monkeypatch.undo()
    assert looks and _unchanged(other)


@BOTH
def test_a_link_to_nothing_that_appears_where_nothing_was_gets_no_row(
        repo, tmp_path, name, monkeypatch, every_platform):
    target = tmp_path / "absent.txt"
    told_not_to_follow = diffstate._NO_FOLLOW
    appeared = _appear_after_the_first_look(
        monkeypatch, repo / ".git" / name, lambda p: _symlink(p, target))
    _write(repo, name)
    monkeypatch.undo()
    assert appeared
    if told_not_to_follow:
        assert not os.path.lexists(target)
    else:
        assert not target.exists() or target.read_bytes() == b""


@no_fifo
def test_a_read_does_not_wait_for_a_name_that_turned_into_a_pipe(repo, monkeypatch):
    record = repo / ".git" / SHAS
    record.write_text("")
    swapped = _swap_after_the_first_look(monkeypatch, record, lambda p: os.mkfifo(p))
    assert _within(10, diffstate._load_reviewed_shas, str(repo)) == set()
    assert swapped


def test_a_name_taken_again_after_the_removal_is_left(
        repo, other, tmp_path, monkeypatch, every_platform):
    """The new file is made only if the name is still free."""
    record = repo / ".git" / DIFFS
    _symlink(record, tmp_path / "absent.txt")
    real_unlink = os.unlink

    def unlink_then_take(p, *a, **k):
        real_unlink(p, *a, **k)
        if os.fspath(p) == str(record):
            os.symlink(other, record)

    monkeypatch.setattr(diffstate.os, "unlink", unlink_then_take)
    assert diffstate._diff_review_started(str(repo), DIFF)[1] == {
        "diff_seen": diffstate.DIFF_SEEN_ERROR}
    monkeypatch.undo()
    assert _unchanged(other)


def test_a_replacement_another_hook_got_to_first_still_makes_the_record(repo, tmp_path, monkeypatch):
    """Two hooks can find the same stray name and both remove it."""
    record = repo / ".git" / DIFFS
    _symlink(record, tmp_path / "absent.txt")
    real_unlink = os.unlink

    def unlink_twice(p, *a, **k):
        if os.fspath(p) == str(record):
            real_unlink(p, *a, **k)
        real_unlink(p, *a, **k)

    monkeypatch.setattr(diffstate.os, "unlink", unlink_twice)
    assert "diff_seen" in diffstate._diff_review_started(str(repo), DIFF)[1]
    monkeypatch.undo()
    assert _is_plain(record) and record.read_text().count("\n") == 1


@pytest.mark.skipif(os.name == "nt", reason="an open file cannot be removed there")
def test_a_marker_its_holder_removes_during_the_look_is_claimed_anew(repo, monkeypatch, released):
    """A review ending as the next one starts is not a stray file."""
    marker = _marker(repo)
    marker.write_text("")
    holder = os.open(marker, os.O_RDONLY)  # keeps its inode from being reused
    real_lstat = os.lstat
    done = []

    def lstat_then_holder_ends(p, *a, **k):
        st = real_lstat(p, *a, **k)
        if os.fspath(p) == str(marker) and not done:
            done.append(1)
            marker.unlink()
        return st

    monkeypatch.setattr(diffstate, "_sweep_inflight", lambda gd: None)
    monkeypatch.setattr(diffstate.os, "lstat", lstat_then_holder_ends)
    try:
        diffstate._mark_inflight(str(repo), [_head(repo)])
    finally:
        monkeypatch.undo()
        os.close(holder)
    assert done and str(marker) in diffstate._inflight_held


# ── the markers ──────────────────────────────────────────────────────────

def _marker(repo):
    return repo / ".git" / f"sg-inflight-{_head(repo)}"


def test_a_marker_is_made_held_and_removed(repo, released):
    diffstate._mark_inflight(str(repo), [_head(repo)])
    assert _is_plain(_marker(repo)) and str(_marker(repo)) in diffstate._inflight_held
    diffstate._release_inflight()
    assert not os.path.lexists(_marker(repo))


@LINKS
def test_a_marker_link_is_replaced_not_followed(repo, other, link, released, every_platform):
    link(_marker(repo), other)
    diffstate._mark_inflight(str(repo), [_head(repo)])
    assert _unchanged(other)
    assert _is_plain(_marker(repo)) and str(_marker(repo)) in diffstate._inflight_held
    diffstate._release_inflight()
    assert other.exists()


def test_a_marker_link_to_nothing_makes_nothing(repo, tmp_path, released, every_platform):
    _symlink(_marker(repo), tmp_path / "absent.txt")
    diffstate._mark_inflight(str(repo), [_head(repo)])
    assert not os.path.lexists(tmp_path / "absent.txt")


@no_fifo
def test_asking_about_a_marker_that_is_a_pipe_does_not_wait(repo):
    os.mkfifo(_marker(repo))
    assert _within(10, diffstate._load_inflight_shas, str(repo), [_head(repo)]) == set()


def test_an_old_link_among_the_markers_is_removed_unopened(repo, other, released):
    link = repo / ".git" / "sg-inflight-old"
    _symlink(link, other)
    try:
        os.utime(link, (1, 1), follow_symlinks=False)
    except NotImplementedError:
        pytest.skip("a link's own time cannot be set here")
    diffstate._mark_inflight(str(repo), [_head(repo)])
    assert not os.path.lexists(link) and _unchanged(other)


@pytest.mark.skipif(os.utime not in os.supports_fd, reason="time stamps go by name here")
def test_the_time_stamp_goes_to_the_marker_that_was_opened(repo, other, released, monkeypatch):
    marker = _marker(repo)
    real_stat = os.stat

    def stat_then_swap(p, *a, **k):
        st = real_stat(p, *a, **k)
        if isinstance(p, str) and p == str(marker):
            marker.unlink()
            os.symlink(other, marker)
        return st

    monkeypatch.setattr(diffstate.os, "stat", stat_then_swap)
    diffstate._mark_inflight(str(repo), [_head(repo)])
    monkeypatch.undo()
    assert _unchanged(other)


def test_an_old_marker_nobody_holds_is_still_swept(repo, released):
    old = repo / ".git" / ("sg-inflight-" + "0" * 40)
    old.write_text("")
    os.utime(old, (1, 1))
    diffstate._mark_inflight(str(repo), [_head(repo)])
    assert not old.exists()


# ── through the hook ─────────────────────────────────────────────────────

def _with_remote(repo, tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")


def _push_event(repo):
    pushed = subprocess.run(["git", "push", "origin", "main"], cwd=repo, capture_output=True,
                            text=True, env={**os.environ, **GIT_ENV})
    assert pushed.returncode == 0, pushed.stderr
    return bash_payload(repo, "git push origin main", pushed.stdout, pushed.stderr)


def _others(repo, tmp_path):
    """A link at each record's name, each to a file of its own."""
    others = []
    for name in (DIFFS, SHAS):
        others.append(tmp_path / (name + ".txt"))
        others[-1].write_text(OTHER)
        _symlink(repo / ".git" / name, others[-1])
    return others


def test_commit_review_with_links_in_place_of_all_three(repo, tmp_path, hook_env, stub_api):
    others = _others(repo, tmp_path)
    sha, out = commit_file(repo, "app.py", SOURCE)
    _symlink(repo / ".git" / f"sg-inflight-{sha}", tmp_path / "absent.txt")
    rc, stdout, _ = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
    assert rc == 0 and stub_api.calls, "the review still runs"
    assert metrics_of(stdout)["diff_seen"] == diffstate.DIFF_SEEN_NO
    assert all(p.read_text() == OTHER for p in others)
    assert not os.path.lexists(tmp_path / "absent.txt")
    assert sha in diffstate._load_reviewed_shas(str(repo))


def test_commit_review_with_folders_in_place_of_all_three(repo, hook_env, stub_api):
    sha, out = commit_file(repo, "app.py", SOURCE)
    for name in (DIFFS, SHAS, f"sg-inflight-{sha}"):
        (repo / ".git" / name).mkdir()
    rc, stdout, _ = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
    assert rc == 0 and stub_api.calls, "the review still runs"
    assert metrics_of(stdout)["diff_seen"] == diffstate.DIFF_SEEN_ERROR


def test_push_review_with_links_in_place_of_the_records(repo, tmp_path, hook_env, stub_api):
    _with_remote(repo, tmp_path)
    others = _others(repo, tmp_path)
    sha, _ = commit_file(repo, "app.py", SOURCE)
    rc, _, _ = run_hook(_push_event(repo), hook_env)
    assert rc == 0 and stub_api.calls, "the review still runs"
    assert all(p.read_text() == OTHER for p in others)
    assert sha in diffstate._load_reviewed_shas(str(repo))


@no_fifo
def test_push_review_does_not_wait_on_pipes(repo, tmp_path, hook_env, stub_api):
    _with_remote(repo, tmp_path)
    sha, _ = commit_file(repo, "app.py", SOURCE)
    os.mkfifo(repo / ".git" / SHAS)
    os.mkfifo(repo / ".git" / f"sg-inflight-{sha}")
    rc, _, _ = run_hook(_push_event(repo), hook_env)  # run_hook gives up after 120 s
    assert rc == 0 and stub_api.calls, "the review still runs"
    assert sha in diffstate._load_reviewed_shas(str(repo))


def test_push_review_runs_whatever_bytes_the_record_holds(repo, tmp_path, hook_env, stub_api):
    _with_remote(repo, tmp_path)
    sha, _ = commit_file(repo, "app.py", SOURCE)
    (repo / ".git" / SHAS).write_bytes(b"\xff\xfe\x81\n")
    rc, _, _ = run_hook(_push_event(repo), hook_env)
    assert rc == 0 and stub_api.calls, "the review still runs"
    assert sha in diffstate._load_reviewed_shas(str(repo))


def test_findings_go_out_while_the_record_is_locked(repo, hook_env, stub_api):
    stub_api.vulns = [STUB_VULN]
    sha, out = commit_file(repo, "app.py", SOURCE)
    holder = subprocess.Popen(
        [sys.executable, "-c", _HOLD, str(repo / ".git" / SHAS), os.path.dirname(diffstate.__file__)],
        stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        rc, _, stderr = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
    finally:
        holder.kill()
        holder.wait()
        holder.stdout.close()
    assert rc == 2 and "command_injection" in stderr
