"""The inner Claude Code the plugin starts for a review gets only the tools
the review needs."""
import json
import sys
import threading
import types

import pytest

import llm

READ_ONLY = {"tools": "Read,Grep,Glob", "strict-mcp-config": None}
NO_TOOLS = {"tools": "", "strict-mcp-config": None}
# Once an inner CLI has refused --strict-mcp-config.
READ_ONLY_NO_MCP = {"tools": "Read,Grep,Glob", "disallowedTools": "mcp__*"}
NO_TOOLS_NO_MCP = {"tools": "", "disallowedTools": "mcp__*"}
# Every review start also asks for its session not to be saved.
NOT_SAVED = {"no-session-persistence": None}


@pytest.fixture(autouse=True)
def strict_mcp_flag_sent(monkeypatch):
    monkeypatch.setattr(llm, "_send_strict_mcp", True)
    monkeypatch.setattr(llm, "_send_session_flag", True)


def test_tool_flags():
    assert llm._only_tools_args(("Read", "Grep", "Glob")) == READ_ONLY
    assert llm._only_tools_args() == NO_TOOLS
    llm._send_strict_mcp = False
    assert llm._only_tools_args(("Read", "Grep", "Glob")) == READ_ONLY_NO_MCP
    assert llm._only_tools_args() == NO_TOOLS_NO_MCP


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
    assert "--disallowedTools" not in cmd

    llm._send_strict_mcp = False
    opts = sdk.ClaudeAgentOptions(
        cli_path="claude", allowed_tools=["Read", "Grep", "Glob"],
        extra_args=llm._only_tools_args(llm._REVIEWER_TOOLS))
    cmd = transport.SubprocessCLITransport(prompt="x", options=opts)._build_command()
    assert cmd[cmd.index("--tools") + 1] == "Read,Grep,Glob"
    assert cmd[cmd.index("--disallowedTools") + 1] == "mcp__*"
    assert cmd.count("--disallowedTools") == 1 and "--strict-mcp-config" not in cmd


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


# What Claude Code prints, before exiting 1, on a machine whose administrator
# delivers the MCP servers.
REFUSAL = "You cannot use --strict-mcp-config when an enterprise MCP config is present"


@pytest.fixture
def managed_mcp(sdk, monkeypatch):
    """The stand-in SDK's inner CLI now refuses --strict-mcp-config. Gives
    the options of the refused starts and of the ones that ran."""
    answer = sys.modules["claude_agent_sdk"].query
    refused = []

    async def query(prompt, options):
        if "strict-mcp-config" in options.kwargs["extra_args"]:
            refused.append(options.kwargs)
            options.kwargs["stderr"](REFUSAL)
            raise RuntimeError("Command failed with exit code 1")
        async for msg in answer(prompt, options):
            yield msg

    monkeypatch.setattr(sys.modules["claude_agent_sdk"], "query", query)
    return refused, sdk


def test_agentic_review_runs_where_the_strict_mcp_flag_is_refused(managed_mcp, tmp_path):
    _, vulns, metrics = llm.agentic_review(str(tmp_path), [("a.py", "+x = 1\n")], ["a.py"])
    assert len(vulns) == 1
    # The refused start's line is not what child_stderr is there to count.
    assert "agentic_fallback" not in metrics and "child_stderr" not in metrics
    refused, ran = managed_mcp
    assert [o["extra_args"] for o in refused] == [{**READ_ONLY, **NOT_SAVED}]
    # investigate, second investigate pass, refute
    assert [o["extra_args"] for o in ran] == [{**READ_ONLY_NO_MCP, **NOT_SAVED}] * 3
    for opts in ran:
        assert opts["allowed_tools"] == ["Read", "Grep", "Glob"]


def test_single_turn_sdk_review_runs_where_the_strict_mcp_flag_is_refused(managed_mcp):
    schema = {"type": "object", "properties": {}}
    assert llm._call_claude_via_sdk("review this", schema) is not None
    refused, ran = managed_mcp
    assert [o["extra_args"] for o in refused] == [{**NO_TOOLS, **NOT_SAVED}]
    assert [o["extra_args"] for o in ran] == [{**NO_TOOLS_NO_MCP, **NOT_SAVED}]
    # The refusal is remembered for the rest of the hook process.
    assert llm._call_claude_via_sdk("review this", schema) is not None
    assert len(refused) == 1 and ran[-1]["extra_args"] == {**NO_TOOLS_NO_MCP, **NOT_SAVED}


