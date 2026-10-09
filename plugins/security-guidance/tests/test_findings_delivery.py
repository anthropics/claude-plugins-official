"""Findings reach Claude on the channel Claude Code reads for an asyncRewake
hook (`stderr || stdout`, never additionalContext)."""
import json
import sys
import types

from conftest import (
    STUB_VULN, VULN_PY, bash_payload, commit_file, metrics_of, run_hook,
)

import llm
import security_reminder_hook as hook


def _rewake_body(stdout, stderr):
    """What Claude Code shows Claude for an exit-2 asyncRewake hook: stderr,
    else stdout."""
    return stderr or stdout


def _commit(repo, env, content=VULN_PY, session_id="s1"):
    sha, out = commit_file(repo, "app.py", content)
    rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out,
                                       session_id=session_id), env)
    return sha, rc, so, se


class TestAgenticReviewerOn:
    def test_findings_not_replaced_by_the_inner_cli_warning(self, agentic_env, gateway, workspace):
        _, repo = workspace
        gateway.vulns = [STUB_VULN]
        sha, rc, so, se = _commit(repo, agentic_env)
        assert rc == 2, (so, se)
        assert metrics_of(so)["agentic_fallback"] == 2
        body = _rewake_body(so, se)
        assert "command_injection" in body
        assert "connectors are disabled" not in body
        assert "Fatal error in message reader" not in body  # the SDK's own log line


class TestFindingsReachClaude:
    def test_commit_findings_are_the_rewake_body(self, env, gateway, workspace):
        _, repo = workspace
        gateway.vulns = [STUB_VULN]
        sha, rc, so, se = _commit(repo, env)
        assert rc == 2
        body = _rewake_body(so, se)
        assert "Security Review: Potential vulnerabilities detected" in body
        assert "command_injection" in body
        out = json.loads(so.strip().splitlines()[-1])
        assert out["metrics"]["vulns_found"] == 1
        assert out["rewakeSummary"].startswith("Commit security review found")
        assert "hookSpecificOutput" not in out  # not repeated where the sync path would show it twice

    def test_stop_findings_also_go_in_decision_and_reason(self, capsys):
        hook.emit_metrics({"vulns_found": 1}, additional_context="FINDINGS", hook_event_name="Stop")
        cap = capsys.readouterr()
        assert cap.err == "FINDINGS"
        out = json.loads(cap.out)
        assert out["decision"] == "block" and out["reason"] == "FINDINGS"

    def test_agentic_review_captures_the_inner_cli_stderr(self, monkeypatch, tmp_path, capfd):
        spawned = []

        class ClaudeAgentOptions:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                spawned.append(kwargs)

        class ResultMessage:
            subtype, usage, total_cost_usd = "success", {}, 0.0
            structured_output = {"findings": []}

        async def query(prompt, options):
            # What the inner CLI prints on stderr; with a callback set the SDK
            # pipes it to the callback instead of the hook's own stderr.
            options.kwargs["stderr"]("claude.ai connectors are disabled")
            yield ResultMessage()

        sdk = types.ModuleType("claude_agent_sdk")
        sdk.ClaudeAgentOptions, sdk.ResultMessage, sdk.query = ClaudeAgentOptions, ResultMessage, query
        sdk.AssistantMessage = type("AssistantMessage", (), {})
        monkeypatch.setitem(sys.modules, "claude_agent_sdk", sdk)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", "")
        llm.agentic_review(str(tmp_path), [("a.py", "+x = 1\n")], ["a.py"])
        assert callable(spawned[0].get("stderr"))
        assert "connectors" not in capfd.readouterr().err
