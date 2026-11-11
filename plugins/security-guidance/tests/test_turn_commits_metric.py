"""The Stop row counts a turn's commits and how many no commit hook saw.
Count only: what is reviewed does not change."""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from conftest import (
    GIT_ENV, STUB_VULN, VULN_PY, bash_payload, commit_file, edit_payload, git, make_repo,
    metrics_of, run_hook, stop_payload, ups_payload,
)

import diffstate
import gitutil
import session_state

FOREVER = 1e11


@pytest.fixture(autouse=True)
def _session_id_from_the_payload(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_REMOTE_SESSION_ID", raising=False)


@pytest.fixture(autouse=True)
def _home_without_user_rules(tmp_path, monkeypatch):
    """A home directory without the user's own rules, whose keys could fill the row."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)


def session_state_file(hook_env):
    [path] = [p for p in Path(hook_env["SECURITY_WARNINGS_STATE_DIR"]).glob("security_warnings_state_*.json")]
    return path


@pytest.fixture
def repo(tmp_path, hook_env):
    r = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    run_hook(ups_payload(r), hook_env)
    return r


@pytest.fixture
def stop(hook_env):
    def run(repo, **env):
        return metrics_of(run_hook(stop_payload(repo), {**hook_env, **env})[1])
    return run


class TestStopRow:
    def test_nothing_committed(self, repo, stop):
        assert "turn_commits" not in stop(repo)

    def test_commit_no_hook_saw(self, repo, stop, stub_api):
        commit_file(repo, "a.py", "print('a')\n")
        m = stop(repo)
        assert m["turn_commits"] == 10101
        assert m["files_reviewed"] == 1

    def test_custom_rule_counts_take_one_place(self, repo, stop, hook_env, stub_api):
        (repo / ".claude").mkdir()
        (repo / ".claude" / "security-patterns.json").write_text(json.dumps({"patterns": [
            {"rule_name": "r1", "substrings": ["NEEDLE("], "reminder": "x", "paths": ["src/**"]},
            {"rule_name": "r2", "substrings": ["NEEDLE("], "reminder": "x", "exclude_paths": ["src/**"]},
        ]}))
        (repo / "src").mkdir()
        (repo / "src" / "a.ts").write_text("NEEDLE(1)\n")
        env = {**hook_env, "CLAUDE_PROJECT_DIR": str(repo)}
        run_hook(edit_payload(repo, repo / "src" / "a.ts", "NEEDLE(1)\n"), env)
        commit_file(repo, "a.py", "print('a')\n")
        m = stop(repo, CLAUDE_PROJECT_DIR=str(repo))
        assert [k for k in m if k.startswith("cr_")] == ["cr_pack"]
        assert "turn_commits" in m

    def test_commit_the_hook_reviewed(self, repo, stop, hook_env):
        _, out = commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
        assert stop(repo)["turn_commits"] == 10000

    def test_seen_but_not_reviewed(self, repo, stop, hook_env):
        _, out = commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -m change", out),
                 {**hook_env, "SECURITY_GUIDANCE_COMMIT_REVIEW": "off"})
        assert stop(repo)["turn_commits"] == 10100

    def test_quiet_commit_is_seen_through_the_reflog(self, repo, stop, hook_env):
        commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -q -m change"),
                 {**hook_env, "SECURITY_GUIDANCE_COMMIT_REVIEW": "off"})
        assert stop(repo)["turn_commits"] == 10100

    def test_one_of_two(self, repo, stop, hook_env):
        _, out = commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
        commit_file(repo, "b.py", "print('b')\n")
        assert stop(repo)["turn_commits"] == 20101

    def test_hook_for_a_failed_commit_hides_nothing(self, repo, stop, hook_env):
        run_hook(bash_payload(repo, "git commit -m x", "nothing to commit"), hook_env)
        commit_file(repo, "a.py", "print('a')\n")
        assert stop(repo)["turn_commits"] == 10101

    def test_hook_for_another_repository_hides_nothing(
            self, repo, stop, hook_env, tmp_path):
        other = make_repo(tmp_path / "other")
        _, out = commit_file(other, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, f"git -C {other} commit -m x", out), hook_env)
        commit_file(repo, "a.py", "print('a')\n")
        assert stop(repo)["turn_commits"] == 10101

    def test_second_stop_of_a_turn_counts_only_what_is_new(self, repo, stop, hook_env):
        _, out = commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
        assert stop(repo)["turn_commits"] == 10000
        assert "turn_commits" not in stop(repo)
        commit_file(repo, "b.py", "print('b')\n")
        assert stop(repo)["turn_commits"] == 10101

    def test_review_still_running(self, repo, stop):
        sha, _ = commit_file(repo, "a.py", "print('a')\n")
        marker = repo / ".git" / f"sg-inflight-{sha}"
        marker.write_text("")
        assert stop(repo)["turn_commits"] == 10000
        assert marker.exists()

    def test_other_session_in_the_same_clone(self, repo, stop, hook_env):
        _, out = commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -m change", out, session_id="s2"),
                 hook_env)
        assert stop(repo)["turn_commits"] == 10000

    def test_seen_by_another_session_but_not_reviewed(self, repo, stop, hook_env):
        _, out = commit_file(repo, "notes.md", "words\n")
        run_hook(bash_payload(repo, "git commit -m change", out, session_id="s2"),
                 hook_env)
        assert stop(repo)["turn_commits"] == 10100

    def test_counted_once_among_sessions(self, repo, stop, hook_env):
        run_hook(ups_payload(repo, session_id="s2"), hook_env)
        commit_file(repo, "a.py", "print('a')\n")
        assert stop(repo)["turn_commits"] == 10101
        _, so, _ = run_hook(stop_payload(repo, session_id="s2"), hook_env)
        assert "turn_commits" not in metrics_of(so)

    @pytest.mark.parametrize("env", [
        {"ENABLE_STOP_REVIEW": "0"}, {"ANTHROPIC_API_KEY": ""}])
    def test_stop_rows_that_review_nothing_count_too(self, repo, stop, env):
        commit_file(repo, "a.py", "print('a')\n")
        m = stop(repo, **env)
        assert m["skipped"] and m["turn_commits"] == 10101

    def test_commit_after_the_stop_began_is_left_for_the_next(self, tmp_path):
        r = make_repo(tmp_path / "r")
        start, since = git(r, "rev-parse", "HEAD").strip(), time.time()
        commit_file(r, "a.py", "1\n")
        assert gitutil.turn_commit_shas(str(r), since, since - 10, start) == []

    def test_kept_baseline_counts_this_turns_commits_only(self, repo, stop, hook_env):
        run_hook(edit_payload(repo, repo / "app.py"), hook_env)
        commit_file(repo, "between.py", "print('b')\n")
        time.sleep(1.1)
        run_hook(ups_payload(repo), hook_env)
        commit_file(repo, "a.py", "print('a')\n")
        assert stop(repo)["turn_commits"] == 10101

    def test_woken_stop_after_a_kept_baseline(self, repo, stop, hook_env, stub_api):
        stub_api.vulns = [STUB_VULN]
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py"), hook_env)
        commit_file(repo, "between.py", "print('b')\n")
        time.sleep(1.1)
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY + "# 2\n")
        assert "turn_commits" not in stop(repo)
        (repo / "app.py").write_text(VULN_PY + "# 3\n")
        assert "turn_commits" not in stop(repo)

    def test_slow_git_does_not_hold_the_row(self, repo, monkeypatch):
        import security_reminder_hook as hook
        monkeypatch.setattr(hook, "_TURN_COMMITS_WAIT_S", 0.2)
        monkeypatch.setattr(hook, "_turn_commits_request",
                            ("s1", str(repo), time.time() - 60, None, FOREVER))
        monkeypatch.setattr(diffstate, "turn_commits_code", lambda *a: time.sleep(3))
        row, started = {}, time.monotonic()
        hook._add_turn_commits(row)
        assert row == {"turn_commits": -1} and time.monotonic() - started < 2

    @pytest.mark.parametrize("started", [None, 5, [], [1.0]])
    def test_odd_turn_start_counts_nothing(self, repo, stop, hook_env, started):
        state = session_state_file(hook_env)
        data = json.loads(state.read_text())
        state.write_text(json.dumps({**data, "turn_started": started}))
        commit_file(repo, "a.py", "print('a')\n")
        assert "turn_commits" not in stop(repo)

    def test_full_row_leaves_the_commits_for_the_next(self, repo, monkeypatch, hook_env):
        import security_reminder_hook as hook
        monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR",
                           hook_env["SECURITY_WARNINGS_STATE_DIR"])
        sha, _ = commit_file(repo, "a.py", "print('a')\n")
        monkeypatch.setattr(hook, "_turn_commits_request",
                            ("s1", str(repo), time.time() - 60, None, FOREVER))
        row = {f"k{i}": 1 for i in range(20)}
        hook._add_turn_commits(row)
        assert "turn_commits" not in row
        row = {f"k{i}": 1 for i in range(19)}
        hook._add_turn_commits(row)
        assert list(row)[-1] == "turn_commits" and row["turn_commits"] > 0
        row = {}
        hook._add_turn_commits(row)
        assert row == {}

    def test_worktree_counts_its_own_commits(self, repo, stop, hook_env, tmp_path):
        tree = tmp_path / "tree"
        git(repo, "worktree", "add", "-q", "-b", "side", str(tree))
        commit_file(tree, "a.py", "print('a')\n")
        assert "turn_commits" not in stop(repo)
        assert stop(tree)["turn_commits"] == 10101

    def test_switch_commit_and_come_back(self, repo, stop, hook_env):
        git(repo, "branch", "side")
        time.sleep(1.1)
        run_hook(ups_payload(repo), hook_env)
        git(repo, "checkout", "-q", "side")
        commit_file(repo, "a.py", "print('a')\n")
        git(repo, "checkout", "-q", "main")
        assert stop(repo)["turn_commits"] == 10101

    def test_repository_without_a_commit(self, tmp_path, stop, hook_env):
        r = tmp_path / "empty"
        r.mkdir()
        git(r, "init", "-q")
        (r / "a.py").write_text("print('a')\n")
        run_hook(ups_payload(r), hook_env)
        assert "turn_commits" not in stop(r)

    def test_portable_hosts_get_no_file(self, repo, hook_env):
        env = {**hook_env, "SECURITY_GUIDANCE_PORTABLE_OUTPUT": "1"}
        _, out = commit_file(repo, "a.py", "print('a')\n")
        run_hook(bash_payload(repo, "git commit -m change", out), env)
        run_hook(stop_payload(repo), env)
        assert not [n for n in os.listdir(hook_env["SECURITY_WARNINGS_STATE_DIR"])
                    if n.endswith(".commits")]

    def test_comes_after_the_older_keys(self, repo, stop):
        commit_file(repo, "a.py", "print('a')\n")
        keys = list(stop(repo))
        assert keys.index("turn_commits") > keys.index("review_scope")
        assert keys.index("turn_commits") > keys.index("bl_origin")

    def test_no_prompt_no_count(self, tmp_path, stop, hook_env):
        r = make_repo(tmp_path / "other")
        commit_file(r, "a.py", "print('a')\n")
        assert "turn_commits" not in stop(r)

    def test_one_review_request_as_before(self, repo, stop, stub_api):
        (repo / "handlers.py").write_text(VULN_PY)
        commit_file(repo, "a.py", "print('a')\n")
        assert stop(repo)["turn_commits"] == 10101
        assert stub_api.calls.count("/v1/messages") == 1

    def test_unreadable_record_does_not_stop_the_review(self, repo, stop, hook_env):
        path = os.path.join(hook_env["SECURITY_WARNINGS_STATE_DIR"],
                            "security_warnings_state_s1.commits")
        os.mkdir(path)
        _, out = commit_file(repo, "a.py", "print('a')\n")
        rc, so, _ = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
        assert rc == 0 and metrics_of(so)["commit_review"]
        m = stop(repo)
        assert m["turn_commits"] == -1
        assert m["files_reviewed"] == 1


class TestTurnCommitShas:
    def head(self, repo):
        return git(repo, "rev-parse", "HEAD").strip()

    def test_newest_first_and_not_before_the_turn(self, tmp_path):
        r = make_repo(tmp_path / "r")
        start, since = self.head(r), time.time()
        a, _ = commit_file(r, "a.py", "1\n")
        b, _ = commit_file(r, "b.py", "1\n")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [b, a]
        assert gitutil.turn_commit_shas(str(r), since + 3600, FOREVER, start) == []

    @pytest.mark.parametrize("old_start", [False, True])
    @pytest.mark.parametrize("how", ["--hard", "--soft"])
    def test_reset_and_commit_again(self, tmp_path, old_start, how):
        r = make_repo(tmp_path / "r")
        start, since = self.head(r), time.time()
        if old_start:
            # The start commit is then in no second the turn is in.
            time.sleep(1.1)
            since = time.time()
            time.sleep(1.1)
        a, _ = commit_file(r, "a.py", "1\n")
        git(r, "reset", "-q", how, start)
        b, _ = commit_file(r, "b.py", "1\n")
        shas = gitutil.turn_commit_shas(str(r), since, FOREVER, start)
        assert shas == [b, a]

    def test_moving_head_is_not_a_commit(self, tmp_path):
        r = make_repo(tmp_path / "r")
        start, since = self.head(r), time.time()
        git(r, "checkout", "-q", "-b", "commit-x")
        a, _ = commit_file(r, "a.py", "1\n")
        git(r, "checkout", "-q", "main")
        git(r, "merge", "-q", "--ff-only", "commit-x")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [a]

    @pytest.mark.parametrize("op", ["merge", "cherry-pick"])
    def test_finished_conflict_does_not_count(self, tmp_path, op):
        r = make_repo(tmp_path / "r")
        git(r, "checkout", "-q", "-b", "side")
        commit_file(r, "a.py", "side\n")
        git(r, "checkout", "-q", "main")
        commit_file(r, "a.py", "main\n")
        time.sleep(1.1)
        start, since = self.head(r), time.time()
        subprocess.run(["git", op, "side"], cwd=r, capture_output=True,
                       env={**os.environ, **GIT_ENV})
        (r / "a.py").write_text("both\n")
        git(r, "add", "a.py")
        git(r, "-c", "core.editor=true", op, "--continue")
        assert self.head(r) != start
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == []

    def test_many_head_moves_hide_nothing(self, tmp_path):
        r = make_repo(tmp_path / "r")
        start, since = self.head(r), time.time()
        a, _ = commit_file(r, "a.py", "1\n")
        for _ in range(60):
            git(r, "checkout", "-q", "--detach", start)
            git(r, "checkout", "-q", "main")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [a]

    def test_file_named_head(self, tmp_path):
        r = make_repo(tmp_path / "r")
        start, since = self.head(r), time.time()
        a, _ = commit_file(r, "HEAD", "1\n")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [a]

    def test_amend_counts(self, tmp_path):
        r = make_repo(tmp_path / "r")
        start, since = self.head(r), time.time()
        a, _ = commit_file(r, "a.py", "1\n")
        git(r, "commit", "-q", "--amend", "-m", "other words")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [self.head(r), a]

    @pytest.mark.parametrize("kind", ["fixed", "extended", "perl"])
    def test_grep_setting_does_not_matter(self, tmp_path, kind):
        r = make_repo(tmp_path / "r")
        git(r, "config", "grep.patternType", kind)
        start, since = self.head(r), time.time()
        a, _ = commit_file(r, "a.py", "1\n")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [a]

    def test_date_setting_does_not_matter(self, tmp_path):
        r = make_repo(tmp_path / "r")
        git(r, "config", "log.date", "relative")
        start, since = self.head(r), time.time()
        a, _ = commit_file(r, "a.py", "1\n")
        assert gitutil.turn_commit_shas(str(r), since, FOREVER, start) == [a]

    def test_no_repository(self, tmp_path):
        assert gitutil.turn_commit_shas(str(tmp_path), time.time(), FOREVER) is None


def test_parts_are_capped(tmp_path, monkeypatch):
    r = make_repo(tmp_path / "r")
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(diffstate, "turn_commit_shas",
                        lambda *a, **k: [f"{i:040x}" for i in range(100)])
    assert diffstate.turn_commits_code(str(r), time.time() - 60, time.time())[0] == 999999


def test_old_commit_records_are_removed(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path))
    diffstate.note_seen_commits("s1", ["abc1234"])
    diffstate.note_seen_commits("s2", ["abc1234"])
    os.utime(session_state.get_commit_log_file("s1"), (1, 1))
    session_state.cleanup_old_state_files()
    assert [n for n in os.listdir(tmp_path) if n.endswith(".commits")] == [
        "security_warnings_state_s2.commits"]
