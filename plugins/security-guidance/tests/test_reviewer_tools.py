"""The inner Claude Code the plugin starts for a review gets only the tools
the review needs."""
import sys
import types

import pytest

import llm

READ_ONLY = {"tools": "Read,Grep,Glob", "strict-mcp-config": None}
NO_TOOLS = {"tools": "", "strict-mcp-config": None}
NOT_SAVED = {"no-session-persistence": None}


def test_tool_flags():
    assert llm._only_tools_args(("Read", "Grep", "Glob")) == READ_ONLY
    assert llm._only_tools_args() == NO_TOOLS


def test_flags_reach_the_command_line_of_the_installed_sdk():
    sdk = pytest.importorskip("claude_agent_sdk")
    transport = pytest.importorskip(
        "claude_agent_sdk._internal.transport.subprocess_cli")
    opts = sdk.ClaudeAgentOptions(
        cli_path="claude", allowed_tools=["Read", "Grep", "Glob"],
        extra_args=llm._only_tools_args(llm._REVIEWER_TOOLS))
    cmd = transport.SubprocessCLITransport(prompt="x", options=opts)._build_command()
    assert cmd[cmd.index("--tools") + 1] == "Read,Grep,Glob"
    assert cmd.count("--tools") == 1 and "--strict-mcp-config" in cmd


@pytest.fixture
def sdk(monkeypatch, tmp_path):
    """Stand-in for claude_agent_sdk that records each spawn's options. The
    first agentic stage reports one finding, later stages keep it."""
    spawned = []

    class ClaudeAgentOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ResultMessage:
        subtype, usage, total_cost_usd = "success", {}, 0.0

        def __init__(self, structured_output):
            self.structured_output = structured_output

    async def query(prompt, options):
        spawned.append(options.kwargs)
        if len(spawned) == 1:
            yield ResultMessage({"hasVulnerabilities": False, "vulnerabilities": [],
                                 "findings": [{
                "filePath": "a.py", "category": "c", "vulnerableCode": "x = 1",
                "explanation": "e", "fix": "f", "severity": "high"}]})
        else:
            yield ResultMessage({"findings": [], "survived": [0]})

    mod = types.ModuleType("claude_agent_sdk")
    mod.ClaudeAgentOptions, mod.ResultMessage, mod.query = ClaudeAgentOptions, ResultMessage, query
    mod.AssistantMessage = type("AssistantMessage", (), {})
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", mod)
    monkeypatch.setenv("SG_AGENTIC_CLI_PATH", "")
    monkeypatch.delenv("SECURITY_GUIDANCE_PERSIST_SESSIONS", raising=False)
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    for var in ("CONTEXT_DIR", "DEBUG_DIR", "MODEL", "ITER2", "FILTER", "NO_ADJUDICATE",
                "DIFF_INTERSECT", "EXCLUDE_MEDIUM", "MAX_TURNS"):
        monkeypatch.delenv("SG_AGENTIC_" + var, raising=False)
    return spawned


def test_every_agentic_stage_gets_only_the_read_tools(sdk, tmp_path):
    _, vulns, _ = llm.agentic_review(str(tmp_path), [("a.py", "+x = 1\n")], ["a.py"])
    assert len(vulns) == 1
    # investigate, second investigate pass, refute
    assert len(sdk) == 3
    for opts in sdk:
        assert opts["extra_args"] == {**READ_ONLY, **NOT_SAVED}
        assert opts["allowed_tools"] == ["Read", "Grep", "Glob"]
        assert "permission_mode" not in opts


def test_single_turn_sdk_review_gets_no_tools(sdk):
    schema = {"type": "object", "properties": {}}
    assert llm._call_claude_via_sdk("review this", schema) is not None
    assert len(sdk) == 1
    assert sdk[0]["extra_args"] == {**NO_TOOLS, **NOT_SAVED}
    assert sdk[0]["allowed_tools"] == []
