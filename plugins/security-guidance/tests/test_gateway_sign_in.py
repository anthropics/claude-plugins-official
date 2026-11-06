"""Reviews in a session signed in to a Claude apps gateway with /login, where
Claude Code gives hooks no credential."""
import asyncio
import json
import os
import sys
import types

import pytest

from conftest import (
    VULN_PY, bash_payload, commit_file, edit_payload, git, metrics_of, run_hook,
    stop_payload, ups_payload, write_cli,
)

import _base
import llm

SIGNED_IN = json.dumps({"loggedIn": True, "authMethod": "third_party", "apiProvider": "gateway"})
NOT_SIGNED_IN = json.dumps({"loggedIn": False, "authMethod": "none", "apiProvider": "gateway"})


def make_cli(tmp_path, auth_status, *, name="claude", hang=False, linger=False):
    """A fake `claude` that logs each call to <name>.calls as its arguments, the
    SECURITY_GUIDANCE_DISABLE it got and its working directory, prints
    `auth_status` for `auth status --json`, and fails anything else. `hang`
    waits 5 s before answering; `linger` leaves a process running that holds
    stdout open after the CLI exits."""
    calls = tmp_path / f"{name}.calls"
    script = f"""import os, subprocess, sys, time
with open({str(calls)!r}, "a", encoding="utf-8") as f:
    f.write(" ".join(sys.argv[1:]) + " | SGD=" + os.environ.get("SECURITY_GUIDANCE_DISABLE", "")
            + " | CWD=" + os.getcwd() + "\\n")
if sys.argv[1:3] != ["auth", "status"]:
    sys.stderr.write("review refused\\n")
    sys.exit(1)
if {hang!r}:
    time.sleep(5)
sys.stdout.write({auth_status!r})
sys.stdout.flush()
if {linger!r}:
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])
"""
    return write_cli(tmp_path, name, script), calls


def calls_of(calls):
    return calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []


def review_calls(calls):
    return [c for c in calls_of(calls) if "--input-format stream-json" in c]


def model_of(call):
    args = call.split(" | ")[0].split()
    return args[args.index("--model") + 1]


@pytest.fixture
def no_credential(monkeypatch, tmp_path):
    # CLAUDE_CODE_REMOTE_SESSION_ID makes every session share one state file.
    for var in ("SECURITY_REVIEW_MODEL", "CLAUDE_CODE_EXECPATH", "CLAUDE_CODE_REMOTE_SESSION_ID",
                *llm._PROVIDER_ENV_VARS):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(tmp_path / "no-claude"))
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(_base, "DEBUG_LOG_FILE", str(tmp_path / "log.txt"))
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", False)
    new_hook_process(monkeypatch)


def new_hook_process(monkeypatch):
    monkeypatch.setattr(llm, "_gateway_cli", None)
    monkeypatch.setattr(llm, "_gateway_check_unanswered", False)
    monkeypatch.setattr(llm, "_gateway_review_timed_out", False)


