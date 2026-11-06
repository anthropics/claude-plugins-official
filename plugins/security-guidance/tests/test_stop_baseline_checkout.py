"""The turn baseline belongs to the checkout the prompt hook captured it in.
A Stop review in another checkout (the session entered a worktree, or edited
another repo) does not use it: commits count from that checkout's own HEAD at
the time of the prompt, files are diffed against HEAD, and uncommitted files
last written before the prompt are left out. Stop rows carry `bl_origin`,
saying which case the row was."""
import json
import os
import shutil
import time

import pytest

from conftest import (
    STUB_VULN, VULN_PY, edit_payload, git, make_repo, metrics_of, run_hook,
    stop_payload, ups_payload,
)


@pytest.fixture
def checkouts(tmp_path, monkeypatch):
    """a: a repo's primary checkout. b: a linked worktree of it whose branch
    already holds a committed file that a's branch lacks. Both were last
    committed to an hour ago."""
    monkeypatch.setenv("GIT_COMMITTER_DATE", f"@{int(time.time()) - 3600} +0000")
    a = make_repo(tmp_path / "ws" / "a", {"app.py": "print('hi')\n"})
    b = tmp_path / "ws" / "b"
    git(a, "worktree", "add", "-q", "-b", "feature", str(b))
    (b / "old.py").write_text(VULN_PY)
    git(b, "add", "-A")
    git(b, "commit", "-q", "-m", "earlier work")
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    return a, b


def _stop(cwd, hook_env):
    return metrics_of(run_hook(stop_payload(cwd), hook_env)[1])


def _state(hook_env):
    d = hook_env["SECURITY_WARNINGS_STATE_DIR"]
    for e in os.scandir(d):
        if e.name.endswith(".json"):
            with open(e.path) as f:
                state = json.load(f)
            if "baseline_sha" in state:
                return state
    raise AssertionError(os.listdir(d))


