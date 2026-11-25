"""The Stop row counts files that changed with no Stop review to see them.
Count only: what is reviewed does not change."""
import json
import os
import time
from pathlib import Path

import pytest

from conftest import (
    STUB_VULN, commit_file, edit_payload, git, make_repo, metrics_of, run_hook, stop_payload,
    ups_payload,
)

AGENT = [{"id": "t1", "type": "subagent", "status": "running"}]


@pytest.fixture(autouse=True)
def _session_id_from_the_payload(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_REMOTE_SESSION_ID", raising=False)


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo", {"app.py": "a = 1\n", "lib.py": "b = 1\n"})


class Session:
    def __init__(self, repo, env, api):
        self.repo, self.env, self.api = repo, env, api

    def prompt(self, cwd=None):
        run_hook(ups_payload(cwd or self.repo), self.env)

    def stop(self, **fields):
        """The row's key, None when the row does not have it."""
        _, out, _ = run_hook({**stop_payload(self.repo), **fields}, self.env)
        self.row = metrics_of(out)
        return self.row.get("changed_files")

    def write(self, name="app.py", text="x = 1\n"):
        with open(self.repo / name, "a") as f:
            f.write(text)

    def state(self):
        [path] = Path(self.env["SECURITY_WARNINGS_STATE_DIR"]).glob("security_warnings_state_*.json")
        return json.loads(path.read_text())


@pytest.fixture
def session(repo, hook_env, stub_api):
    return Session(repo, hook_env, stub_api)


def test_turns_that_end_with_a_stop_count_nothing(session):
    session.prompt()
    session.write()
    assert session.stop() is None
    session.prompt()
    session.write("new.py")
    assert session.stop() is None
    # Between turns: the user's own edit.
    session.write("lib.py")
    session.prompt()
    assert session.stop() is None


@pytest.mark.parametrize("name", ["app.py", "new.py"])
def test_turn_with_no_stop(session, name):
    session.prompt()
    session.write(name)
    session.prompt()
    assert session.stop() == 1001
    session.prompt()
    assert session.stop() is None


def test_turn_with_no_stop_and_no_change(session):
    session.prompt()
    session.write()
    session.prompt()
    session.stop()
    session.prompt()
    session.prompt()
    assert session.stop() is None


def test_several_prompts_before_a_stop_are_one_number(session):
    session.prompt()
    session.write("app.py")
    session.write("new.py")
    session.prompt()
    session.write("lib.py")
    session.write("notes.txt")
    session.prompt()
    assert session.stop() == 1003


def test_untracked_file_that_gets_staged_is_counted_once(session):
    session.prompt()
    session.write("new.py")
    session.prompt()
    git(session.repo, "add", "new.py")
    session.prompt()
    assert session.stop() == 1001


def test_only_reviewable_files_are_counted(session):
    session.prompt()
    (session.repo / "vendor").mkdir()
    session.write("vendor/a.js")
    session.write("Dockerfile")
    session.prompt()
    assert session.stop() == 1001


def test_files_past_the_listing_cap_are_not_new(session):
    for name in ("b1.py", "b2.py", "b3.py"):
        session.write(name)
    session.prompt()
    set_state(session, untracked_at_baseline={
        "b1.py": (session.repo / "b1.py").stat().st_mtime_ns, "\0capped_at_ns": time.time_ns()})
    session.prompt()
    assert session.stop() is None


def test_recorded_edit_keeps_the_baseline_and_counts_nothing(session):
    session.prompt()
    session.write()
    run_hook(edit_payload(session.repo, session.repo / "app.py"), session.env)
    session.prompt()
    assert session.stop() is None
    assert session.row["files_reviewed"] == 1


def test_moved_head_is_told_apart(session):
    session.prompt()
    commit_file(session.repo, "lib.py", "b = 2\n")
    session.prompt()
    assert session.stop() == 11001


def test_agent_at_work_in_the_background(session):
    session.prompt()
    session.write("lib.py")
    session.stop(background_tasks=AGENT)
    time.sleep(0.05)
    session.write("app.py")
    session.write("new.py")
    session.prompt()
    # lib.py was in the first review.
    assert session.stop() == 3002


def test_agent_turn_whose_files_change_again_or_went_before_the_stop(session):
    session.prompt()
    session.write("app.py")
    (session.repo / "lib.py").unlink()
    session.stop(background_tasks=AGENT)
    session.prompt()
    session.write("app.py")
    assert session.stop() is None


def test_commit_before_the_stop_does_not_count_as_moved(session):
    session.prompt()
    commit_file(session.repo, "lib.py", "b = 2\n")
    session.stop(background_tasks=AGENT)
    time.sleep(0.05)
    session.write("app.py")
    session.prompt()
    assert session.stop() == 3001


def test_shell_task_in_the_background_is_not_counted(session):
    session.prompt()
    session.stop(background_tasks=[{"id": "t1", "type": "shell", "status": "running"}])
    session.write()
    session.prompt()
    assert session.stop() is None


@pytest.mark.parametrize("wake_prompt", [True, False])
def test_turn_that_a_finding_starts(session, wake_prompt):
    session.prompt()
    session.write()
    session.api.vulns = [STUB_VULN]
    session.stop()
    session.api.vulns = []
    time.sleep(0.05)
    if wake_prompt:
        session.prompt()
    session.write("lib.py")
    session.stop(stop_hook_active=True)
    session.prompt()
    assert session.stop() == 2001


@pytest.mark.parametrize("recorded", [False, True])
def test_failed_review(session, recorded):
    session.prompt()
    session.write()
    if recorded:
        run_hook(edit_payload(session.repo, session.repo / "app.py"), session.env)
    session.api.status = 400
    assert session.stop() == (None if recorded else 4001)
    session.api.status = 200
    session.prompt()
    assert session.stop() is None
    # The recorded edit is reviewed now, the other is in no review.
    assert ("files_reviewed" in session.row) == recorded


def test_finding_of_a_commit_review_does_not_start_the_turn(session):
    session.prompt()
    set_state(session, previous_findings_ts=time.time(), previous_findings=[])
    session.stop()
    session.prompt()
    session.write()
    session.prompt()
    assert session.stop() == 1001


def test_prompt_outside_a_repository_leaves_the_marks(session, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    session.prompt()
    session.write()
    session.stop()
    session.prompt(plain)
    session.prompt()
    assert session.stop() is None


def test_counted_on_a_review_row_within_the_key_cap(session):
    session.prompt()
    session.write()
    session.prompt()
    session.write("lib.py")
    assert session.stop() == 1001
    assert list(session.row).index("changed_files") < 20
    session.prompt()
    session.write()
    session.prompt()
    session.write("lib.py")
    session.api.vulns = [STUB_VULN]
    assert session.stop() == 1001
    assert list(session.row).index("changed_files") < 20


def test_other_checkout_is_not_counted(session, tmp_path):
    other = make_repo(tmp_path / "other", {"app.py": "a = 1\n"})
    session.prompt()
    session.write()
    session.prompt(other)
    assert session.stop() is None


@pytest.mark.parametrize("env", [{"ENABLE_STOP_REVIEW": "0"}, {"SECURITY_GUIDANCE_PORTABLE_OUTPUT": "1"}])
def test_not_counted(session, env):
    session.env = {**session.env, **env}
    session.prompt()
    session.write()
    session.prompt()
    assert "dropped" not in session.state()


def set_state(session, **fields):
    path = next(Path(session.env["SECURITY_WARNINGS_STATE_DIR"]).glob("security_warnings_state_*.json"))
    path.write_text(json.dumps({**json.loads(path.read_text()), **fields}))


def test_base_that_is_gone(session):
    session.prompt()
    session.write()
    set_state(session, baseline_sha="1" * 40)
    session.prompt()
    assert session.stop() == -1


@pytest.mark.parametrize("fields", [
    {"dropped": "x"}, {"dropped": []}, {"dropped": {"a": 1}},
    {"stop_left": "x", "no_stop": False}, {"untracked_at_baseline": "x"}])
def test_unusable_state_does_not_stop_the_review(session, fields):
    session.prompt()
    set_state(session, **fields)
    session.write()
    session.prompt()
    session.write("lib.py")
    session.stop()
    assert session.row["files_reviewed"] == 1


def test_baseline_that_fell_back_to_head_says_nothing(session):
    session.write()
    session.prompt()
    set_state(session, baseline_fail=1, baseline_sha=git(session.repo, "rev-parse", "HEAD").strip())
    session.prompt()
    assert session.stop() == -1


def test_baseline_that_is_head_both_times_counts_nothing(session):
    session.write()
    session.prompt()
    set_state(session, baseline_fail=2)
    state = session.state()
    import diffstate
    assert diffstate.dropped_changes(
        state, state["baseline_sha"], 2, state["baseline_root"], state["head_at_capture"],
        state["untracked_at_baseline"]) == 0


def test_listing_that_failed_does_not_make_old_files_new(session):
    session.write("old.py")
    time.sleep(0.05)
    session.prompt()
    set_state(session, untracked_at_baseline={})
    session.prompt()
    assert session.stop() is None


def test_nested_checkout_is_not_counted(session):
    session.prompt()
    make_repo(session.repo / "inner", {"a.py": "a = 1\n"})
    session.prompt()
    assert session.stop() is None


def test_files_moved_in_by_an_agent(session):
    session.prompt()
    (session.repo.parent / "old.py").write_text("x = 1\n")
    session.stop(background_tasks=AGENT)
    time.sleep(0.05)
    (session.repo.parent / "old.py").rename(session.repo / "old.py")
    session.prompt()
    # Windows keeps a moved file's times.
    assert session.stop() == (None if os.name == "nt" else 3001)


def test_failed_review_adds_to_an_earlier_count(session):
    session.prompt()
    session.write()
    session.prompt()
    session.write("lib.py")
    session.api.status = 400
    assert session.stop() == 1002


def test_stop_during_the_count(session, monkeypatch):
    import security_reminder_hook as hook
    for k, v in session.env.items():
        monkeypatch.setenv(k, v)
    session.prompt()
    session.write()

    def count(*args):
        session.stop()
        return 1001
    monkeypatch.setattr(hook.diffstate, "dropped_changes", count)
    with pytest.raises(SystemExit):
        hook.handle_user_prompt_submit(ups_payload(session.repo))
    assert "dropped" not in session.state()


def test_slow_git_is_given_up(session, monkeypatch):
    import diffstate
    session.prompt()
    session.write()
    state = session.state()

    def slow(*args, timeout, env, **kwargs):
        assert timeout <= 1
        assert env["GIT_NO_LAZY_FETCH"] == "1" and env["GIT_ALLOW_PROTOCOL"]
        raise diffstate.subprocess.TimeoutExpired("git", timeout)
    monkeypatch.setattr(diffstate.subprocess, "run", slow)
    assert diffstate.dropped_changes(
        state, "2" * 40, 0, state["baseline_root"], state["head_at_capture"], {}) == -1


def test_subagent_stop_leaves_the_count_for_the_stop(session):
    session.prompt()
    session.write()
    session.prompt()
    assert session.stop(hook_event_name="SubagentStop") is None
    assert session.stop() == 1001


def test_what_is_reviewed_does_not_change(session):
    session.prompt()
    session.write(text="MARK_dropped = 1\n")
    session.prompt()
    session.write("lib.py", "MARK_sent = 1\n")
    session.stop()
    sent = "".join(session.api.bodies)
    assert "MARK_sent" in sent and "MARK_dropped" not in sent