class TestGatewaySignInCheck:
    @pytest.mark.parametrize("auth_status, signed_in", [
        pytest.param(SIGNED_IN, True, id="signed-in"),
        pytest.param(NOT_SIGNED_IN, False, id="gateway-named-but-not-signed-in"),
        pytest.param(json.dumps({"loggedIn": True, "apiProvider": "firstParty"}), False,
                     id="first-party"),
        pytest.param(json.dumps({"loggedIn": "true", "apiProvider": "gateway"}), False,
                     id="logged-in-not-a-boolean"),
        pytest.param("Logged in via gateway", False, id="not-json"),
        pytest.param("[]", False, id="not-an-object"),
        pytest.param("[" * 60000, False, id="too-deeply-nested"),
    ])
    def test_reviews_only_for_a_signed_in_gateway_session(
            self, no_credential, monkeypatch, tmp_path, auth_status, signed_in):
        cli, calls = make_cli(tmp_path, auth_status)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        assert llm.can_review("s1") is signed_in
        assert [c.split(" | ")[0] for c in calls_of(calls)] == ["auth status --json"]

    def test_cli_that_cannot_start_means_no_review(self, no_credential):
        assert llm.can_review("s1") is False

    def test_no_cli_found_means_no_review(self, no_credential, monkeypatch):
        monkeypatch.setattr(llm, "_user_cli_path", lambda: None)
        assert llm.can_review("s1") is False

    def test_relative_cli_path_is_not_run(self, no_credential, monkeypatch, tmp_path):
        cli, calls = make_cli(tmp_path, SIGNED_IN)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", f"./{cli.name}")
        assert llm.can_review("s1") is False
        assert calls_of(calls) == []

    def test_asked_from_the_home_directory(self, no_credential, monkeypatch, tmp_path):
        cli, calls = make_cli(tmp_path, SIGNED_IN)
        home, repo = tmp_path / "home", tmp_path / "repo"
        home.mkdir()
        repo.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))  # "~" on Windows
        monkeypatch.chdir(repo)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        assert llm.can_review("s1")
        assert calls_of(calls)[0].endswith(f"CWD={home}")

    def test_hung_cli_means_no_review(self, no_credential, monkeypatch, tmp_path):
        cli, _ = make_cli(tmp_path, SIGNED_IN, hang=True)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        monkeypatch.setattr(llm, "_GATEWAY_CHECK_TIMEOUT_S", 1)
        assert llm.can_review("s1") is False

    def test_answer_is_read_while_a_process_it_started_holds_stdout(
            self, no_credential, monkeypatch, tmp_path):
        cli, _ = make_cli(tmp_path, SIGNED_IN, linger=True)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        monkeypatch.setattr(llm, "_GATEWAY_CHECK_TIMEOUT_S", 3)
        assert llm.can_review("s1") is True

    def test_asked_once_per_session(self, no_credential, monkeypatch, tmp_path):
        cli, calls = make_cli(tmp_path, SIGNED_IN)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        assert llm.can_review("s1")
        new_hook_process(monkeypatch)
        assert llm.can_review("s1")
        assert len(calls_of(calls)) == 1
        new_hook_process(monkeypatch)
        assert llm.can_review("s2")
        assert len(calls_of(calls)) == 2

    def test_no_answer_is_asked_again(self, no_credential, monkeypatch, tmp_path):
        cli, calls = make_cli(tmp_path, "")
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        assert llm.can_review("s1") is False
        make_cli(tmp_path, SIGNED_IN)
        new_hook_process(monkeypatch)
        assert llm.can_review("s1") is True
        assert len(calls_of(calls)) == 2

    def test_a_different_cli_is_asked_again(self, no_credential, monkeypatch, tmp_path):
        first, _ = make_cli(tmp_path, SIGNED_IN, name="first")
        second, second_calls = make_cli(tmp_path, NOT_SIGNED_IN, name="second")
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(first))
        assert llm.can_review("s1")
        new_hook_process(monkeypatch)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(second))
        assert llm.can_review("s1") is False
        assert len(calls_of(second_calls)) == 1

    def test_credential_in_env_never_asks_the_cli(self, no_credential, monkeypatch, tmp_path):
        cli, calls = make_cli(tmp_path, SIGNED_IN)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
        assert llm.can_review("s1")
        assert calls_of(calls) == []

    def test_telemetry_names_the_route(self, no_credential, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_CUSTOM_HEADERS", raising=False)
        cli, _ = make_cli(tmp_path, SIGNED_IN)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        assert llm.gateway_cfg() == 0
        assert llm.can_review("s1")
        assert llm.gateway_cfg() == 4

    def test_essential_traffic_only_still_reviews(self, no_credential, monkeypatch, tmp_path):
        cli, _ = make_cli(tmp_path, SIGNED_IN)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        monkeypatch.setenv("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1")
        assert llm.can_review("s1")


class FakeChild:
    """Stands in for the child CLI's review; `reply` is what each call returns."""

    def __init__(self):
        self.prompts = []
        self.reply = {"hasVulnerabilities": False, "vulnerabilities": []}

    def __call__(self, prompt, schema, *, max_tokens=16000, model=None, cli_path=None):
        self.prompts.append(prompt)
        if self.reply is None:
            llm._last_call_claude_http_error = -1
        return self.reply


class TestGatewayReviewOutcome:
    @pytest.fixture
    def child(self, no_credential, monkeypatch, tmp_path):
        cli, _ = make_cli(tmp_path, SIGNED_IN)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        fake = FakeChild()
        monkeypatch.setattr(llm, "_call_claude_via_sdk", fake)
        return fake

    def test_review_is_sent_to_the_child(self, child):
        assert llm.can_review("s1")
        assert llm.analyze_code_security([("a.py", "+x = 1\n")], is_diff=True) == (None, [])
        assert not llm.last_review_failed()
        assert "+x = 1" in child.prompts[0]
        assert child.prompts[0].startswith(llm._CODE_REVIEW_RUBRIC)

    @pytest.mark.parametrize("reply", [
        pytest.param(None, id="child-failed"),
        pytest.param({"findings": []}, id="no-verdict"),
    ])
    def test_child_without_a_verdict_is_a_failed_review(self, child, reply):
        child.reply = reply
        assert llm.can_review("s1")
        assert llm.analyze_code_security([("a.py", "+x = 1\n")], is_diff=True) == (None, [])
        assert llm.last_review_failed()

    def test_failed_review_is_tried_on_sonnet_unless_it_timed_out(self, child, monkeypatch):
        child.reply = None
        assert llm.can_review("s1")
        llm.analyze_code_security([("a.py", "+x = 1\n")], is_diff=True)
        assert len(child.prompts) == 2
        monkeypatch.setattr(llm, "_gateway_review_timed_out", True)
        llm.analyze_code_security([("a.py", "+x = 1\n")], is_diff=True)
        assert len(child.prompts) == 3 and llm.last_review_failed()

    def test_not_signed_in_sends_nothing(self, child, monkeypatch, tmp_path):
        cli, _ = make_cli(tmp_path, NOT_SIGNED_IN, name="signed-out")
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", str(cli))
        assert not llm.can_review("s1")
        assert llm.analyze_code_security([("a.py", "+x = 1\n")], is_diff=True) == (None, [])
        assert not llm.last_review_failed()
        assert child.prompts == []


def test_timed_out_review_logs_what_the_cli_retried(no_credential, monkeypatch, tmp_path):
    """The CLI retries a refused sign-in by itself until the plugin's time
    limit; the retries are in its output, not on stderr."""
    class Retry:
        subtype, data = "api_retry", {"error_status": 401}

    async def query(prompt, options):
        yield Retry()
        raise asyncio.TimeoutError()

    mod = types.ModuleType("claude_agent_sdk")
    mod.query = query
    mod.ClaudeAgentOptions = lambda **kwargs: kwargs
    mod.AssistantMessage = type("AssistantMessage", (), {})
    mod.ResultMessage = type("ResultMessage", (), {})
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", mod)
    cli, _ = make_cli(tmp_path, SIGNED_IN)
    schema = {"type": "object", "properties": {}}
    assert llm._call_claude_via_sdk("review this", schema, cli_path=str(cli)) is None
    assert llm._gateway_review_timed_out is True
    assert ("gateway sdk-single-turn: timeout after 120s; the CLI's API requests were "
            "retried after status 401") in (tmp_path / "log.txt").read_text()
    # Not for the cloud-provider route, where the model can be the reason.
    monkeypatch.setattr(llm, "_gateway_review_timed_out", False)
    assert llm._call_claude_via_sdk("review this", schema) is None
    assert llm._gateway_review_timed_out is False


def without_credential(hook_env):
    return {k: v for k, v in hook_env.items()
            if k not in ("ANTHROPIC_API_KEY", "SECURITY_REVIEW_MODEL",
                         "CLAUDE_CODE_REMOTE_SESSION_ID", *llm._PROVIDER_ENV_VARS)}


class TestHooksInASignedInSession:
    """The hooks with the real Agent SDK and a fake CLI that signs in but
    refuses every review."""

    @pytest.fixture
    def session(self, hook_env, tmp_path):
        pytest.importorskip("claude_agent_sdk")
        env = without_credential(hook_env)
        cli, calls = make_cli(tmp_path, SIGNED_IN)
        env["SG_AGENTIC_CLI_PATH"] = str(cli)
        return env, calls

    def test_commit_review_goes_through_the_cli_and_fails_loudly(self, session, workspace):
        env, calls = session
        _, repo = workspace
        sha, out = commit_file(repo, "app.py", VULN_PY)
        rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out), env)
        assert rc == 2
        assert metrics_of(so)["review_failed"] is True
        assert ("did not complete: the review through Claude Code on the Claude apps "
                "gateway returned no result.") in se
        reviewed = repo / ".git" / "sg-reviewed-shas"
        assert not reviewed.exists() or sha not in reviewed.read_text()
        made = calls_of(calls)
        assert made[0].startswith("auth status --json")
        reviews = review_calls(calls)
        assert [model_of(r) for r in reviews] == ["opus", "sonnet"]
        # Every claude process the plugin starts (the sign-in check and the
        # reviews) has this plugin switched off. The Agent SDK's own
        # `claude -v` version check starts no session, so it is not checked.
        assert " | SGD=1 | " in made[0]
        assert all(" | SGD=1 | " in r for r in reviews)
        # The single-shot review gets no tools, as on Bedrock and Vertex.
        assert all(" --tools  --strict-mcp-config" in r for r in reviews)
        assert metrics_of(so)["gateway_cfg"] & 4

    def test_pinned_model_is_sent_as_given(self, session, workspace):
        env, calls = session
        env["SECURITY_REVIEW_MODEL"] = "claude-sonnet-5-5"
        _, repo = workspace
        _, out = commit_file(repo, "app.py", VULN_PY)
        rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out), env)
        assert rc == 2
        assert [model_of(r) for r in review_calls(calls)] == ["claude-sonnet-5-5"]
        assert "SECURITY_REVIEW_MODEL (claude-sonnet-5-5) may also name a model" in se

    def test_agentic_commit_review_runs(self, session, workspace):
        env, calls = session
        env["SG_AGENTIC_COMMIT_REVIEW"] = "1"
        env["SG_AGENTIC_MAX_TURNS"] = "7"
        _, repo = workspace
        _, out = commit_file(repo, "app.py", VULN_PY)
        rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out), env)
        assert rc == 2 and metrics_of(so)["review_failed"] is True
        reviews = review_calls(calls)
        assert any("--max-turns 7" in r for r in reviews)
        # The agentic reviewer gets the file-reading tools and nothing else.
        assert any(" --tools Read,Grep,Glob --strict-mcp-config" in r for r in reviews)

    def test_stop_review_goes_through_the_cli(self, session, workspace):
        env, calls = session
        ws, repo = workspace
        assert run_hook(ups_payload(repo), env)[0] == 0
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py", VULN_PY), env)
        rc, so, se = run_hook(stop_payload(repo), env)
        assert metrics_of(so)["review_failed"] is True
        assert review_calls(calls)

    def test_push_review_goes_through_the_cli(self, session, workspace, tmp_path):
        env, calls = session
        ws, repo = workspace
        remote = tmp_path / "remote.git"
        git(ws, "init", "-q", "--bare", str(remote))
        git(repo, "remote", "add", "origin", str(remote))
        git(repo, "push", "-q", "-u", "origin", "main")
        base = git(repo, "rev-parse", "HEAD").strip()
        sha, _ = commit_file(repo, "app.py", VULN_PY)
        git(repo, "push", "-q", "origin", "main")
        push_stdout = f"To {remote}\n   {base[:7]}..{sha[:7]}  main -> main\n"
        rc, so, se = run_hook(bash_payload(repo, "git push origin main", push_stdout), env)
        m = metrics_of(so)
        assert rc == 2 and m["push_sweep"] is True and m["review_failed"] is True, m
        assert review_calls(calls)

    def test_not_signed_in_skips_and_asks_once(self, hook_env, tmp_path, workspace):
        env = without_credential(hook_env)
        cli, calls = make_cli(tmp_path, NOT_SIGNED_IN)
        env["SG_AGENTIC_CLI_PATH"] = str(cli)
        _, repo = workspace
        for n in range(2):
            _, out = commit_file(repo, "app.py", VULN_PY + f"# {n}\n")
            rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out), env)
            assert rc == 0 and metrics_of(so)["skip_reason"] == 22
        assert len(calls_of(calls)) == 1

    def test_unanswered_sign_in_check_keeps_the_turn_for_the_next_stop(
            self, hook_env, tmp_path, workspace):
        pytest.importorskip("claude_agent_sdk")
        env = without_credential(hook_env)
        cli, calls = make_cli(tmp_path, "")
        env["SG_AGENTIC_CLI_PATH"] = str(cli)
        _, repo = workspace
        assert run_hook(ups_payload(repo), env)[0] == 0
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py", VULN_PY), env)
        rc, so, _ = run_hook(stop_payload(repo), env)
        assert metrics_of(so)["skip_reason"] == 3 and not review_calls(calls)
        # The CLI answers in the next turn: the first turn's edit is reviewed.
        make_cli(tmp_path, SIGNED_IN)
        assert run_hook(ups_payload(repo), env)[0] == 0
        rc, so, _ = run_hook(stop_payload(repo), env)
        assert metrics_of(so)["review_failed"] is True
        assert review_calls(calls)
