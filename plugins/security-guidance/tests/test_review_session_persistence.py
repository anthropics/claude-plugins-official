"""Review runs through the Agent SDK are not saved as Claude Code session
transcripts unless SECURITY_GUIDANCE_PERSIST_SESSIONS is set."""
import subprocess
import sys

import pytest

from conftest import (
    HOOKS_DIR, STUB_VULN, VULN_PY, bash_payload, commit_file, run_hook,
)

import llm

FLAG = "--no-session-persistence"
SINGLE_TURN = (
    "import sys; sys.path.insert(0, sys.argv[1]); import llm, review_api; "
    "llm._call_claude_via_sdk('review', review_api.FINDINGS_SCHEMA)"
)


def _stub_cli(tmp_path, reject_flag=False):
    """An inner CLI that records each launch's arguments on one line and
    exits 1. With reject_flag it first refuses the flag the way a Claude Code
    older than the flag does."""
    log = tmp_path / "inner-cli-launches"
    reject = (
        f'case " $* " in *" {FLAG} "*) '
        f'echo "error: unknown option \'{FLAG}\'" >&2; exit 1;; esac\n'
    ) if reject_flag else ""
    cli = tmp_path / "claude"
    cli.write_text(f'#!/bin/sh\necho "$*" >> "{log}"\n{reject}exit 1\n')
    cli.chmod(0o755)
    return str(cli), log


def _reviews(log):
    """Argument lines of the review launches (the SDK also probes `-v`)."""
    return [l for l in log.read_text().splitlines() if "--input-format" in l]


@pytest.fixture
def sdk_env(env):
    pytest.importorskip("claude_agent_sdk")
    e = {**env, "SG_AGENTIC_COMMIT_REVIEW": "1"}
    e.pop("SECURITY_GUIDANCE_PERSIST_SESSIONS", None)
    return e


def _commit(repo, env):
    _, out = commit_file(repo, "app.py", VULN_PY)
    return run_hook(bash_payload(repo, "git commit -m change", out), env)


def _single_turn(env):
    subprocess.run([sys.executable, "-c", SINGLE_TURN, str(HOOKS_DIR)],
                   env=env, capture_output=True, text=True, timeout=120)


class TestSessionArgs:
    @pytest.mark.parametrize("value", [None, "", "0", "off"])
    def test_not_saved_by_default(self, monkeypatch, value):
        monkeypatch.setattr(llm, "_session_flag_rejected", False)
        if value is None:
            monkeypatch.delenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", raising=False)
        else:
            monkeypatch.setenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", value)
        assert llm._reviewer_session_args() == {"no-session-persistence": None}

    @pytest.mark.parametrize("value", ["1", " on ", "TRUE", "yes"])
    def test_opt_in_keeps_sessions(self, monkeypatch, value):
        monkeypatch.setattr(llm, "_session_flag_rejected", False)
        monkeypatch.setenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", value)
        assert llm._reviewer_session_args() == {}

    def test_only_a_rejection_of_this_flag_counts(self, monkeypatch):
        monkeypatch.setattr(llm, "_session_flag_rejected", False)
        llm._note_reviewer_stderr("error: unknown option '--other'")
        assert llm._session_flag_rejected is False
        llm._note_reviewer_stderr(f"error: unknown option '{FLAG}'")
        assert llm._session_flag_rejected is True


class TestInnerCliArguments:
    def test_commit_reviewer_gets_the_flag(self, sdk_env, gateway, workspace, tmp_path):
        cli, log = _stub_cli(tmp_path)
        gateway.vulns = [STUB_VULN]
        _commit(workspace[1], {**sdk_env, "SG_AGENTIC_CLI_PATH": cli})
        reviews = _reviews(log)
        assert reviews and all(FLAG in r for r in reviews)

    def test_commit_reviewer_opt_in_drops_the_flag(self, sdk_env, gateway, workspace, tmp_path):
        cli, log = _stub_cli(tmp_path)
        gateway.vulns = [STUB_VULN]
        _commit(workspace[1], {**sdk_env, "SG_AGENTIC_CLI_PATH": cli,
                               "SECURITY_GUIDANCE_PERSIST_SESSIONS": "1"})
        reviews = _reviews(log)
        assert reviews and not any(FLAG in r for r in reviews)

    def test_single_turn_review_gets_the_flag(self, sdk_env, tmp_path):
        cli, log = _stub_cli(tmp_path)
        _single_turn({**sdk_env, "SG_AGENTIC_CLI_PATH": cli})
        reviews = _reviews(log)
        assert reviews and all(FLAG in r for r in reviews)

    def test_single_turn_review_opt_in_drops_the_flag(self, sdk_env, tmp_path):
        cli, log = _stub_cli(tmp_path)
        _single_turn({**sdk_env, "SG_AGENTIC_CLI_PATH": cli,
                      "SECURITY_GUIDANCE_PERSIST_SESSIONS": "1"})
        reviews = _reviews(log)
        assert reviews and not any(FLAG in r for r in reviews)


class TestInnerCliOlderThanTheFlag:
    def test_commit_reviewer_runs_again_without_it(self, sdk_env, gateway, workspace, tmp_path):
        cli, log = _stub_cli(tmp_path, reject_flag=True)
        gateway.vulns = [STUB_VULN]
        _commit(workspace[1], {**sdk_env, "SG_AGENTIC_CLI_PATH": cli})
        reviews = _reviews(log)
        assert [FLAG in r for r in reviews] == [True, False]

    def test_single_turn_review_runs_again_without_it(self, sdk_env, tmp_path):
        cli, log = _stub_cli(tmp_path, reject_flag=True)
        _single_turn({**sdk_env, "SG_AGENTIC_CLI_PATH": cli})
        reviews = _reviews(log)
        assert [FLAG in r for r in reviews] == [True, False]