def test_baseline_from_the_reviewed_checkout(hook_env, checkouts):
    a, _ = checkouts
    run_hook(ups_payload(a), hook_env)
    (a / "app.py").write_text(VULN_PY)
    m = _stop(a, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 0


def test_sent_on_a_skipped_review_too(hook_env, checkouts):
    a, _ = checkouts
    run_hook(ups_payload(a), hook_env)
    m = _stop(a, hook_env)
    assert m["skipped"] is True and m["bl_origin"] == 0


def test_prompt_in_a_subdirectory_is_the_same_checkout(hook_env, checkouts):
    a, _ = checkouts
    (a / "pkg").mkdir()
    run_hook(ups_payload(a / "pkg"), hook_env)
    (a / "app.py").write_text(VULN_PY)
    assert _stop(a, hook_env)["bl_origin"] == 0


def test_turn_that_only_enters_another_worktree_reviews_nothing(
        hook_env, checkouts, stub_api):
    a, b = checkouts
    run_hook(ups_payload(a), hook_env)
    m = _stop(b, hook_env)
    # b's earlier commit is not a commit made this turn.
    assert m["skipped"] is True and m["bl_origin"] == 1
    assert not stub_api.calls


def test_edit_after_entering_another_worktree_is_reviewed(
        hook_env, checkouts, stub_api):
    a, b = checkouts
    run_hook(ups_payload(a), hook_env)
    (b / "new.py").write_text(VULN_PY)
    run_hook(edit_payload(b, b / "new.py"), hook_env)
    m = _stop(b, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 1
    assert stub_api.calls.count("/v1/messages") == 1


def test_commit_made_after_entering_another_worktree_is_reviewed(
        hook_env, checkouts):
    a, b = checkouts
    run_hook(ups_payload(a), hook_env)
    (b / "new.py").write_text(VULN_PY)
    git(b, "add", "-A")
    git(b, "commit", "-q", "-m", "this turn")
    m = _stop(b, hook_env)
    # new.py, not old.py from the earlier commit.
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 1


def test_commit_in_a_worktree_created_this_turn_is_reviewed(hook_env, checkouts):
    a, _ = checkouts
    run_hook(ups_payload(a), hook_env)
    c = a.parent / "c"
    git(a, "worktree", "add", "-q", "-b", "fresh", str(c))
    (c / "new.py").write_text(VULN_PY)
    git(c, "add", "-A")
    git(c, "commit", "-q", "-m", "this turn")
    (c / "more.py").write_text(VULN_PY)
    m = _stop(c, hook_env)
    assert m["files_reviewed"] == 2 and m["bl_origin"] == 1


def test_uncommitted_work_already_in_the_other_worktree_is_left_out(
        hook_env, checkouts, stub_api):
    a, b = checkouts
    (b / "scratch.py").write_text(VULN_PY)             # untracked
    (b / "old.py").write_text(VULN_PY + "# todo\n")    # tracked, edited
    time.sleep(2.2)   # past the slack allowed around the prompt time
    run_hook(ups_payload(a), hook_env)
    m = _stop(b, hook_env)
    assert m["skipped"] is True and m["bl_origin"] == 1
    assert not stub_api.calls
    # Both are reviewed once the turn writes to them.
    (b / "scratch.py").write_text(VULN_PY + "x = 1\n")
    (b / "old.py").write_text(VULN_PY + "# done\n")
    m = _stop(b, hook_env)
    assert m["files_reviewed"] == 2 and m["bl_origin"] == 1


def test_baseline_kept_from_an_interrupted_turn_in_another_worktree(
        hook_env, checkouts, stub_api):
    a, b = checkouts
    run_hook(ups_payload(a), hook_env)
    run_hook(edit_payload(a, a / "app.py"), hook_env)
    run_hook(ups_payload(b), hook_env)
    m = _stop(b, hook_env)
    assert m["skipped"] is True and m["bl_origin"] == 21
    assert not stub_api.calls


def test_baseline_kept_from_an_interrupted_turn_in_the_same_checkout(hook_env, checkouts):
    a, _ = checkouts
    run_hook(ups_payload(a), hook_env)
    run_hook(edit_payload(a, a / "app.py"), hook_env)
    run_hook(ups_payload(a), hook_env)
    (a / "app.py").write_text(VULN_PY)
    assert _stop(a, hook_env)["bl_origin"] == 20


def test_interrupted_turn_then_a_prompt_that_cannot_capture(hook_env, checkouts):
    a, _ = checkouts
    run_hook(ups_payload(a), hook_env)
    run_hook(edit_payload(a, a / "app.py"), hook_env)
    run_hook(ups_payload(a), hook_env)
    run_hook(ups_payload(a.parent), hook_env)
    (a / "app.py").write_text(VULN_PY)
    assert _stop(a, hook_env)["bl_origin"] == 10


def test_baseline_from_another_repository(hook_env, checkouts, tmp_path):
    a, _ = checkouts
    other = make_repo(tmp_path / "ws" / "other", {"lib.py": "x = 1\n"})
    run_hook(ups_payload(a), hook_env)
    (other / "lib.py").write_text(VULN_PY)
    m = _stop(other, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 2


def test_baseline_from_a_checkout_that_is_gone(hook_env, checkouts):
    a, b = checkouts
    run_hook(ups_payload(b), hook_env)
    git(a, "worktree", "remove", "--force", str(b))
    shutil.rmtree(b, ignore_errors=True)
    (a / "app.py").write_text(VULN_PY)
    m = _stop(a, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 3


def test_prompt_in_a_folder_that_is_not_a_repo_keeps_the_untracked_snapshot(
        hook_env, checkouts):
    a, _ = checkouts
    ws = a.parent
    (a / "notes.py").write_text("n = 0\n")   # untracked since before the session
    run_hook(ups_payload(a), hook_env)
    (a / "first.py").write_text("x = 1\n")
    assert _stop(a, hook_env)["bl_origin"] == 0
    run_hook(ups_payload(ws), hook_env)
    (a / "second.py").write_text("y = 2\n")
    run_hook(edit_payload(ws, a / "second.py"), hook_env)
    m = _stop(ws, hook_env)
    # The earlier baseline is kept, so the first turn's file is reviewed
    # again. notes.py is not: the snapshot that goes with it is kept too.
    assert m["files_reviewed"] == 2 and m["bl_origin"] == 10
    # The next prompt in the repo captures a fresh baseline there.
    run_hook(ups_payload(a), hook_env)
    (a / "third.py").write_text("z = 3\n")
    m = _stop(a, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 0


def test_baseline_taken_after_a_finding_belongs_to_the_reviewed_checkout(
        hook_env, checkouts, stub_api):
    a, b = checkouts
    run_hook(ups_payload(a), hook_env)
    (b / "new.py").write_text(VULN_PY)
    stub_api.vulns = [dict(STUB_VULN, filePath="new.py")]
    assert _stop(b, hook_env)["bl_origin"] == 1
    st = _state(hook_env)
    assert os.path.samefile(st["baseline_root"], b)
    # b's HEAD at the prompt, not a's.
    assert st["head_at_capture"] == git(b, "rev-parse", "HEAD").strip()
    # Same turn, next Stop: only what changed since the finding.
    stub_api.vulns = []
    (b / "newer.py").write_text("v = 1\n")
    m = _stop(b, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 0


def test_baseline_taken_after_a_finding_keeps_the_turns_first_commit(
        hook_env, checkouts, stub_api):
    a, _ = checkouts
    head = git(a, "rev-parse", "HEAD").strip()
    run_hook(ups_payload(a), hook_env)
    (a / "app.py").write_text(VULN_PY)
    git(a, "commit", "-q", "-am", "this turn")
    stub_api.vulns = [dict(STUB_VULN, filePath="app.py")]
    assert _stop(a, hook_env)["bl_origin"] == 0
    assert _state(hook_env)["head_at_capture"] == head
    # A fix folded into the commit is still inside the turn's range.
    (a / "app.py").write_text(VULN_PY + "x = 1\n")
    git(a, "commit", "-q", "-a", "--amend", "-m", "this turn")
    assert _stop(a, hook_env)["files_reviewed"] == 1


def test_first_baseline_taken_after_a_finding_records_its_checkout(
        hook_env, checkouts, stub_api):
    a, b = checkouts
    ws = a.parent
    run_hook(ups_payload(ws), hook_env)
    (a / "new.py").write_text(VULN_PY)
    run_hook(edit_payload(ws, a / "new.py"), hook_env)
    stub_api.vulns = [dict(STUB_VULN, filePath="new.py")]
    assert _stop(ws, hook_env)["bl_origin"] == 4
    assert os.path.samefile(_state(hook_env)["baseline_root"], a)
    stub_api.vulns = []
    assert _stop(b, hook_env)["bl_origin"] == 1


def test_no_baseline_at_all(hook_env, checkouts):
    a, _ = checkouts
    ws = a.parent
    run_hook(ups_payload(ws), hook_env)
    (a / "new.py").write_text("v = 1\n")
    run_hook(edit_payload(ws, a / "new.py"), hook_env)
    m = _stop(ws, hook_env)
    assert m["files_reviewed"] == 1 and m["bl_origin"] == 4


def test_prompt_subdirectory_removed_during_the_turn(hook_env, checkouts):
    a, _ = checkouts
    (a / "pkg").mkdir()
    run_hook(ups_payload(a / "pkg"), hook_env)
    (a / "pkg").rmdir()
    (a / "app.py").write_text(VULN_PY)
    assert _stop(a, hook_env)["bl_origin"] == 0


def test_nested_worktree_removed_during_the_turn(hook_env, checkouts):
    a, _ = checkouts
    nested = a / ".claude" / "worktrees" / "wt"
    git(a, "worktree", "add", "-q", "-b", "nested", str(nested))
    run_hook(ups_payload(nested), hook_env)
    git(a, "worktree", "remove", "--force", str(nested))
    (a / "app.py").write_text(VULN_PY)
    assert _stop(a, hook_env)["bl_origin"] == 3
