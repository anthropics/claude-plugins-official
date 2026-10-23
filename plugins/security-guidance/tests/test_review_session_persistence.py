"""Review runs through the Agent SDK are not saved as Claude Code session
transcripts unless SECURITY_GUIDANCE_PERSIST_SESSIONS is set."""
import subprocess
import sys

import pytest

from conftest import (
    HOOKS_DIR, STUB_VULN, VULN_PY, bash_payload, commit_file, run_hook,
    write_cli,
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
        f"if {FLAG!r} in sys.argv:\n"
        f"    sys.stderr.write(\"error: unknown option '{FLAG}'\\n\")\n"
        "    sys.exit(1)\n"
    ) if reject_flag else ""
    cli = write_cli(tmp_path, "claude", (
        "import sys\n"
        # utf-8: the reviewer's prompt has characters cp1252 cannot write.
        f"with open({str(log)!r}, 'a', encoding='utf-8') as f:\n"
        "    f.write(' '.join(sys.argv[1:]) + '\\n')\n"
        f"{reject}"
        "sys.exit(1)\n"))
    return str(cli), log


def _reviews(log):
    """Argument lines of the review launches (the SDK also probes `-v`)."""
    return [l for l in log.read_text(encoding="utf-8").splitlines()
            if "--input-format" in l]


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
        monkeypatch.setattr(llm, "_send_session_flag", True)
        if value is None:
            monkeypatch.delenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", raising=False)
        else:
            monkeypatch.setenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", value)
        assert llm._reviewer_session_args() == {"no-session-persistence": None}

    @pytest.mark.parametrize("value", ["1", " on ", "TRUE", "yes"])
    def test_opt_in_keeps_sessions(self, monkeypatch, value):
        monkeypatch.setattr(llm, "_send_session_flag", True)
        monkeypatch.setenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", value)
        assert llm._reviewer_session_args() == {}

    def test_only_a_rejection_of_this_flag_counts(self):
        assert llm._refused_flags(["error: unknown option '--other'"]) == []
        assert llm._refused_flags([f"error: unknown option '{FLAG}'"]) == [FLAG]

    def test_left_out_once_refused(self, monkeypatch):
        monkeypatch.setattr(llm, "_send_session_flag", False)
        monkeypatch.delenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", raising=False)
        assert llm._reviewer_session_args() == {}


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
