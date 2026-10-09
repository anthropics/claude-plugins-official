"""A review that got no verdict is never reported as clean."""
import json
import time

import pytest

from conftest import (
    STUB_VULN, VULN_PY, bash_payload, commit_file, edit_payload, git,
    metrics_of, run_hook, stop_payload, ups_payload,
)

import llm
import security_reminder_hook as hook


def _reviewed(repo):
    p = repo / ".git" / "sg-reviewed-shas"
    return p.read_text() if p.exists() else ""


def _rewake_body(stdout, stderr):
    """What Claude Code shows Claude for an exit-2 asyncRewake hook: stderr,
    else stdout."""
    return stderr or stdout


def _commit(repo, env, content=VULN_PY, session_id="s1"):
    sha, out = commit_file(repo, "app.py", content)
    rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out,
                                       session_id=session_id), env)
    return sha, rc, so, se


class TestFailedReviewIsNotClean:
    def test_commit_left_unreviewed_and_user_told(self, env, gateway, workspace):
        _, repo = workspace
        gateway.status = 401
        sha, rc, so, se = _commit(repo, env)
        m = metrics_of(so)
        assert m["review_failed"] is True and m["api_error"] == 401 and m["vulns_found"] == 0
        assert sha not in _reviewed(repo)
        assert rc == 2
        body = _rewake_body(so, se)
        assert ("The security review of this commit did not complete: "
                "the API rejected the plugin's credentials (HTTP 401).") in body
        assert "ANTHROPIC_CUSTOM_HEADERS" in body  # ANTHROPIC_BASE_URL is set
        assert "If it is pushed later from Claude Code, the push review will check it." in body
        assert "log.txt" in body
        summary = json.loads(so.strip().splitlines()[-1])["rewakeSummary"]
        assert summary.startswith("Commit security review did not complete: "
                                  "the API rejected the plugin's credentials (HTTP 401). Log: ")

    def test_commit_pushed_by_the_same_command(self, env, gateway, workspace):
        """The push hook does not run for `git commit && git push`, so no later
        push review covers this commit."""
        _, repo = workspace
        gateway.status = 401
        sha, out = commit_file(repo, "app.py", VULN_PY)
        out += f"To /srv/remote.git\n   1111111..{sha[:7]}  main -> main\n"
        rc, so, se = run_hook(bash_payload(repo, "git commit -m change && git push", out), env)
        assert rc == 2
        assert "The same command pushed it, so a later push will not re-check it." in se
        assert "If it is pushed later" not in se

    @pytest.mark.parametrize("command", [
        'git commit -m "retry git push on 403"',  # push only in the message
        "git commit -m change && git push",      # push rejected or output hidden
    ])
    def test_push_in_the_command_without_push_output(self, env, gateway, workspace, command):
        _, repo = workspace
        gateway.status = 401
        sha, out = commit_file(repo, "app.py", VULN_PY)
        rc, so, se = run_hook(bash_payload(repo, command, out), env)
        assert rc == 2
        assert "The same command pushed it" not in se
        assert ("If the same command pushed it, a later push will not re-check it; "
                "otherwise a later push from Claude Code will.") in se

    def test_told_once_per_session_for_each_kind_of_failure(self, env, gateway, workspace):
        _, repo = workspace
        gateway.status = 401
        _commit(repo, env)
        sha2, rc, so, se = _commit(repo, env, VULN_PY + "# 2\n")
        assert rc == 0 and se == ""
        assert metrics_of(so)["review_failed"] is True
        assert sha2 not in _reviewed(repo)
        gateway.status = 503  # a different kind of failure is still told
        sha3, rc, so, se = _commit(repo, env, VULN_PY + "# 3\n")
        assert rc == 2 and "busy or unavailable (HTTP 503)" in se
        assert sha3 not in _reviewed(repo)

    def test_unreadable_reply_is_a_failed_review(self, env, gateway, workspace):
        _, repo = workspace
        gateway.reply = "I can't help with that."
        sha, rc, so, se = _commit(repo, env)
        assert metrics_of(so)["review_failed"] is True
        assert sha not in _reviewed(repo)

    def test_reply_without_the_verdict_flag_is_a_failed_review(self, env, gateway, workspace):
        _, repo = workspace
        gateway.reply = json.dumps({"findings": []})
        sha, rc, so, se = _commit(repo, env)
        assert metrics_of(so)["review_failed"] is True
        assert sha not in _reviewed(repo)

    def test_unexpected_error_in_the_call_is_a_failed_review(self, monkeypatch):
        def boom(*a, **k):
            raise ConnectionResetError("dropped")
        monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
        monkeypatch.setattr(llm, "_call_claude_dual_or", boom)
        assert llm.analyze_code_security([("a.py", "+x = 1\n")], is_diff=True) == (None, [])
        assert llm.last_review_failed()

    def test_pushed_commit_is_told_after_an_unpushed_one(self, env, gateway, workspace):
        _, repo = workspace
        gateway.status = 401
        _commit(repo, env)
        sha, out = commit_file(repo, "app.py", VULN_PY + "# 2\n")
        out += "To github.com:o/r.git\n   1111111..2222222  main -> main\n"
        rc, so, se = run_hook(bash_payload(repo, "git commit -am x && git push", out), env)
        assert rc == 2 and "The same command pushed it" in se

    def test_clean_review_still_marks_the_commit(self, env, gateway, workspace):
        _, repo = workspace
        sha, rc, so, se = _commit(repo, env)
        m = metrics_of(so)
        assert rc == 0 and "review_failed" not in m and m["vulns_found"] == 0
        assert sha in _reviewed(repo)

    def test_push_sweep_leaves_the_range_unreviewed(self, env, gateway, workspace, tmp_path):
        """Also told after a commit review failed the same way: a failed push
        review is not re-checked later, so it has its own notice."""
        ws, repo = workspace
        remote = tmp_path / "remote.git"
        git(ws, "init", "-q", "--bare", str(remote))
        git(repo, "remote", "add", "origin", str(remote))
        git(repo, "push", "-q", "-u", "origin", "main")
        base = git(repo, "rev-parse", "HEAD").strip()
        gateway.status = 401
        sha, rc, so, se = _commit(repo, env)
        assert rc == 2
        git(repo, "push", "-q", "origin", "main")
        push_stdout = f"To {remote}\n   {base[:7]}..{sha[:7]}  main -> main\n"
        rc, so, se = run_hook(bash_payload(repo, "git push origin main", push_stdout), env)
        m = metrics_of(so)
        assert m["push_sweep"] is True and m["review_failed"] is True, m
        assert sha not in _reviewed(repo)
        assert rc == 2
        assert "The security review of this push did not complete" in se
        assert ("It was for the pushed commits not already reviewed when they were "
                "committed, and a later push will not re-check them.") in se

    def test_subagent_review_failure_keeps_the_diff_unreviewed(self, env, gateway, workspace):
        """A SubagentStop review that finds nothing records its diff as
        reviewed; one that got no verdict must not, or it is never retried."""
        _, repo = workspace
        gateway.reply = "not json"
        run_hook(ups_payload(repo), env)
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py", VULN_PY), env)
        rc, so, se = run_hook(stop_payload(repo, event="SubagentStop"), env)
        assert rc == 0, (so, se)
        gateway.reply, gateway.vulns = None, [STUB_VULN]
        rc, so, se = run_hook(stop_payload(repo, event="SubagentStop"), env)
        assert rc == 2 and "command_injection" in se, (so, se)

    @pytest.fixture
    def race(self, monkeypatch):
        """Runs the race with the fallback starting at once; agentic_review
        and the single-shot review are stand-ins."""
        calls = []
        monkeypatch.setenv("SG_AGENTIC_RACE_DELAY_S", "0")
        monkeypatch.delenv("SG_AGENTIC_NO_RACE", raising=False)

        def failing_single_shot(*a, **k):
            calls.append("single_shot")
            llm._review_status.failed = True
            return None, []

        monkeypatch.setattr(hook, "analyze_code_security", failing_single_shot)

        def run(agentic):
            monkeypatch.setattr(hook, "agentic_review", agentic)
            llm._review_status.failed = False
            result = hook._agentic_review_with_race("/nonexistent", [("a.py", "+x")], ["a.py"], [])
            assert llm.last_review_failed() is False  # the flag stays on its own thread
            return result
        run.calls = calls
        return run

    def test_failed_fallback_waits_for_agentic(self, race):
        """Direct calls can fail where the agentic reviewer's CLI works (it
        may hold a credential the direct calls lack); its verdict must count."""
        def slow_agentic(*a, **k):
            time.sleep(1)
            return None, [], {"agentic": True}

        g, v, m = race(slow_agentic)
        assert m["race_winner"] == 1 and not m.get("review_failed")

    def test_both_failing_reports_the_fallback_once(self, race):
        def failing_agentic(*a, **k):
            time.sleep(1)
            return None, [], {"agentic_fallback": "investigate:ProcessError"}

        g, v, m = race(failing_agentic)
        assert m["race_winner"] == 2 and m["review_failed"] is True
        assert "agentic_fallback" not in m  # the caller must not rerun it
        assert race.calls == ["single_shot"]

    def test_no_fallback_after_agentic_finished(self, race, monkeypatch):
        """Once agentic has answered, the delayed fallback never starts, even
        after the caller has taken agentic's result off the queue."""
        monkeypatch.setenv("SG_AGENTIC_RACE_DELAY_S", "1")

        def quick_failing_agentic(*a, **k):
            return None, [], {"agentic_fallback": "investigate:ProcessError"}

        g, v, m = race(quick_failing_agentic)
        assert m["race_winner"] == 1
        time.sleep(1.5)
        assert race.calls == []

    def test_agentic_failing_while_the_fallback_overruns(self, race, monkeypatch):
        """Past the deadline the race reports no verdict instead of letting the
        caller start yet another review."""
        monkeypatch.setattr(hook, "_RACE_MAX_WAIT_S", 2)

        def slow_single_shot(*a, **k):
            race.calls.append("single_shot")
            time.sleep(10)
            return None, []

        monkeypatch.setattr(hook, "analyze_code_security", slow_single_shot)

        def failing_agentic(*a, **k):
            time.sleep(0.5)
            return None, [], {"agentic_fallback": "investigate:ProcessError"}

        t0 = time.monotonic()
        g, v, m = race(failing_agentic)
        assert time.monotonic() - t0 < 5
        assert m["review_failed"] is True and m["api_error"] == hook._RACE_TIMED_OUT
        assert "agentic_fallback" not in m
        assert hook._review_failure_reason(m["api_error"])[1] == "the review did not finish in time"

    def test_failed_fallback_stops_waiting_at_the_deadline(self, race, monkeypatch):
        monkeypatch.setattr(hook, "_RACE_MAX_WAIT_S", 1)

        def hung_agentic(*a, **k):
            time.sleep(30)

        g, v, m = race(hung_agentic)
        assert m["race_winner"] == 2 and m["review_failed"] is True