def test_other_start_failures_are_not_retried(sdk, monkeypatch, tmp_path):
    async def query(prompt, options):
        sdk.append(options.kwargs)
        options.kwargs["stderr"]("Fallback model cannot be the same as the main model")
        raise RuntimeError("Command failed with exit code 1")
        yield

    monkeypatch.setattr(sys.modules["claude_agent_sdk"], "query", query)
    guidance, vulns, metrics = llm.agentic_review(str(tmp_path), [("a.py", "+x = 1\n")], ["a.py"])
    assert guidance is None and vulns == []
    assert metrics["agentic_fallback"] == "investigate:RuntimeError"
    assert llm._call_claude_via_sdk("review this", {"type": "object", "properties": {}}) is None
    assert [o["extra_args"] for o in sdk] == [{**READ_ONLY, **NOT_SAVED}, {**NO_TOOLS, **NOT_SAVED}]


def test_reviews_started_together_are_each_started_again(managed_mcp):
    refused, ran = managed_mcp
    both_refused = threading.Barrier(2, timeout=10)
    refuse = sys.modules["claude_agent_sdk"].query

    async def query(prompt, options):
        if "strict-mcp-config" in options.kwargs["extra_args"]:
            both_refused.wait()
        async for msg in refuse(prompt, options):
            yield msg

    sys.modules["claude_agent_sdk"].query = query
    schema = {"type": "object", "properties": {}}
    results = []
    threads = [threading.Thread(
        target=lambda: results.append(llm._call_claude_via_sdk("review this", schema)))
        for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(20)
    assert len(results) == 2 and None not in results
    assert len(refused) == 2 and [o["extra_args"] for o in ran] == [{**NO_TOOLS_NO_MCP, **NOT_SAVED}] * 2


def test_review_rows_say_when_the_flag_was_left_out(managed_mcp, capsys):
    import security_reminder_hook as hook

    def row():
        hook.emit_metrics({"vulns_found": 0, "review_ms": 10})
        return json.loads(capsys.readouterr().out)["metrics"]

    assert "strict_mcp_off" not in row()
    assert llm._call_claude_via_sdk("review this", {"type": "object", "properties": {}}) is not None
    assert row()["strict_mcp_off"] == 1


# What a Claude Code older than --no-session-persistence prints, before exiting 1.
UNKNOWN = "error: unknown option '--no-session-persistence'"


@pytest.fixture
def old_cli(sdk, monkeypatch):
    """The stand-in SDK's inner CLI now refuses --no-session-persistence
    and, once that is gone, --strict-mcp-config: one flag per start, as
    Claude Code does. Gives the options of the refused starts and of the
    ones that ran."""
    answer = sys.modules["claude_agent_sdk"].query
    refused = []

    async def query(prompt, options):
        args = options.kwargs["extra_args"]
        line = (UNKNOWN if "no-session-persistence" in args
                else REFUSAL if "strict-mcp-config" in args else None)
        if line:
            refused.append(options.kwargs)
            options.kwargs["stderr"](line)
            raise RuntimeError("Command failed with exit code 1")
        async for msg in answer(prompt, options):
            yield msg

    monkeypatch.setattr(sys.modules["claude_agent_sdk"], "query", query)
    return refused, sdk


def test_agentic_review_runs_where_both_flags_are_refused(old_cli, tmp_path):
    _, vulns, metrics = llm.agentic_review(str(tmp_path), [("a.py", "+x = 1\n")], ["a.py"])
    assert len(vulns) == 1
    assert "agentic_fallback" not in metrics and "child_stderr" not in metrics
    refused, ran = old_cli
    assert [o["extra_args"] for o in refused] == [{**READ_ONLY, **NOT_SAVED}, READ_ONLY]
    assert [o["extra_args"] for o in ran] == [READ_ONLY_NO_MCP] * 3


def test_single_turn_sdk_review_runs_where_both_flags_are_refused(old_cli):
    schema = {"type": "object", "properties": {}}
    assert llm._call_claude_via_sdk("review this", schema) is not None
    refused, ran = old_cli
    assert [o["extra_args"] for o in refused] == [{**NO_TOOLS, **NOT_SAVED}, NO_TOOLS]
    assert [o["extra_args"] for o in ran] == [NO_TOOLS_NO_MCP]
    # Both refusals are remembered for the rest of the hook process.
    assert llm._call_claude_via_sdk("review this", schema) is not None
    assert len(refused) == 2 and ran[-1]["extra_args"] == NO_TOOLS_NO_MCP


def test_a_flag_refused_again_after_it_was_left_out_is_not_retried(sdk, monkeypatch):
    async def query(prompt, options):
        sdk.append(options.kwargs)
        options.kwargs["stderr"](UNKNOWN)
        raise RuntimeError("Command failed with exit code 1")
        yield

    monkeypatch.setattr(sys.modules["claude_agent_sdk"], "query", query)
    assert llm._call_claude_via_sdk("review this", {"type": "object", "properties": {}}) is None
    assert [o["extra_args"] for o in sdk] == [{**NO_TOOLS, **NOT_SAVED}, NO_TOOLS]