class TestFailureReason:
    @pytest.mark.parametrize("status,failure,reason", [
        (401, "auth", "the API rejected the plugin's credentials (HTTP 401)"),
        (403, "auth", "the API refused access (HTTP 403)"),
        (529, "busy", "the API was busy or unavailable (HTTP 529)"),
        (-1, "network", "the model could not be reached (network error or timeout)"),
        (404, "request", "the API refused the request (HTTP 404)"),
        (None, "reply", "the model's reply could not be read"),
    ])
    def test_first_party(self, monkeypatch, status, failure, reason):
        for var in llm._PROVIDER_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        assert hook._review_failure_reason(status)[:2] == (failure, reason)

    def test_cloud_provider(self, monkeypatch):
        monkeypatch.setenv("CLAUDE_CODE_USE_BEDROCK", "1")
        for status in (-1, None):
            assert hook._review_failure_reason(status)[:2] == (
                "provider", "the review through the cloud provider got no answer")

    def test_causes_name_only_settings_in_use(self, monkeypatch):
        for var in llm._PROVIDER_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
        monkeypatch.delenv("SECURITY_REVIEW_MODEL", raising=False)
        assert "ANTHROPIC_CUSTOM_HEADERS" not in hook._review_failure_reason(401)[2]
        assert hook._review_failure_reason(404)[2] == ""
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://gateway")
        monkeypatch.setenv("SECURITY_REVIEW_MODEL", "claude-x")
        assert "ANTHROPIC_CUSTOM_HEADERS" in hook._review_failure_reason(401)[2]
        assert "SECURITY_REVIEW_MODEL (claude-x)" in hook._review_failure_reason(404)[2]


class TestAgenticReviewerOn:
    def test_failed_review_is_not_clean(self, agentic_env, gateway, workspace):
        _, repo = workspace
        gateway.status = 401
        sha, rc, so, se = _commit(repo, agentic_env)
        m = metrics_of(so)
        assert m["review_failed"] is True and m["agentic_fallback"] == 2, m
        assert sha not in _reviewed(repo)
        assert rc == 2 and "HTTP 401" in se
